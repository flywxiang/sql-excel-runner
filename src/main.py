#!/usr/bin/env python3
"""SQL Excel Runner - 主程序"""
import argparse
import sys
import shutil
from pathlib import Path
from datetime import datetime
import yaml

from db import execute_query, load_config
from converter import dict_to_dataframe
from excel_writer import write_to_excel


def setup_logging():
    """配置日志"""
    config = load_config()
    log_config = config.get('logging', {})
    
    log_file = log_config.get('file', './logs/runner.log')
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    import logging
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def find_files(directory, extension):
    """查找指定扩展名的文件"""
    dir_path = Path(directory)
    if not dir_path.exists():
        return []
    return list(dir_path.glob(f'*{extension}'))


def replace_date_in_sql(sql_content, exec_date):
    """替换SQL中的日期占位符为执行日期"""
    import re
    pattern = r"'(\d{4}-\d{2}-\d{2})'"
    result = re.sub(pattern, f"'{exec_date.strftime('%Y-%m-%d')}'", sql_content)
    return result


def run_sql_with_date(sql_file, exec_date):
    """读取SQL并替换日期后执行"""
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
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


def get_output_filename(template_name, exec_date):
    """生成带日期的输出文件名"""
    config = load_config()
    date_format = config.get('excel', {}).get('date_format', '%Y%m%d')
    date_str = exec_date.strftime(date_format)
    
    # 移除模板名中的日期部分（如20260323）生成新文件名
    import re
    name_without_date = re.sub(r'\d{8}', '', template_name)
    return f"{name_without_date}{date_str}.xlsx"


def run_all_scripts(logger, scripts_dir, excel_dir, output_dir, exec_date=None):
    """执行SQL脚本并生成带日期的Excel"""
    config = load_config()
    exec_date = exec_date or datetime.now()
    
    scripts_path = Path(scripts_dir)
    excel_path = Path(excel_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    sql_files = find_files(scripts_path, '.sql')
    excel_files = find_files(excel_path, '.xlsx')
    
    if not sql_files:
        logger.warning(f"未找到SQL脚本: {scripts_dir}")
        return
    
    logger.info(f"执行日期: {exec_date.strftime('%Y-%m-%d')}")
    logger.info(f"找到 {len(sql_files)} 个SQL, {len(excel_files)} 个Excel模板")
    
    results = []
    
    for sql_file in sql_files:
        script_name = sql_file.stem
        logger.info(f"处理: {script_name}")
        
        try:
            # 执行SQL
            result = run_sql_with_date(sql_file, exec_date)
            
            if not result.get('columns') or not result.get('data'):
                logger.warning(f"  SQL无查询结果")
                continue
            
            df = dict_to_dataframe(result['data'], result['columns'])
            logger.info(f"  查询到 {len(df)} 条记录")
            
            # 查找匹配的Excel模板
            matched_excel = None
            for excel_file in excel_files:
                if script_name in excel_file.name or excel_file.stem in script_name:
                    matched_excel = excel_file
                    break
            
            if matched_excel:
                # 复制模板到output目录，文件名加日期
                output_filename = get_output_filename(matched_excel.name, exec_date)
                output_file = output_path / output_filename
                shutil.copy2(matched_excel, output_file)
                
                # 填充数据
                write_to_excel(
                    df, 
                    output_file,
                    sheet_name='一览表',
                    start_col='E',
                    start_row=4,
                    date_cell='B1',
                    exec_date=exec_date.strftime('%Y-%m-%d %H:%M:%S')
                )
                logger.info(f"  ✓ 已生成: {output_filename}")
                results.append(output_file)
            else:
                logger.warning(f"  未找到匹配的Excel模板: {script_name}")
                
        except Exception as e:
            logger.error(f"  ✗ 处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    return results


def run_schedule():
    """定时执行模式"""
    import schedule as schedule_lib
    
    config = load_config()
    schedule_config = config.get('schedule', {})
    
    if not schedule_config.get('enabled'):
        print("定时任务未启用，请在config.yaml中设置 schedule.enabled=true")
        return
    
    day = schedule_config.get('day', 'mon')
    time_str = schedule_config.get('time', '09:00')
    
    config = load_config()
    scripts_dir = config.get('excel', {}).get('template_dir', './excel').replace('./excel', './scripts')
    if not Path(scripts_dir).exists():
        scripts_dir = './scripts'
    excel_dir = config.get('excel', {}).get('template_dir', './excel')
    output_dir = config.get('excel', {}).get('output_dir', './output')
    
    logger = setup_logging()
    logger.info(f"定时任务已设置: 每周{day} {time_str}")
    
    def job():
        logger.info("=" * 50)
        logger.info("开始执行定时任务")
        run_all_scripts(logger, scripts_dir, excel_dir, output_dir)
        logger.info("定时任务执行完成")
        logger.info("=" * 50)
    
    day_map = {
        'mon': 'monday', 'tue': 'tuesday', 'wed': 'wednesday',
        'thu': 'thursday', 'fri': 'friday', 'sat': 'saturday', 'sun': 'sunday'
    }
    
    eval(f'schedule_lib.every().{day_map[day]}.at("{time_str}").do')(job)
    
    while True:
        schedule_lib.run_pending()
        import time as time_lib
        time_lib.sleep(60)


def main():
    parser = argparse.ArgumentParser(description='SQL Excel Runner')
    parser.add_argument('--scripts', '-s', default='./scripts', help='SQL脚本目录')
    parser.add_argument('--excel', '-e', default='./excel', help='Excel模板目录')
    parser.add_argument('--output', '-o', default='./output', help='输出目录')
    parser.add_argument('--config', '-c', default='./config.yaml', help='配置文件路径')
    parser.add_argument('--date', '-d', help='执行日期 (YYYY-MM-DD)，默认今天')
    parser.add_argument('--schedule', action='store_true', help='定时运行模式')
    
    args = parser.parse_args()
    
    logger = setup_logging()
    
    if args.schedule:
        run_schedule()
    else:
        # 解析执行日期
        if args.date:
            exec_date = datetime.strptime(args.date, '%Y-%m-%d')
        else:
            exec_date = datetime.now()
        
        results = run_all_scripts(
            logger, 
            args.scripts, 
            args.excel, 
            args.output, 
            exec_date
        )
        
        if results:
            print(f"\n✅ 完成! 生成 {len(results)} 个文件:")
            for f in results:
                print(f"   {f}")
        else:
            print("\n⚠️ 未生成文件")


if __name__ == '__main__':
    main()
