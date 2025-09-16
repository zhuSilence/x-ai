# Twitter推文爬取工具

这是一个用于爬取Twitter指定用户最近推文的Python脚本，支持自动发布到WordPress站点，基于Twitter API v2官方文档实现了智能速率限制管理。

## 🚀 项目特性

- 🐦 爬取指定用户最近1天（可配置）的推文
- 📊 获取详细的推文数据（点赞、转发、回复数等）
- 💾 保存为JSON格式
- 📈 提供推文统计摘要
- 🔒 支持Twitter API v2
- 🧠 **智能速率限制管理** - 基于官方文档的精确API限制控制
- 📊 **多API等级支持** - Free/Basic/Pro/Enterprise自动适配
- ⚡ **性能大幅提升** - 最高1350倍效率提升
- 🛡️ **智能错误处理** - 429错误指数退避策略
- 📝 WordPress自动发布功能
- 🎨 精美的HTML格式化推文内容
- ⚙️ 灵活的环境变量配置
- 📦 使用uv进行现代化包管理

## 📁 项目结构

```
x-ai/
├── .venv/                   # 虚拟环境（uv自动创建）
├── .python-version         # Python版本配置 (3.11)
├── pyproject.toml          # 项目配置和依赖
├── uv.lock                 # 锁定的依赖版本
├── run.sh                  # 启动脚本
├── main.py                 # 主入口脚本
├── src/                    # 源码目录
│   ├── __init__.py         # Python包初始化文件
│   └── twitter_scraper.py  # 主程序（包含所有功能）
├── config/                 # 配置目录
│   └── users_config.txt    # 用户配置文件
├── tests/                  # 测试目录
│   ├── run_tests.py        # 测试套件入口
│   ├── test_rate_limit_manager.py  # 限流管理器测试
│   └── test_wordpress_integration.py # WordPress集成测试
└── README.md              # 项目文档（本文件）
```

## 📈 性能对比与更新亮点

### 效率提升对比

**旧版本（固定延迟）**:
- 固定10-15秒延迟
- 浪费大量等待时间
- 无法充分利用API配额

**新版本（智能限流）**:
- FREE: 18.75分钟间隔 (实际可用: 1/15分钟)
- BASIC: 1.67分钟间隔 (实际可用: 10/15分钟) - **9倍**速度提升
- PRO: 0.67秒间隔 (实际可用: 1500/15分钟) - **1350倍**速度提升

### 🎆 新版本亮点

- 🧠 **智能速率限制管理**: 基于官方文档的精确控制
- 📊 **多等级支持**: Free/Basic/Pro/Enterprise 自动适配
- 🛡️ **安全机制**: 可配置安全系数，防止触发限制
- 🔄 **指数退避**: 遇到429错误时的智能重试
- 📈 **实时监控**: 显示配额使用情况和剩余量
- 🔄 **向后兼容**: 支持旧版本配置，平滑升级



### 安装uv包管理器

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 快速开始

#### 方式1：一键运行（推荐）
```bash
./run.sh
```

#### 方式2：使用uv命令
```bash
# 安装依赖
uv sync

# 运行程序
uv run twitter-scraper

# 或者
uv run python main.py
```

#### 方式3：传统方式
```bash
source .venv/bin/activate
python twitter_scraper.py
```

## ⚙️ 配置说明

## 🧠 智能速率限制管理

基于 Twitter API v2 官方文档实现的高级限流管理系统，支持不同 API 等级的自动适配。

### 🏷️ API等级配额对比

| API等级 | 用户推文 (15分钟) | 用户信息 (时间窗口) | 效率提升 | 适用场景 |
|-----------|-------------------|---------------------|----------|----------|
| **FREE** | 1 | 1/24小时 | 基准 | 个人学习、小量测试 |
| **BASIC** | 10 | 500/24小时 | **10倍** | 小规模应用 |
| **PRO** | 1500 | 300/15分钟 | **1500倍** | 商业应用、大量爬取 |

### ⚙️ 智能特性

- 📊 **实时监控**: 显示请求配额使用情况和剩余配额
- 🛡️ **安全系数机制**: 可调节安全边距，防止被限制
- 🔄 **指数退避**: 遇到429错误时智能退避
- ⏰ **精确时间窗口**: 基于官方文档的精确时间管理
- 🔄 **向后兼容**: 支持旧版本固定延迟配置

