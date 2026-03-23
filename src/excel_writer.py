"""Excel写入模块"""
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from pathlib import Path
from datetime import datetime
import yaml


def load_config():
    """加载配置"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        config_path = Path(__file__).parent.parent / "config.example.yaml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def write_with_template(df, template_path, output_path, sheet_name='Sheet1'):
    """
    使用模板写入Excel
    df: 数据DataFrame
    template_path: 模板文件路径
    output_path: 输出文件路径
    """
    # 读取模板
    wb = load_workbook(template_path)
    ws = wb[sheet_name]
    
    # 找到数据开始的行（假设模板有标题行）
    start_row = 1
    for row in range(1, ws.max_row + 1):
        if ws.cell(row=row, column=1).value is None:
            start_row = row
            break
        start_row = row + 1
    
    # 写入数据
    for r_idx, row in enumerate(df.values, start=start_row):
        for c_idx, value in enumerate(row, start=1):
            ws.cell(row=r_idx, column=c_idx, value=value)
    
    # 保存
    wb.save(output_path)


def write_simple(df, output_path, sheet_name='数据'):
    """
    直接写入Excel（无模板）
    """
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # 美化表格
    style_excel(output_path, sheet_name)


def style_excel(output_path, sheet_name='数据'):
    """美化Excel表格"""
    wb = load_workbook(output_path)
    ws = wb[sheet_name]
    
    # 标题样式
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    header_alignment = Alignment(horizontal='center', vertical='center')
    
    # 边框样式
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # 设置标题行
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # 设置数据行
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # 调整列宽
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    wb.save(output_path)


def write_output(result_data, output_filename=None):
    """
    生成输出文件
    result_data: 字典，key为脚本名（不含.sql），value为DataFrame
    """
    config = load_config()
    output_dir = Path(config['excel']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if output_filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'report_{timestamp}.xlsx'
    
    output_path = output_dir / output_filename
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name, df in result_data.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)  # Excel表名最长31字符
    
    return output_path
