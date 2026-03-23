# SQL Excel Runner

每周自动执行SQL脚本并生成Excel报表。

## 项目结构

```
sql-excel-runner/
├── scripts/          # SQL脚本 (.sql)
├── excel/            # Excel模板 (.xlsx)
├── output/           # 输出结果
├── src/
│   ├── __init__.py
│   ├── main.py       # 主程序
│   ├── db.py         # 数据库连接
│   ├── converter.py  # 数据转换
│   └── excel_writer.py # Excel写入
├── config.yaml       # 配置文件
├── requirements.txt
└── README.md
```

## 配置

1. 复制并编辑配置：
```bash
cp config.example.yaml config.yaml
```

2. 编辑 `config.yaml` 填入数据库信息

## 使用

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python src/main.py

# 定时运行 (每周一9:00)
python src/main.py --schedule
```

## 开发

```bash
# 运行测试
pytest tests/

# 代码检查
flake8 src/
```
