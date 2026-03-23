# SQL Excel Runner

每周自动执行SQL脚本并生成带日期的Excel报表。

## 项目结构

```
sql-excel-runner/
├── scripts/          # SQL脚本 (.sql)
├── excel/            # Excel模板 (.xlsx)
├── output/           # 输出结果 (带日期文件名)
├── src/
│   ├── main.py       # 主程序
│   ├── db.py         # 数据库连接
│   ├── converter.py  # 数据转换
│   └── excel_writer.py # Excel写入
├── config.yaml       # 配置文件
├── config.example.yaml # 配置模板
├── requirements.txt  # Python依赖
├── run.bat           # Windows运行脚本
└── README.md
```

## Windows安装运行

```batch
# 1. 安装Python 3.8+
# 2. 双击 run.bat 或命令行运行:
pip install -r requirements.txt
python src\main.py
```

## 配置

编辑 `config.yaml`:

```yaml
database:
  host: localhost
  port: 3306
  user: root
  password: your_password
  database: your_database

excel:
  template_dir: ./excel
  output_dir: ./output

schedule:
  enabled: true      # 是否启用定时
  day: mon            # 每周执行日
  time: "09:00"      # 执行时间
```

## 新增报表

只需添加两个文件（文件名包含关系即可匹配）：

```
scripts/
├── 交易汇总统计.sql    ← SQL脚本
└── 用户统计.sql        ← 新增

excel/
├── 交易情况汇总20260323.xlsx  ← 模板
└── 用户统计.xlsx              ← 新增模板
```

## 使用

```bash
# 安装依赖
pip install -r requirements.txt

# 运行(今天)
python src/main.py

# 指定日期
python src/main.py -d 2026-03-20

# 定时模式(读取config.yaml)
python src/main.py --schedule

# Windows双击
run.bat
```

## 输出

输出文件自动添加日期：`交易情况汇总20260323.xlsx` → `交易情况汇总_20260323.xlsx`
