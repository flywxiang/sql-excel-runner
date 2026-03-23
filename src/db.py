"""数据库连接模块"""
import mysql.connector
from mysql.connector import Error
import yaml
from pathlib import Path


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        config_path = Path(__file__).parent.parent / "config.example.yaml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_connection():
    """获取数据库连接"""
    config = load_config()
    db_config = config['database']
    
    try:
        connection = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            charset=db_config.get('charset', 'utf8mb4')
        )
        return connection
    except Error as e:
        print(f"数据库连接失败: {e}")
        raise


def execute_query(sql_path):
    """执行SQL文件并返回结果"""
    # 读取SQL文件
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(sql)
        
        # 判断是查询还是更新
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