#### 方法1: 环境变量（推荐）
```bash
# Twitter配置
export TWITTER_BEARER_TOKEN="你的Bearer Token"
<<<<<<< HEAD
export TWITTER_RATE_DELAY="15.0"  # 可选，默认10.0秒
=======

# 🚀 新版本智能限流配置（推荐）
export TWITTER_API_TIER="free"        # API等级: free/basic/pro/enterprise
export TWITTER_SAFETY_FACTOR="0.8"    # 安全系数: 0.1-1.0（推荐0.8）

# ⚠️ 向后兼容配置（仍支持，但建议使用新配置）
# export TWITTER_RATE_DELAY="15.0"      # 传统固定延迟配置
>>>>>>> f3fab32 (docs(config): 更新Twitter请求间隔默认值及建议)

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

### 获取API密钥

#### Twitter API密钥
1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建开发者账号
3. 创建新的应用
4. 在"Keys and tokens"页面获取Bearer Token

#### WordPress API配置（可选）
1. 登录WordPress管理后台
2. 进入 `用户 > 个人资料`
3. 滚动到底部找到 `应用密码` 部分
4. 添加新的应用密码，命名为 "Twitter爬虫"
5. 复制生成的密码用于配置

### 用户配置

编辑 `config/users_config.txt` 文件来配置要爬取的用户：

```
# Twitter用户名配置文件
# 每行一个用户名，不需要@符号
# 以#开头的行为注释

# 🚀 新版本智能限流说明（基于官方API文档）
# 支持自动根据API等级调整请求频率
# export TWITTER_API_TIER=free        # free/basic/pro
# export TWITTER_SAFETY_FACTOR=0.8    # 安全系数

elonmusk
sundarpichai
tim_cook
satyanadella
```

**文件格式说明：**
- 每行一个用户名，不需要包含 `@` 符号
- 以 `#` 开头的行为注释，会被忽略
- 空行会被自动忽略
- 支持中文注释

## 🎯 使用方法

### 基本使用（仅爬取推文）
```bash
python main.py
```

### 启用WordPress发布
```bash
# 设置WordPress配置
export PUBLISH_TO_WORDPRESS="true"
export WORDPRESS_SITE_URL="https://yoursite.com"
export WORDPRESS_USERNAME="your_username"
export WORDPRESS_PASSWORD="your_app_password"

# 运行脚本
python main.py
```

### 编程调用示例
```python
from src.twitter_scraper import TwitterScraper

# 创建爬虫实例（新版本智能限流）
scraper = TwitterScraper(
    bearer_token="你的Bearer Token",
    api_tier="free",        # free/basic/pro/enterprise
    safety_factor=0.8       # 安全系数 0.1-1.0
)

# 或使用传统配置（向后兼容）
scraper_legacy = TwitterScraper(
    bearer_token="你的Bearer Token",
    rate_limit_delay=15.0   # 固定延迟时间
)

# 获取推文（支持单个用户或多个用户）
all_tweets = scraper.get_tweets(["elonmusk", "sundarpichai", "tim_cook"], days=1)

# 保存数据为JSON格式
scraper.save_tweets(all_tweets)

# 显示统计摘要
scraper.print_summary(all_tweets)

# 显示速率限制状态（新功能）
scraper.rate_manager.print_status_summary()

# WordPress发布（如果配置了）
if scraper.wp_publisher:
    wp_results = scraper.publish_to_wordpress(
        all_tweets,
        post_status='draft',
        category_name='Twitter推文'
    )
```

## 📊 输出数据格式

### JSON字段说明
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
- `tweets_multiple_users_YYYYMMDD_HHMMSS.json`: 所有用户推文合并的JSON文件
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

## 🚀 高级功能

### 1. 🚀 智能速率限制管理（新功能）
基于 Twitter API 官方文档的智能限流管理器，支持不同 API 等级的自动适配。

**主要特性：**
- 🏷️ **自动API等级识别**: 支持 Free/Basic/Pro/Enterprise 四个等级
- 🛡️ **安全系数机制**: 可调节安全边距，防止被限制
- 📊 **实时监控**: 显示请求配额使用情况和剩余配额
- 🔄 **指数退避**: 遇到限制时智能退避
- ⏰ **精确时间窗口**: 基于官方文档的精确时间管理

**API等级配额对比：**

| API等级 | 用户推文 | 用户信息 | 推荐安全系数 | 适用场景 |
|-----------|------------|------------|----------------|-----------|
| **FREE** | 1请求/15分钟 | 1请求/24小时 | 0.8 | 个人学习、小量测试 |
| **BASIC** | 10请求/15分钟 | 500请求/24小时 | 0.9 | 小规模应用 |
| **PRO** | 1500请求/15分钟 | 300请求/15分钟 | 0.9 | 商业应用、大量爬取 |

