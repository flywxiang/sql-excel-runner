#!/usr/bin/env python3
"""SQL Excel Runner - 主程序"""
import argparse
import sys
import schedule
import time
import logging
from pathlib import Path
from datetime import datetime
import yaml

from db import execute_query, load_config
from converter import dict_to_dataframe
from excel_writer import write_output, write_simple


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


def find_sql_scripts(scripts_dir):
    """查找所有SQL脚本"""
    scripts_path = Path(scripts_dir)
    if not scripts_path.exists():
        logging.warning(f"SQL脚本目录不存在: {scripts_dir}")
        return []
    
    sql_files = list(scripts_path.glob('*.sql'))
    logging.info(f"找到 {len(sql_files)} 个SQL脚本")
    return sql_files


def run_all_scripts(scripts_dir, config_dir):
    """执行所有SQL脚本并生成报表"""
    config = load_config()
    scripts_path = Path(scripts_dir)
    excel_template_dir = Path(config_dir) if config_dir else Path(config['excel']['template_dir'])
    
    sql_files = find_sql_scripts(scripts_path)
    results = {}
    
    for sql_file in sql_files:
        script_name = sql_file.stem  # 去掉.sql后缀作为表名
        logging.info(f"执行脚本: {script_name}")
        
        try:
            result = execute_query(sql_file)
            
            if result.get('columns') and result.get('data'):
                df = dict_to_dataframe(result['data'], result['columns'])
                results[script_name] = df
                logging.info(f"  ✓ {script_name}: {len(df)} 条记录")
            else:
                logging.info(f"  ✓ {script_name}: 执行成功，影响 {result.get('affected_rows', 0)} 行")
                
        except Exception as e:
            logging.error(f"  ✗ {script_name} 执行失败: {e}")
    
    if results:
        output_path = write_output(results)
        logging.info(f"报表已生成: {output_path}")
        return output_path
    
    return None


def main():
    parser = argparse.ArgumentParser(description='SQL Excel Runner')
    parser.add_argument('--scripts', '-s', default='./scripts', help='SQL脚本目录')
    parser.add_argument('--config', '-c', default='./config.yaml', help='配置文件路径')
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
    
    if args.schedule:
        # 定时模式
        day_map = {
            'mon': 'monday', 'tue': 'tuesday', 'wed': 'wednesday',
            'thu': 'thursday', 'fri': 'friday', 'sat': 'saturday', 'sun': 'sunday'
        }
        day = day_map[args.day]
        
        logging.info(f"定时任务已设置: 每周{day} {args.time} 执行")
        
        eval(f'schedule.every().{day}.at("{args.time}").do')(run_all_scripts, args.scripts, args.config)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        # 单次执行
        output = run_all_scripts(args.scripts, args.config)
        if output:
            print(f"\n✅ 完成! 报表: {output}")
        else:
            print("\n⚠️ 未生成报表")
            sys.exit(1)


if __name__ == '__main__':
    main()
