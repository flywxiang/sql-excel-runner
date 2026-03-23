#!/usr/bin/env python3
"""SQL Excel Runner - 主程序"""
import argparse
import sys
import schedule
import time
import logging
import re
from pathlib import Path
from datetime import datetime
import yaml

from db import execute_query, load_config
from converter import dict_to_dataframe
from excel_writer import write_to_excel, write_output, write_simple


# 日志配置
def setup_logging():
    config = load_config()
    log_config = config.get('logging', {})
    
    log_file = log_config.get('file', './logs/runner.log')
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def find_files(directory, extension):
    """查找指定扩展名的文件"""
    dir_path = Path(directory)
    if not dir_path.exists():
        logging.warning(f"目录不存在: {directory}")
        return []
    
    return list(dir_path.glob(f'*{extension}'))


def replace_date_in_sql(sql_content, exec_date):
    """
    替换SQL中的日期占位符
    支持格式: 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM:SS'
    """
    # 匹配 '2026-03-23' 或 '2026-03-23 HH:MM:SS' 格式
    pattern = r"'(\d{4}-\d{2}-\d{2})(?:[ '-][\d:]+)?')"
    
    def replacer(match):
        original = match.group(0)
        # 检查是否已经是目标日期
        date_part = match.group(1)
        if date_part == exec_date.strftime('%Y-%m-%d'):
            return original
        # 替换日期部分，保持引号和后面的内容
        return f"'{exec_date.strftime('%Y-%m-%d')}'"
    
    # 更精确的替换：只替换特定的日期表达式
    result = re.sub(r"'2026-\d{2}-\d{2}'", f"'{exec_date.strftime('%Y-%m-%d')}'", sql_content)
    return result


def run_sql_with_date(sql_file, exec_date):
    """读取SQL并替换日期后执行"""
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 替换日期
    modified_sql = replace_date_in_sql(sql_content, exec_date)
    
    return execute_query_with_sql(modified_sql)


def execute_query_with_sql(sql):
    """执行SQL字符串并返回结果"""
    from db import get_connection
    from mysql.connector import Error
    
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(sql)
        
        if cursor.description:
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return {'columns': columns, 'data': results}
        else:
            connection.commit()
            return {'affected_rows': cursor.rowcount}
    except Error as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


def run_all_scripts(scripts_dir, excel_dir, config_dir, exec_date=None):
    """执行SQL脚本并填充到Excel"""
    config = load_config()
    exec_date = exec_date or datetime.now()
    
    scripts_path = Path(scripts_dir)
    excel_path = Path(excel_dir)
    
    sql_files = find_files(scripts_path, '.sql')
    excel_files = find_files(excel_path, '.xlsx')
    
    if not sql_files:
        logging.warning(f"未找到SQL脚本: {scripts_dir}")
        return
    
    logging.info(f"找到 {len(sql_files)} 个SQL脚本, {len(excel_files)} 个Excel文件")
    
    # 按文件名匹配 (去掉扩展名匹配)
    for sql_file in sql_files:
        script_name = sql_file.stem
        logging.info(f"处理: {script_name}")
        
        try:
            # 执行SQL (带日期替换)
            result = run_sql_with_date(sql_file, exec_date)
            
            if not result.get('columns') or not result.get('data'):
                logging.warning(f"  SQL无查询结果")
                continue
            
            df = dict_to_dataframe(result['data'], result['columns'])
            logging.info(f"  查询到 {len(df)} 条记录")
            
            # 查找对应的Excel文件
            matched_excel = None
            for excel_file in excel_files:
                # 匹配逻辑：SQL文件名包含在Excel文件名中，或反过来
                if script_name in excel_file.name or excel_file.stem in script_name:
                    matched_excel = excel_file
                    break
            
            if matched_excel:
                # 填充到现有Excel
                write_to_excel(
                    df, 
                    matched_excel,
                    sheet_name='一览表',
                    start_col='E',
                    start_row=4,
                    date_cell='B1',
                    exec_date=exec_date.strftime('%Y-%m-%d %H:%M:%S')
                )
                logging.info(f"  ✓ 已填充到: {matched_excel.name}")
            else:
                logging.warning(f"  未找到匹配的Excel文件")
                
        except Exception as e:
            logging.error(f"  ✗ 处理失败: {e}")
            import traceback
            traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description='SQL Excel Runner')
    parser.add_argument('--scripts', '-s', default='./scripts', help='SQL脚本目录')
    parser.add_argument('--excel', '-e', default='./scripts', help='Excel文件目录')
    parser.add_argument('--config', '-c', default='./config.yaml', help='配置文件路径')
    parser.add_argument('--date', '-d', help='执行日期 (YYYY-MM-DD)，默认今天')
    parser.add_argument('--schedule', action='store_true', help='定时运行模式')
    parser.add_argument('--time', default='09:00', help='定时执行时间 (HH:MM)')
    parser.add_argument('--day', default='mon', 
                       choices=['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
                       help='每周执行日期')
    
    args = parser.parse_args()
    
    try:
        setup_logging()
    except:
        pass
    
    # 解析执行日期
    if args.date:
        exec_date = datetime.strptime(args.date, '%Y-%m-%d')
    else:
        exec_date = datetime.now()
    
    if args.schedule:
        # 定时模式
        day_map = {
            'mon': 'monday', 'tue': 'tuesday', 'wed': 'wednesday',
            'thu': 'thursday', 'fri': 'friday', 'sat': 'saturday', 'sun': 'sunday'
        }
        day = day_map[args.day]
        
        logging.info(f"定时任务已设置: 每周{day} {args.time} 执行")
        
        def scheduled_job():
            run_all_scripts(args.scripts, args.excel, args.config)
        
        eval(f'schedule.every().{day}.at("{args.time}").do')(scheduled_job)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        # 单次执行
        logging.info(f"执行日期: {exec_date.strftime('%Y-%m-%d')}")
        run_all_scripts(args.scripts, args.excel, args.config)
        print(f"\n✅ 完成!")


if __name__ == '__main__':
    main()