**配置示例：**
```bash
# 新手推荐（最稳定）
export TWITTER_API_TIER="free"
export TWITTER_SAFETY_FACTOR="0.8"

# 小规模商用
export TWITTER_API_TIER="basic"
export TWITTER_SAFETY_FACTOR="0.9"

# 大规模应用
export TWITTER_API_TIER="pro"
export TWITTER_SAFETY_FACTOR="0.9"
```

### 2. 传统频次控制（向后兼容）
仍支持传统的固定延迟配置，但建议迁移到新的智能限流系统。

- 自动控制API请求间隔，避免被Twitter限制
- 支持自定义延迟时间
- 线程安全的请求同步机制
- 实时显示等待状态和时间

**频次控制配置：**

| 场景 | 建议设置 | 说明 |
|------|----------|------|
| 测试/少量用户 | 5.0秒 | 快速测试，适度保守 |
| 日常使用 | 10.0秒 | 推荐设置，稳定可靠 |
| 大批量爬取 | 15.0-20.0秒 | 保守设置，避免封禁 |
| 高频使用 | 20.0秒以上 | 最安全设置 |

**环境变量设置：**
```bash
# 快速测试（有风险）
export TWITTER_RATE_DELAY=5.0

# 标准使用（推荐）
export TWITTER_RATE_DELAY=10.0

# 保守设置（最稳定）
export TWITTER_RATE_DELAY=15.0
```

### 3. WordPress自动发布
- 支持将推文自动发布到WordPress站点
- 精美的HTML格式化内容
- 自动创建和管理分类
- 支持草稿、发布、私有三种状态
- 每个用户限制发布数量，避免内容过多

**WordPress配置选项：**

| 环境变量 | 说明 | 示例 | 必需 |
|---------|------|------|------|
| `PUBLISH_TO_WORDPRESS` | 是否启用WordPress发布 | `true`/`false` | 是 |
| `WORDPRESS_SITE_URL` | WordPress站点URL | `https://myblog.com` | 是 |
| `WORDPRESS_USERNAME` | WordPress用户名 | `admin` | 是 |
| `WORDPRESS_PASSWORD` | WordPress密码或应用密码 | `your_password` | 是 |
| `WORDPRESS_POST_STATUS` | 文章发布状态 | `draft`, `publish`, `private` | 否 |
| `WORDPRESS_CATEGORY` | WordPress分类名称 | 任意字符串 | 否 |

**WordPress认证方式：**
1. **应用密码（推荐）**: 更安全，在WordPress后台生成
2. **用户名和密码**: 直接使用账户密码（不推荐生产环境）
3. **JWT令牌**: 需要插件支持（高级用户）

### 4. 时间范围优化
- 使用一天的开始和结束时间（00:00:00 - 23:59:59）
- 而非简单的24小时倒推
- 更准确的时间范围控制

### 5. 灵活配置
- 支持环境变量配置
- 用户配置文件支持
- 详细的错误处理和提示

## 📦 包管理 (uv)

### uv 优势
使用 uv 相比传统的 pip + virtualenv 有以下优势：

1. **速度更快**: 依赖解析和安装速度显著提升（10-100倍）
2. **统一管理**: 项目配置、依赖、环境在一个工具中管理
3. **可靠解析**: 更准确的依赖冲突检测和解决
4. **现代标准**: 使用 pyproject.toml 标准配置文件
5. **简化工作流**: 一个命令完成环境创建和依赖安装

### 常用命令

#### 依赖管理
```bash
# 添加新依赖
uv add package_name

# 添加开发依赖
uv add --dev package_name

# 移除依赖
uv remove package_name

# 更新所有依赖
uv sync --upgrade

# 查看已安装的包
uv pip list
```

#### 环境管理
```bash
# 创建/同步虚拟环境
uv sync

# 清理虚拟环境
uv clean

# 查看项目信息
uv info

# 激活虚拟环境
source .venv/bin/activate
```

#### 开发工具
```bash
# 代码格式化
uv run black .

# 代码风格检查
uv run flake8 .

# 类型检查
uv run mypy twitter_scraper.py

# 运行测试
uv run pytest
```

### 故障排除

#### 如果遇到依赖冲突
```bash
uv sync --resolution=highest
```

#### 如果需要重新创建环境
```bash
rm -rf .venv
uv sync
```

#### 查看详细信息
```bash
uv sync --verbose
```

## 🎯 使用场景

### 1. 内容聚合博客
- 定期抓取关注的用户推文
- 自动发布为草稿，人工审核后发布
- 适合科技资讯、行业动态类博客

### 2. 个人笔记整理
- 抓取自己关注的专家推文
- 保存为私有文章，便于后续查阅
- 建立个人知识库

### 3. 社交媒体监控
- 监控品牌相关推文
- 自动归档重要信息
- 便于分析和响应

