# 语雀发布功能使用指南

本指南将介绍如何配置和使用新的语雀文档发布功能，替代之前的WordPress发布功能。

## 🌟 功能特点

- 🐦 将Twitter推文自动发布为语雀文档
- 📝 支持Markdown和HTML两种格式
- 🔒 支持私密和公开文档设置
- 🔄 自动检测重复文档避免重复发布
- 🎨 精美的推文格式化展示
- ⚙️ 灵活的环境变量配置

## 🔧 配置步骤

### 1. 获取语雀API Token

1. 登录语雀账号
2. 访问 [语雀设置页面 - Token管理](https://www.yuque.com/settings/tokens)
3. 点击 "新建 Token"
4. 输入Token名称（如："Twitter推文爬虫"）
5. 选择权限范围（需要包含目标知识库的读写权限）
6. 点击创建并复制生成的Token

### 2. 确定知识库命名空间

知识库命名空间格式为：`用户名或团队名/知识库路径`

**如何获取命名空间：**
1. 访问目标知识库页面
2. 从URL中提取命名空间
   - 例如：`https://www.yuque.com/company/tech-docs` 
   - 命名空间为：`company/tech-docs`

**权限要求：**
- 个人知识库：确保是知识库所有者
- 团队知识库：确保是团队成员且有写入权限

### 3. 环境变量配置

创建或编辑 `.env` 文件，添加以下配置：

```bash
# === 语雀API配置 ===
# 启用语雀发布
PUBLISH_TO_YUQUE=true

# 语雀API Token
YUQUE_TOKEN=your_yuque_token_here

# 知识库命名空间
YUQUE_NAMESPACE=owner_login/book_slug

# API基础URL（可选，默认线上地址）
YUQUE_BASE_URL=https://yuque-api.antfin-inc.com

# === 发布设置 ===
# 文档格式：markdown 或 html
YUQUE_DOC_FORMAT=markdown

# 文档公开性：0-私密，1-公开
YUQUE_DOC_PUBLIC=0

# === Twitter API配置（必需） ===
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
TWITTER_API_TIER=free
TWITTER_SAFETY_FACTOR=0.8
```

### 4. 配置说明

| 环境变量 | 说明 | 可选值 | 默认值 | 必需 |
|---------|------|--------|--------|------|
| `PUBLISH_TO_YUQUE` | 是否启用语雀发布 | `true`/`false` | `false` | 是 |
| `YUQUE_TOKEN` | 语雀API Token | 字符串 | 无 | 是 |
| `YUQUE_NAMESPACE` | 知识库命名空间 | `owner/book` | 无 | 是 |
| `YUQUE_BASE_URL` | API基础URL | URL字符串 | 官方地址 | 否 |
| `YUQUE_DOC_FORMAT` | 文档格式 | `markdown`/`html` | `markdown` | 否 |
| `YUQUE_DOC_PUBLIC` | 文档公开性 | `0`/`1` | `0` | 否 |

## 🚀 使用方法

### 基本使用

```bash
# 设置环境变量
export PUBLISH_TO_YUQUE=true
export YUQUE_TOKEN="your_token"
export YUQUE_NAMESPACE="your/namespace"

# 运行爬虫
python main.py
```

### 测试连接

使用专门的测试脚本验证配置：

```bash
# 测试语雀API连接和权限
python tests/test_yuque_publisher.py
```

测试脚本会验证：
- ✅ API连接是否正常
- ✅ Token权限是否充足  
- ✅ 知识库访问权限
- ✅ 文档创建功能
- ✅ 推文格式化功能

### 编程调用

```python
from src.twitter_scraper import TwitterScraper

# 配置语雀发布
yuque_config = {
    'yuque_token': 'your_yuque_token',
    'yuque_namespace': 'owner_login/book_slug',
    'yuque_base_url': 'https://yuque-api.antfin-inc.com'
}

# 创建爬虫实例
scraper = TwitterScraper(
    bearer_token="your_bearer_token",
    api_tier="free",
    safety_factor=0.8,
    wordpress_config=yuque_config  # 复用参数名保持兼容性
)

# 获取推文
tweets = scraper.get_tweets(["elonmusk"], days=1)

# 发布到语雀（如果配置了语雀发布器）
if scraper.yuque_publisher:
    results = scraper.yuque_publisher.publish_tweets_as_documents(
        tweets,
        doc_format='markdown',
        public=0,
        avoid_duplicates=True
    )
```

## 📝 文档格式示例

### Markdown格式（推荐）

```markdown
# 🐦 来自 @username 的推文

## 📋 推文信息

- **发布时间**: 2024-01-15 10:30:00
- **原文链接**: [https://twitter.com/username/status/123456789]
- **推文ID**: `123456789`
- **语言**: en

## 📝 推文内容

> 这里是推文的实际内容...

## 📊 互动数据

| 指标 | 数量 |
|------|------|
| 👍 点赞 | 42 |
| 🔄 转发 | 15 |
| 💬 回复 | 8 |
| 📝 引用 | 3 |

---

*通过 Twitter推文爬虫 自动生成于 2024-01-15 10:30:00*
```

### HTML格式

HTML格式包含更丰富的样式，适合需要特殊展示效果的场景。

## 🔍 文档管理

### 文档命名规则

自动生成的文档标题格式：
```
@用户名 的推文 - YYYY-MM-DD - 推文ID后8位
```

例如：`@elonmusk 的推文 - 2024-01-15 - 90123456`

### 重复检测

系统会自动检测同名文档，避免重复发布：
- ✅ 检测到重复文档会自动跳过
- 📝 在日志中显示跳过原因
- 📊 在结果文件中记录跳过状态

### 文档路径

自动生成的文档路径格式：
```
tweet-用户名-推文ID后8位
```

例如：`tweet-elonmusk-90123456`

## 📊 输出文件

### 语雀发布结果文件

每次发布会生成详细的结果文件：

文件名：`yuque_results_用户名_YYYYMMDD_HHMMSS.json`

文件内容示例：
```json
[
  {
    "username": "elonmusk",
    "tweet_id": "1234567890123456789",
    "doc_id": 12345,
    "doc_slug": "tweet-elonmusk-90123456",
    "doc_url": "https://yuque-api.antfin-inc.com/company/tech-docs/tweet-elonmusk-90123456",
    "status": "success"
  },
  {
    "username": "elonmusk", 
    "tweet_id": "1234567890123456790",
    "status": "skipped",
    "reason": "document_exists"
  }
]
```

### 状态说明

- `success`: 成功发布
- `failed`: 发布失败
- `skipped`: 跳过发布（通常因为重复）

## ⚠️ 注意事项

### API限制

- 语雀API有请求频率限制
- 脚本已内置1.5秒间隔控制
- 大量发布时请注意不要过于频繁

### 权限要求

- Token必须有目标知识库的写入权限
- 团队知识库需要确保用户是团队成员
- 私有知识库需要确保有相应访问权限

### 内容限制

- 每个用户默认最多发布5条推文
- 文档标题长度有限制（通常不超过200字符）
- 推文内容会自动转义特殊字符

### 网络要求

- 需要能访问语雀API服务器
- 建议在网络稳定的环境下运行
- 如使用企业内网，请确保相关端口开放

## 🔧 故障排除

### 常见错误及解决方案

#### 1. Token认证失败 (401)
```
❌ 语雀Token认证失败，请检查Token是否正确
```

**解决方案：**
- 检查Token是否正确复制
- 确认Token未过期
- 重新生成Token并更新配置

#### 2. 知识库不存在或无权限 (404)
```
❌ 知识库不存在或无访问权限: company/tech-docs
```

**解决方案：**
- 检查命名空间格式是否正确
- 确认对该知识库有写入权限
- 如果是团队知识库，确认用户是团队成员

#### 3. 文档创建失败 (422)
```
❌ 语雀文档创建失败，状态码: 422
💡 提示: 请检查文档标题是否重复或参数格式是否正确
```

**解决方案：**
- 检查是否有重复的文档标题
- 确认文档内容格式正确
- 检查特殊字符是否需要转义

#### 4. 网络连接问题
```
❌ 语雀连接测试失败: Connection timeout
```

**解决方案：**
- 检查网络连接是否正常
- 确认能够访问语雀官网
- 检查防火墙设置
- 尝试更换网络环境

### 调试技巧

1. **使用测试脚本**：
   ```bash
   python tests/test_yuque_publisher.py
   ```

2. **查看详细日志**：
   程序会输出详细的操作日志，包括：
   - API连接状态
   - 文档创建过程
   - 错误详细信息

3. **验证配置**：
   ```bash
   echo $YUQUE_TOKEN | cut -c1-10  # 查看Token前10位
   echo $YUQUE_NAMESPACE           # 查看命名空间
   ```

4. **手动测试API**：
   ```bash
   curl -H "X-Auth-Token: your_token" \
        https://yuque-api.antfin-inc.com/api/v2/user
   ```

## 📈 最佳实践

### 推荐配置

**个人使用：**
```bash
YUQUE_DOC_FORMAT=markdown
YUQUE_DOC_PUBLIC=0  # 私密文档
```

**团队分享：**
```bash
YUQUE_DOC_FORMAT=markdown
YUQUE_DOC_PUBLIC=1  # 公开文档
```

**展示用途：**
```bash
YUQUE_DOC_FORMAT=html
YUQUE_DOC_PUBLIC=1  # 公开文档，更好的样式
```

### 使用建议

1. **批量处理**：一次处理多个用户时，建议使用较小的用户列表避免超时
2. **定期清理**：定期检查和清理不需要的文档
3. **备份重要内容**：对重要推文建议手动备份
4. **监控API配额**：注意API使用情况，避免超限

### 自动化运行

```bash
# 每日定时运行
0 8 * * * cd /path/to/project && source .env && python main.py

# 每6小时运行一次
0 */6 * * * cd /path/to/project && source .env && python main.py
```

## 🔄 从WordPress迁移

如果你之前使用WordPress发布功能，迁移到语雀非常简单：

### 1. 更新环境变量

**原WordPress配置：**
```bash
PUBLISH_TO_WORDPRESS=true
WORDPRESS_SITE_URL=https://yoursite.com
WORDPRESS_USERNAME=admin
WORDPRESS_PASSWORD=your_password
```

**新语雀配置：**
```bash
PUBLISH_TO_YUQUE=true
YUQUE_TOKEN=your_yuque_token
YUQUE_NAMESPACE=your/namespace
```

### 2. 功能对比

| 功能 | WordPress | 语雀 |
|------|-----------|------|
| 文档格式 | HTML | Markdown/HTML |
| 分类管理 | 自动创建分类 | 知识库管理 |
| 公开性控制 | 草稿/发布/私有 | 私密/公开 |
| 重复检测 | 无 | 自动检测 |
| 访问权限 | 用户名+密码 | API Token |

### 3. 注意事项

- 语雀的文档组织方式与WordPress文章不同
- 需要重新配置权限和访问方式
- 推文格式化样式可能略有不同

---

## 📞 支持与反馈

如果在使用过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 运行测试脚本检查配置
3. 查看程序输出的详细日志
4. 检查语雀官方API文档

**相关链接：**
- [语雀API文档](https://www.yuque.com/yuque/developer/api)
- [语雀Token管理](https://www.yuque.com/settings/tokens)
- [项目GitHub仓库](https://github.com/your-repo/twitter-scraper)

---

*更新时间：2025-09-17*