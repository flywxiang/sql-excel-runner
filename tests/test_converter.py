"""测试数据转换模块"""
import pytest
import pandas as pd
from src.converter import dict_to_dataframe, transform_data, aggregate_data


def test_dict_to_dataframe():
    """测试字典转DataFrame"""
    data = [
        {'name': 'Alice', 'age': 25},
        {'name': 'Bob', 'age': 30}
    ]
    columns = ['name', 'age']
    df = dict_to_dataframe(data, columns)
    
    assert len(df) == 2
    assert list(df.columns) == columns
    assert df['name'][0] == 'Alice'


def test_transform_data():
    """测试数据转换"""
    df = pd.DataFrame({
        'name': ['Alice', 'Bob'],
        'age': ['25', '30'],
        'score': [85.5, 92.3]
    })
    
    transforms = {
        'age': 'int',
        'name': 'upper'
    }
    
    result = transform_data(df, transforms)
    
    assert result['age'].dtype == int
    assert result['name'][0] == 'ALICE'


def test_aggregate_data():
    """测试数据聚合"""
    df = pd.DataFrame({
        'category': ['A', 'A', 'B', 'B'],
        'value': [10, 20, 30, 40]
    })
    
    result = aggregate_data(df, 'category', {'value': ['sum', 'mean']})
    
    assert len(result) == 2
    assert result[result['category'] == 'A']['value']['sum'].values[0] == 30


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
