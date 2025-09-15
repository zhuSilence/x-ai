# Twitter推文爬取工具

这是一个用于爬取Twitter指定用户最近推文的Python脚本。

## 功能特性

- 🐦 爬取指定用户最近1天（可配置）的推文
- 📊 获取详细的推文数据（点赞、转发、回复数等）
- 💾 支持保存为CSV和JSON格式
- 📈 提供推文统计摘要
- 🔒 支持Twitter API v2
- ⚡ 处理API限制和错误

## 安装依赖

```bash
pip install tweepy pandas
```

## 配置API密钥

### 方法1: 环境变量（推荐）
```bash
export TWITTER_BEARER_TOKEN="你的Bearer Token"
```

### 方法2: 直接在代码中设置
在 `main()` 函数中修改：
```python
BEARER_TOKEN = "你的Bearer Token"  # 替换这里
```

## 获取Twitter API密钥

1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建开发者账号
3. 创建新的应用
4. 在"Keys and tokens"页面获取Bearer Token

## 使用方法

### 基本使用
```bash
python twitter_scraper.py
```

### 自定义参数
在脚本中可以修改这些参数：
```python
# 多用户模式（推荐）
USERNAMES = [
    "elonmusk",
    "sundarpichai", 
    "tim_cook",
    "satyanadella"
]
DAYS = 1                    # 获取天数
USE_MULTIPLE_USERS = True   # True=多用户模式，False=单用户模式

# 单用户模式
# USERNAME = "elonmusk"  # 目标用户名
```

### 编程调用示例
```python
from twitter_scraper import TwitterScraper

# 创建爬虫实例
scraper = TwitterScraper("你的Bearer Token")

# 单用户模式
tweets = scraper.get_user_tweets("elonmusk", days=1)
scraper.save_tweets_to_csv(tweets, "tweets.csv")
scraper.print_tweets_summary(tweets)

# 多用户模式
usernames = ["elonmusk", "sundarpichai", "tim_cook"]
all_tweets = scraper.get_multiple_users_tweets(usernames, days=1)

# 保存数据（包含合并文件和单独文件）
scraper.save_multiple_users_tweets(all_tweets, format_type='both')
# 显示统计
scraper.print_multiple_users_summary(all_tweets)
```

## 输出数据格式

### CSV/JSON字段说明
- `id`: 推文唯一ID
- `text`: 推文内容
- `created_at`: 发布时间
- `retweet_count`: 转发数
- `like_count`: 点赞数
- `reply_count`: 回复数
- `quote_count`: 引用数
- `language`: 语言
- `url`: 推文链接
- `username`: 用户名（多用户模式下的合并文件中包含）

### 输出文件

#### 单用户模式
- `tweets_YYYYMMDD_HHMMSS.csv`: CSV格式的推文数据
- `tweets_YYYYMMDD_HHMMSS.json`: JSON格式的推文数据

#### 多用户模式
- `tweets_multiple_users_YYYYMMDD_HHMMSS.csv`: 所有用户推文合并的CSV文件
- `tweets_multiple_users_YYYYMMDD_HHMMSS.json`: 包含详细数据结构的JSON文件
- `tweets_用户名_YYYYMMDD_HHMMSS.csv`: 每个用户的单独CSV文件
- `tweets_用户名_YYYYMMDD_HHMMSS.json`: 每个用户的单独JSON文件

### 多用户JSON数据结构
```json
{
  "timestamp": "20240915_143022",
  "total_users": 4,
  "total_tweets": 156,
  "users_data": {
    "elonmusk": [...],
    "sundarpichai": [...]
  },
  "combined_tweets": [...]
}
```

## 注意事项

### API限制
- Twitter API v2有请求频率限制
- 免费账户每月有推文获取限制
- 脚本会自动处理频率限制错误

### 权限要求
- 需要Twitter开发者账号
- 应用需要有读取推文的权限

### 隐私保护
- 只能获取公开推文
- 受保护的账户无法爬取
- 请遵守Twitter的使用条款

## 错误排查

### 常见错误
1. **401 Unauthorized**: 检查Bearer Token是否正确
2. **403 Forbidden**: 用户可能受保护或不存在
3. **429 Too Many Requests**: API请求过于频繁，等待后重试
4. **用户不存在**: 检查用户名是否正确（不包含@符号）

### 调试建议
- 确保网络连接正常
- 检查API密钥权限
- 查看控制台输出的详细错误信息

## 扩展功能

### 已实现功能
- ✅ 多用户批量爬取
- ✅ 自动处理API限制
- ✅ 智能文件命名和组织
- ✅ 详细的统计报告

### 可以根据需要添加的功能
- 支持关键词过滤
- 支持更多时间范围选项
- 添加数据可视化
- 集成数据库存储
- 添加情感分析
- 支持推文内容翻译

## 许可证

本项目仅用于学习和研究目的，请遵守Twitter的服务条款和API使用政策。