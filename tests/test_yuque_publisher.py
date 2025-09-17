#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语雀发布功能测试脚本
测试语雀API连接和文档创建功能
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

from src.twitter_scraper import YuquePublisher


def test_yuque_connection():
    """测试语雀API连接"""
    print("🧪 语雀API连接测试")
    print("=" * 50)
    
    # 从环境变量获取配置
    token = os.getenv('YUQUE_TOKEN')
    namespace = os.getenv('YUQUE_NAMESPACE')
    base_url = os.getenv('YUQUE_BASE_URL', 'https://yuque-api.antfin-inc.com')
    
    if not token:
        print("❌ 未设置 YUQUE_TOKEN 环境变量")
        print("💡 请设置环境变量或查看 config/yuque_config_example.txt")
        return False
    
    if not namespace:
        print("❌ 未设置 YUQUE_NAMESPACE 环境变量")
        print("💡 格式应为：owner_login/book_slug")
        return False
    
    print(f"📊 配置信息:")
    print(f"  🌐 API地址: {base_url}")
    print(f"  📚 命名空间: {namespace}")
    print(f"  🔑 Token: {token[:10]}...")
    
    try:
        # 创建语雀发布器实例
        publisher = YuquePublisher(token, namespace, base_url)
        
        # 测试连接
        print(f"\n🔗 正在测试API连接...")
        if publisher.test_connection():
            print("✅ 语雀API连接测试成功！")
            return publisher
        else:
            print("❌ 语雀API连接测试失败")
            return None
            
    except Exception as e:
        print(f"❌ 连接测试异常: {str(e)}")
        return None


def test_document_creation(publisher):
    """测试文档创建功能"""
    print(f"\n📝 测试文档创建功能")
    print("=" * 50)
    
    # 创建测试文档
    test_title = f"测试文档 - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_content = f"""# 测试文档

这是一个自动生成的测试文档，用于验证语雀API集成功能。

## 📊 测试信息

- **创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **测试类型**: API集成测试
- **文档格式**: Markdown

## 🐦 推文示例格式

> 这里是推文内容示例，支持多行文本。
> 
> 可以包含链接、话题标签等内容。

## 📈 数据统计示例

| 指标 | 数量 |
|------|------|
| 👍 点赞 | 123 |
| 🔄 转发 | 45 |
| 💬 回复 | 67 |
| 📝 引用 | 12 |

---

*此文档由Twitter推文爬虫自动生成*
"""
    
    print(f"📄 文档标题: {test_title}")
    print(f"📝 文档长度: {len(test_content)} 字符")
    
    try:
        # 创建测试文档
        result = publisher.create_document(
            title=test_title,
            body=test_content,
            format_type='markdown',
            public=0  # 私密文档
        )
        
        if result:
            print("✅ 测试文档创建成功！")
            print(f"  📄 文档ID: {result.get('id', 'N/A')}")
            print(f"  🔗 文档路径: {result.get('slug', 'N/A')}")
            print(f"  🌐 访问链接: {publisher.base_url}/{publisher.namespace}/{result.get('slug', '')}")
            return True
        else:
            print("❌ 测试文档创建失败")
            return False
            
    except Exception as e:
        print(f"❌ 文档创建异常: {str(e)}")
        return False


def test_tweet_formatting():
    """测试推文格式化功能"""
    print(f"\n🎨 测试推文格式化功能")
    print("=" * 50)
    
    # 模拟推文数据
    sample_tweet = {
        'id': '1234567890123456789',
        'text': 'This is a sample tweet for testing purposes.\n\nIt contains multiple lines and demonstrates the formatting capabilities. 🐦 #test',
        'created_at': '2024-01-15 10:30:00',
        'like_count': 42,
        'retweet_count': 15,
        'reply_count': 8,
        'quote_count': 3,
        'language': 'en',
        'url': 'https://twitter.com/testuser/status/1234567890123456789'
    }
    
    sample_username = 'testuser'
    
    try:
        # 创建临时发布器实例用于格式化测试
        publisher = YuquePublisher('test', 'test/test')
        
        # 测试Markdown格式化
        print("📝 测试Markdown格式化...")
        markdown_content = publisher.format_tweet_as_markdown(sample_tweet, sample_username)
        print(f"✅ Markdown格式化成功，长度: {len(markdown_content)} 字符")
        
        # 测试HTML格式化
        print("🌐 测试HTML格式化...")
        html_content = publisher.format_tweet_as_html(sample_tweet, sample_username)
        print(f"✅ HTML格式化成功，长度: {len(html_content)} 字符")
        
        # 显示格式化结果预览
        print(f"\n📖 Markdown格式预览（前200字符）:")
        print(markdown_content[:200] + "..." if len(markdown_content) > 200 else markdown_content)
        
        return True
        
    except Exception as e:
        print(f"❌ 格式化测试异常: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("🚀 语雀发布功能综合测试")
    print("=" * 60)
    
    # 测试推文格式化（不需要API）
    format_test = test_tweet_formatting()
    
    # 测试API连接
    publisher = test_yuque_connection()
    
    if publisher:
        # 测试文档创建
        doc_test = test_document_creation(publisher)
        
        print(f"\n🎯 测试结果汇总")
        print("=" * 50)
        print(f"📝 格式化测试: {'✅ 通过' if format_test else '❌ 失败'}")
        print(f"🔗 连接测试: ✅ 通过")
        print(f"📄 文档创建: {'✅ 通过' if doc_test else '❌ 失败'}")
        
        if format_test and doc_test:
            print(f"\n🎉 所有测试通过！语雀发布功能可以正常使用。")
        else:
            print(f"\n⚠️ 部分测试失败，请检查配置和权限。")
    else:
        print(f"\n📝 格式化测试: {'✅ 通过' if format_test else '❌ 失败'}")
        print(f"🔗 连接测试: ❌ 失败")
        print(f"📄 文档创建: ⏭️ 跳过")
        print(f"\n❌ API连接失败，请检查Token和权限配置。")
        print(f"💡 参考配置文件: config/yuque_config_example.txt")


if __name__ == "__main__":
    main()