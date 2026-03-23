"""数据转换模块"""
import pandas as pd
from datetime import datetime


def dict_to_dataframe(data, columns):
    """将字典列表转换为DataFrame"""
    return pd.DataFrame(data, columns=columns)


def transform_data(df, transforms=None):
    """
    数据转换
    transforms: 转换规则字典，格式 {'列名': '操作类型'}
    操作类型: 'date' 格式化日期, 'upper' 转大写, 'lower' 转小写, 'int' 转整数, 'float' 转浮点
    """
    if transforms is None:
        return df
    
    for column, transform_type in transforms.items():
        if column not in df.columns:
            continue
            
        if transform_type == 'date':
            df[column] = pd.to_datetime(df[column]).dt.strftime('%Y-%m-%d')
        elif transform_type == 'upper':
            df[column] = df[column].astype(str).str.upper()
        elif transform_type == 'lower':
            df[column] = df[column].astype(str).str.lower()
        elif transform_type == 'int':
            df[column] = pd.to_numeric(df[column], errors='coerce').fillna(0).astype(int)
        elif transform_type == 'float':
            df[column] = pd.to_numeric(df[column], errors='coerce').round(2)
    
    return df


def aggregate_data(df, group_by, agg_config):
    """
    数据聚合
    group_by: 分组列
    agg_config: 聚合配置，格式 {'列名': ['sum', 'count', 'mean', ...]}
    """
    return df.groupby(group_by).agg(agg_config).reset_index()
