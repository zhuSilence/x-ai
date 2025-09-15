# Twitter推文爬取工具

这是一个用于爬取Twitter指定用户最近推文的Python脚本，支持自动发布到WordPress站点。

## 功能特性

- 🐦 爬取指定用户最近1天（可配置）的推文
- 📊 获取详细的推文数据（点赞、转发、回复数等）
- 💾 支持保存为CSV和JSON格式
- 📈 提供推文统计摘要
- 🔒 支持Twitter API v2
- ⚡ 处理API限制和错误
- 🚀 **新增**: 智能频次控制，避免API被拦截
- 📝 **新增**: WordPress自动发布功能
- 🎨 **新增**: 精美的HTML格式化推文内容
- ⚙️ **新增**: 灵活的环境变量配置

## 安装依赖

```bash
pip install tweepy pandas requests
```

## 配置API密钥

### Twitter API配置

#### 方法1: 环境变量（推荐）
```bash
# Twitter配置
export TWITTER_BEARER_TOKEN="你的Bearer Token"
export TWITTER_RATE_DELAY="1.5"  # 可选，默认1.0秒

# WordPress配置（可选）
export PUBLISH_TO_WORDPRESS="true"
export WORDPRESS_SITE_URL="https://yoursite.com"
export WORDPRESS_USERNAME="your_username"
export WORDPRESS_PASSWORD="your_password"
export WORDPRESS_POST_STATUS="draft"  # draft/publish/private
export WORDPRESS_CATEGORY="Twitter推文"
```

#### 方法2: 直接在代码中设置
在 `main()` 函数中修改：
```python
BEARER_TOKEN = "你的Bearer Token"  # 替换这里
```

## 获取API密钥

### Twitter API密钥
1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建开发者账号
3. 创建新的应用
4. 在"Keys and tokens"页面获取Bearer Token

### WordPress API配置（可选）
1. 登录WordPress管理后台
2. 进入 `用户 > 个人资料`
3. 滚动到底部找到 `应用密码` 部分
4. 添加新的应用密码，命名为 "Twitter爬虫"
5. 复制生成的密码用于配置

## 使用方法

### 基本使用（仅爬取推文）
```bash
python twitter_scraper.py
```

### 启用WordPress发布
```bash
# 设置WordPress配置
export PUBLISH_TO_WORDPRESS="true"
export WORDPRESS_SITE_URL="https://yoursite.com"
export WORDPRESS_USERNAME="your_username"
export WORDPRESS_PASSWORD="your_app_password"

# 运行脚本
python twitter_scraper.py
```

### 用户配置
编辑 `users_config.txt` 文件来配置要爬取的用户：

```
# Twitter用户名配置文件
# 每行一个用户名，不需要@符号
# 以#开头的行为注释

elonmusk
sundarpichai
tim_cook
satyanadella
```

### 频次控制配置
```bash
# 设置请求间隔（秒）
export TWITTER_RATE_DELAY="1.5"  # 推荐值，平衡速度和稳定性
export TWITTER_RATE_DELAY="2.0"  # 保守值，适合大批量爬取
export TWITTER_RATE_DELAY="0.5"  # 激进值，有被限制风险
```

### 编程调用示例
```python
from twitter_scraper import TwitterScraper

# 创建爬虫实例（带频次控制）
scraper = TwitterScraper(
    bearer_token="你的Bearer Token",
    rate_limit_delay=1.5  # 每1.5秒一次请求
)

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

# WordPress发布（如果配置了）
if scraper.wp_publisher:
    wp_results = scraper.publish_to_wordpress(
        all_tweets,
        post_status='draft',
        category_name='Twitter推文'
    )
```

