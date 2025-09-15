# WordPress发布配置指南

## 🚀 快速开始

### 1. 设置环境变量

#### Mac/Linux:
```bash
# Twitter API配置
export TWITTER_BEARER_TOKEN="your_twitter_bearer_token"
export TWITTER_RATE_DELAY="1.5"

# WordPress配置
export PUBLISH_TO_WORDPRESS="true"
export WORDPRESS_SITE_URL="https://yoursite.com"
export WORDPRESS_USERNAME="your_wp_username"
export WORDPRESS_PASSWORD="your_wp_password"
export WORDPRESS_POST_STATUS="draft"
export WORDPRESS_CATEGORY="Twitter推文"
```

#### Windows:
```cmd
set TWITTER_BEARER_TOKEN=your_twitter_bearer_token
set TWITTER_RATE_DELAY=1.5
set PUBLISH_TO_WORDPRESS=true
set WORDPRESS_SITE_URL=https://yoursite.com
set WORDPRESS_USERNAME=your_wp_username
set WORDPRESS_PASSWORD=your_wp_password
set WORDPRESS_POST_STATUS=draft
set WORDPRESS_CATEGORY=Twitter推文
```

### 2. 运行脚本
```bash
python twitter_scraper.py
```

## ⚙️ 配置选项详解

### WordPress连接配置

| 环境变量 | 说明 | 示例 | 必需 |
|---------|------|------|------|
| `PUBLISH_TO_WORDPRESS` | 是否启用WordPress发布 | `true`/`false` | 是 |
| `WORDPRESS_SITE_URL` | WordPress站点URL | `https://myblog.com` | 是 |
| `WORDPRESS_USERNAME` | WordPress用户名 | `admin` | 是 |
| `WORDPRESS_PASSWORD` | WordPress密码或应用密码 | `your_password` | 是 |

### WordPress发布设置

| 环境变量 | 说明 | 可选值 | 默认值 |
|---------|------|--------|--------|
| `WORDPRESS_POST_STATUS` | 文章发布状态 | `draft`, `publish`, `private` | `draft` |
| `WORDPRESS_CATEGORY` | WordPress分类名称 | 任意字符串 | `Twitter推文` |

## 🔐 WordPress认证方式

### 方式1: 用户名和密码（不推荐）
- 使用WordPress账户的用户名和密码
- 安全性较低，不推荐用于生产环境

### 方式2: 应用密码（推荐）
1. 登录WordPress管理后台
2. 进入 `用户 > 个人资料`
3. 滚动到底部找到 `应用密码` 部分
4. 添加新的应用密码，命名为 "Twitter爬虫"
5. 复制生成的密码，在环境变量中使用此密码

### 方式3: JWT令牌（高级）
需要安装JWT认证插件，适合高级用户。

## 📝 发布内容格式

### 文章标题格式
```
@用户名 的推文 - 2024-01-15 - 推文内容前50字...
```

### 文章内容格式
- 用户信息（用户名、发布时间）
- 推文原文（保持格式）
- 互动数据（点赞、转发、回复、引用）
- 原文链接
- 自动添加CSS样式美化

### 分类管理
- 自动创建指定的分类（如果不存在）
- 所有推文文章都会分配到指定分类

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

## 🔧 高级配置

### 批处理发布
```bash
# 设置为发布状态，直接发布文章
export WORDPRESS_POST_STATUS="publish"

# 设置为私有状态，仅自己可见
export WORDPRESS_POST_STATUS="private"
```

### 自定义分类
```bash
# 按用户分类
export WORDPRESS_CATEGORY="科技大佬"

# 按主题分类  
export WORDPRESS_CATEGORY="AI资讯"
```

### 频次控制
```bash
# 更保守的发布频率，避免WordPress限制
export TWITTER_RATE_DELAY="2.0"
```

## 🚨 注意事项

### 1. API限制
- WordPress REST API有频率限制
- 建议设置合理的延迟时间
- 大量发布时可能需要分批进行

### 2. 权限要求
- WordPress用户需要有发布文章的权限
- 建议使用编辑者或管理员角色账户

### 3. 安全建议
- 使用应用密码而非账户密码
- 定期更换密码
- 监控WordPress登录日志

### 4. 内容合规
- 确保转发内容符合网站政策
- 注意版权和隐私问题
- 建议设置为草稿状态，人工审核

## 🔍 故障排除

### 连接失败
1. 检查WordPress站点URL是否正确
2. 确认用户名和密码是否正确
3. 检查WordPress是否启用REST API
4. 确认防火墙设置

### 发布失败
1. 检查用户权限
2. 确认分类名称是否有效
3. 检查文章内容是否过长
4. 查看WordPress错误日志

### 认证问题
1. 尝试使用应用密码
2. 检查用户角色权限
3. 确认WordPress版本兼容性

## 📊 输出文件

运行成功后会生成以下文件：
- `tweets_*.csv` - 推文数据CSV格式
- `tweets_*.json` - 推文数据JSON格式
- `wordpress_publish_results_*.json` - WordPress发布结果

## 🔄 自动化运行

### 使用cron定时执行
```bash
# 每天早上8点执行
0 8 * * * cd /path/to/project && /path/to/python twitter_scraper.py

# 每6小时执行一次
0 */6 * * * cd /path/to/project && /path/to/python twitter_scraper.py
```

### 使用systemd定时器（Linux）
创建服务和定时器文件，实现更灵活的定时任务管理。