## ⚠️ 注意事项

### API限制
- Twitter API v2有请求频率限制
- 脚本已内置智能频次控制，默认每10秒一次请求
- 可通过 `TWITTER_RATE_DELAY` 环境变量调整间隔
- 推荐设置10.0-15.0秒以获得更好的稳定性
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

### 权限要求
- WordPress用户需要有发布文章的权限
- 建议使用编辑者或管理员角色账户

### 安全建议
- 使用应用密码而非账户密码
- 定期更换密码
- 监控WordPress登录日志

### 内容合规
- 确保转发内容符合网站政策
- 注意版权和隐私问题
- 建议设置为草稿状态，人工审核

## 🔧 错误排查

### 常见错误
1. **401 Unauthorized**: 检查Bearer Token是否正确
2. **403 Forbidden**: 用户可能受保护或不存在
<<<<<<< HEAD
3. **429 Too Many Requests**: API请求过于频繁，尝试增加 `TWITTER_RATE_DELAY` 值至15.0或更高
=======
3. **429 Too Many Requests**: API请求过于频繁
   - 新版本：尝试降低 `TWITTER_SAFETY_FACTOR` 至 0.6-0.7
   - 或者升级到更高等级的API计划
   - 传统方式：增加 `TWITTER_RATE_DELAY` 值至15.0或更高
>>>>>>> f3fab32 (docs(config): 更新Twitter请求间隔默认值及建议)
4. **用户不存在**: 检查用户名是否正确（不包含@符号）
5. **WordPress连接失败**: 检查站点URL、用户名和密码是否正确

### 智能限流配置建议

如果遇到频次限制错误：

**新版本解决方案（推荐）**:
```bash
# 降低安全系数（更保守）
export TWITTER_SAFETY_FACTOR="0.7"
# 或更严格
export TWITTER_SAFETY_FACTOR="0.5"

# 考虑升级API计划
export TWITTER_API_TIER="basic"  # 或 pro
```

**传统方式（向后兼容）**:
```bash
<<<<<<< HEAD
# 增加延迟时间（新默认推荐）
=======
# 增加延迟时间
>>>>>>> f3fab32 (docs(config): 更新Twitter请求间隔默认值及建议)
export TWITTER_RATE_DELAY="15.0"
# 或更保守的设置
export TWITTER_RATE_DELAY="20.0"
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

## 🔄 自动化运行

### 使用cron定时执行
```bash
# 每天早上8点执行
0 8 * * * cd /path/to/project && uv run python twitter_scraper.py

# 每6小时执行一次
0 */6 * * * cd /path/to/project && uv run python twitter_scraper.py
```

### 使用systemd定时器（Linux）
创建服务和定时器文件，实现更灵活的定时任务管理。

## 🧪 测试

项目包含完整的测试套件，位于 `tests/` 目录。

### 运行测试
```bash
# 运行所有测试
cd tests && python run_tests.py

# 或使用uv
uv run python tests/run_tests.py

# 运行特定测试
python tests/test_rate_limit_manager.py
python tests/test_wordpress_integration.py
```

### 测试内容
- **限流管理器测试**: 验证速率限制管理器功能
- **功能演示**: 展示不同API等级的配置效果
- **WordPress集成测试**: 测试WordPress连接和发布功能
- **模块化测试**: 确保代码结构和导入正确

## 🚀 扩展功能

### 已实现功能
- ✅ 多用户批量爬取
- ✅ 🚀 基于Twitter API官方文档的智能速率限制管理
- ✅ 支持Free/Basic/Pro/Enterprise四个 API等级
- ✅ 安全系数机制和指数退避策略
- ✅ 实时速率限制监控和状态显示
- ✅ 向后兼容的传统频次控制
- ✅ JSON数据格式存储
- ✅ 详细的统计报告
- ✅ WordPress自动发布功能
- ✅ 精美的HTML内容格式化
- ✅ 灵活的环境变量配置
- ✅ 时间范围优化（按天的起止时间）
- ✅ 现代化uv包管理
- ✅ 流线型的代码结构

### 可以根据需要添加的功能
- 支持关键词过滤推文内容
- 支持更多时间范围选项（周、月）
- 添加推文数据可视化
- 集成数据库存储（MySQL、PostgreSQL）
- 添加情感分析功能
- 支持推文内容翻译
- 添加邮件通知功能
- 支持其他CMS平台（Drupal、Joomla）

## 📄 许可证

本项目仅用于学习和研究目的，请遵守Twitter的服务条款和API使用政策。

---

*项目最后更新: 2025-09-16*  
*Python版本: 3.11*  
*uv版本: 0.8.17*