### WordPress集成示例
```python
from twitter_scraper import TwitterScraper

# WordPress配置
wordpress_config = {
    'site_url': 'https://yoursite.com',
    'username': 'your_username',
    'password': 'your_app_password'
}

# 创建带WordPress功能的爬虫
scraper = TwitterScraper(
    bearer_token="你的Bearer Token",
    rate_limit_delay=1.5,
    wordpress_config=wordpress_config
)

# 爬取并发布
usernames = ["elonmusk", "sundarpichai"]
all_tweets = scraper.get_multiple_users_tweets(usernames, days=1)

# 自动发布到WordPress（草稿状态）
wp_results = scraper.publish_to_wordpress(
    all_tweets,
    post_status='draft',
    category_name='科技大佬推文'
)
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

#### 推文数据文件
- `tweets_multiple_users_YYYYMMDD_HHMMSS.csv`: 所有用户推文合并的CSV文件
- `tweets_multiple_users_YYYYMMDD_HHMMSS.json`: 包含详细数据结构的JSON文件
- `tweets_用户名_YYYYMMDD_HHMMSS.csv`: 每个用户的单独CSV文件
- `tweets_用户名_YYYYMMDD_HHMMSS.json`: 每个用户的单独JSON文件

#### WordPress发布文件
- `wordpress_publish_results_YYYYMMDD_HHMMSS.json`: WordPress发布结果记录

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

## 高级功能

### 1. 智能频次控制
- 自动控制API请求间隔，避免被Twitter限制
- 支持自定义延迟时间
- 线程安全的请求同步机制
- 实时显示等待状态和时间

### 2. WordPress自动发布
- 支持将推文自动发布到WordPress站点
- 精美的HTML格式化内容
- 自动创建和管理分类
- 支持草稿、发布、私有三种状态
- 每个用户限制发布数量，避免内容过多

### 3. 时间范围优化
- 使用一天的开始和结束时间（00:00:00 - 23:59:59）
- 而非简单的24小时倒推
- 更准确的时间范围控制

### 4. 灵活配置
- 支持环境变量配置
- 用户配置文件支持
- 详细的错误处理和提示

### API限制
- Twitter API v2有请求频率限制
- 脚本已内置智能频次控制，默认每秒1次请求
- 可通过 `TWITTER_RATE_DELAY` 环境变量调整间隔
- 推荐设置1.5-2.0秒以获得更好的稳定性
- 免费账户每月有推文获取限制

### WordPress发布
- 需要WordPress站点支持REST API（默认支持）
- 建议使用应用密码而非账户密码
- 默认发布为草稿状态，需人工审核
- 大量发布时注意WordPress服务器性能

### 隐私保护
- 只能获取公开推文
- 受保护的账户无法爬取
- 请遵守Twitter的使用条款

## 错误排查

### 常见错误
1. **401 Unauthorized**: 检查Bearer Token是否正确
2. **403 Forbidden**: 用户可能受保护或不存在
3. **429 Too Many Requests**: API请求过于频繁，尝试增加 `TWITTER_RATE_DELAY` 值
4. **用户不存在**: 检查用户名是否正确（不包含@符号）
5. **WordPress连接失败**: 检查站点URL、用户名和密码是否正确

### 频次限制问题
如果遇到频次限制错误：
```bash
# 增加延迟时间
export TWITTER_RATE_DELAY="2.0"
# 或更保守的设置
export TWITTER_RATE_DELAY="3.0"
```

### WordPress发布问题
如果WordPress发布失败：
1. 检查REST API是否可用：`https://yoursite.com/wp-json/wp/v2/`
2. 确认用户有发布权限
3. 尝试使用应用密码
4. 检查网络连接和防火墙设置

### 调试建议
- 确保网络连接正常
- 检查API密钥权限
- 查看控制台输出的详细错误信息

## 扩展功能

### 已实现功能
- ✅ 多用户批量爬取
- ✅ 智能频次控制和API限制处理
- ✅ 自动文件命名和组织
- ✅ 详细的统计报告
- ✅ WordPress自动发布功能
- ✅ 精美的HTML内容格式化
- ✅ 灵活的环境变量配置
- ✅ 时间范围优化（按天的起止时间）

### 可以根据需要添加的功能
- 支持关键词过滤推文内容
- 支持更多时间范围选项（周、月）
- 添加推文数据可视化
- 集成数据库存储（MySQL、PostgreSQL）
- 添加情感分析功能
- 支持推文内容翻译
- 添加邮件通知功能
- 支持其他CMS平台（Drupal、Joomla）

## 相关文档

- [RATE_LIMITING_CONFIG.md](RATE_LIMITING_CONFIG.md) - 详细的频次限制配置说明
- [WORDPRESS_CONFIG.md](WORDPRESS_CONFIG.md) - WordPress发布功能完整指南
- [users_config.txt](users_config.txt) - 用户配置文件模板

## 许可证

本项目仅用于学习和研究目的，请遵守Twitter的服务条款和API使用政策。