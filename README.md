# Google Trends Monitor

一个用于监控 Google Trends 数据的自动化工具，支持定时获取关键词相关查询数据，生成报告，并通过邮件通知重要趋势变化。

## 功能特点

- 自动监控多个关键词的 Google Trends 数据
- 支持自定义时间范围和地区
- 批量处理关键词以避免请求限制
- 自动生成每日数据报告（CSV格式）
- 高增长趋势的即时邮件通知
- 完整的日志记录
- 支持测试模式和计划任务模式

## 配置说明

### 1. 环境变量配置
复制 `.env.example` 文件为 `.env` 并设置以下环境变量：
```bash
# SMTP服务器设置
TRENDS_SMTP_SERVER=smtp.gmail.com
TRENDS_SMTP_PORT=587

# 邮件账号设置
TRENDS_SENDER_EMAIL=your-email@gmail.com
TRENDS_SENDER_PASSWORD=your-app-password
TRENDS_RECIPIENT_EMAIL=recipient@example.com
```

### 2. 监控关键词 (KEYWORDS)
在 `config.py` 中配置要监控的关键词：
```python
KEYWORDS = [
    'Python',
    'AI',
    'Machine Learning',
    # 添加更多关键词
]
```

### 3. 趋势查询配置 (TRENDS_CONFIG)
```python
TRENDS_CONFIG = {
    'timeframe': 'now 1-d',  # 时间范围
    'geo': '',              # 地区代码
}
```
- timeframe 可选值：
  - 'now 1-d': 最近1天
  - 'now 7-d': 最近7天
  - 'now 30-d': 最近30天
  - 'now 90-d': 最近90天
  - 'today 12-m': 最近12个月
  - '2024-12-30 2024-12-31': 日期范围
- geo 可选值：
  - '': 全球
  - 'US': 美国
  - 'CN': 中国
  - 其他国家代码

### 4. 频率限制配置 (RATE_LIMIT_CONFIG)
```python
RATE_LIMIT_CONFIG = {
    'max_retries': 3,        # 最大重试次数
    'min_delay_between_queries': 10,  # 查询间最小延迟（秒）
    'max_delay_between_queries': 20,  # 查询间最大延迟（秒）
    'batch_size': 5,         # 每批处理的关键词数量
    'batch_interval': 300,   # 批次间隔时间（秒）
}
```

### 5. 计划任务配置 (SCHEDULE_CONFIG)
```python
SCHEDULE_CONFIG = {
    'hour': 13,  # 执行时间（24小时制）
    'random_delay_minutes': 10,  # 随机延迟范围（分钟）
}
```

### 6. 监控阈值配置 (MONITOR_CONFIG)
```python
MONITOR_CONFIG = {
    'rising_threshold': 1000,  # 高增长趋势阈值
}
```

## 安装和设置

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/trends-monitor.git
cd trends-monitor
```

2. 创建并激活虚拟环境（推荐）：
```bash
# 在 Windows 上
python -m venv venv
venv\Scripts\activate

# 在 macOS/Linux 上
python3 -m venv venv
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的邮件配置
```

5. Gmail 设置：
   - 开启两步验证：Google账号 -> 安全性 -> 2步验证
   - 生成应用专用密码：
     1. Google账号 -> 安全性 -> 应用专用密码
     2. 选择"其他"，输入名称（如"Trends Monitor"）
     3. 复制生成的16位密码到 `.env` 文件的 `TRENDS_SENDER_PASSWORD`

6. 修改其他配置：
   - 根据需要在 `config.py` 中调整其他配置项
   - 添加或修改要监控的关键词

## 使用方法

### 测试模式
立即执行一次数据收集：
```bash
# 使用配置文件中的关键词
python trends_monitor.py --test

# 使用指定的关键词
python trends_monitor.py --test --keywords "Python" "AI"
```

### 计划任务模式
启动定时监控任务：
```bash
python trends_monitor.py
```

## 输出说明

### 1. 数据存储
数据按日期存储在独立目录中：
```
data_20240101/
  ├── daily_report_20240101.csv     # 当日汇总报告
  ├── related_queries_Python_*.json  # 各关键词的详细数据
  └── ...
```

### 2. 邮件通知
- 每日报告邮件：包含所有关键词的相关查询数据
- 高增长趋势通知：当发现增长超过阈值的趋势时立即发送
- 错误通知：当发生错误时发送详细信息

### 3. 日志记录
所有操作记录在 `trends_monitor.log` 文件中，包括：
- 查询执行情况
- 错误信息
- 邮件发送状态
- 配置信息

## 注意事项

1. 请求频率限制：
   - 使用批处理和延迟机制避免触发限制
   - 可以通过 `RATE_LIMIT_CONFIG` 调整请求间隔

2. 邮件发送：
   - 强烈建议使用 Gmail
   - 必须使用应用专用密码而不是账号密码
   - 确保网络环境能够访问 Gmail

3. 数据存储：
   - 确保运行目录有足够的存储空间
   - 定期清理历史数据

## 故障排除

1. 邮件发送失败：
   - 检查 Gmail 配置是否正确
   - 确认应用专用密码是否有效
   - 检查网络连接

2. 数据获取失败：
   - 检查网络连接
   - 可能触发了 Google Trends 的频率限制
   - 尝试调整 `RATE_LIMIT_CONFIG` 中的延迟设置

3. 计划任务问题：
   - 检查系统时间是否正确
   - 确保程序有持续运行的权限 

4. SSL相关警告：
   - 如果看到 urllib3 SSL 警告，不会影响程序运行
   - 如果想要消除警告，可以：
     1. 升级系统的 OpenSSL
     2. 或者使用 `urllib3<2.0.0`（已在 requirements.txt 中指定）

## 开发说明

1. 环境变量：
   - 所有敏感信息都存储在 `.env` 文件中
   - 不要将 `.env` 文件提交到版本控制系统
   - 可以参考 `.env.example` 创建自己的 `.env` 文件

2. 版本控制：
   - `.gitignore` 已配置为排除敏感文件和临时文件
   - 数据文件夹 (`data_*`) 不会被提交
   - 日志文件 (`*.log`) 不会被提交 