#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter to WordPress 集成测试脚本
"""

from twitter_scraper import WordPressPublisher


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_wordpress_config():
    """测试WordPress配置"""
    print("🧪 WordPress配置测试")
    print("=" * 40)
    
    # 检查必需的环境变量
    required_vars = [
        'WORDPRESS_SITE_URL',
        'WORDPRESS_USERNAME', 
        'WORDPRESS_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ 缺少以下WordPress环境变量:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 请设置以下环境变量:")
        print("export WORDPRESS_SITE_URL='https://yoursite.com'")
        print("export WORDPRESS_USERNAME='your_username'")
        print("export WORDPRESS_PASSWORD='your_password'")
        return False
    
    print("✅ WordPress环境变量配置完整")
    return True

def test_wordpress_connection() -> WordPressPublisher | None:
    """测试WordPress连接"""
    print("\n🔗 WordPress连接测试")
    print("=" * 40)
    
    try:
        from twitter_scraper import WordPressPublisher
        
        wp_config = {
            'site_url': os.getenv('WORDPRESS_SITE_URL'),
            'username': os.getenv('WORDPRESS_USERNAME'),
            'password': os.getenv('WORDPRESS_PASSWORD')
        }
        
        print(f"🌐 站点: {wp_config['site_url']}")
        print(f"👤 用户: {wp_config['username']}")
        print("🔐 密码: ***隐藏***")
        
        publisher = WordPressPublisher(**wp_config)
        
        print("\n📡 正在测试连接...")
        if publisher.test_connection():
            print("✅ WordPress连接测试通过!")
            return publisher
        else:
            print("❌ WordPress连接测试失败!")
            return None
            
    except Exception as e:
        print(f"❌ 连接测试异常: {str(e)}")
        return None

def test_wordpress_categories(publisher):
    """测试WordPress分类功能"""
    print("\n📁 WordPress分类测试")
    print("=" * 40)
    
    try:
        # 获取现有分类
        categories = publisher.get_categories()
        if categories:
            print(f"📋 现有分类 ({len(categories)}个):")
            for cat in categories[:5]:  # 显示前5个
                print(f"   - {cat['name']} (ID: {cat['id']})")
            if len(categories) > 5:
                print(f"   ... 还有 {len(categories) - 5} 个分类")
        
        # 测试创建分类
        test_category = "Twitter推文测试"
        print(f"\n🆕 测试创建分类: {test_category}")
        
        # 检查是否已存在
        existing = [cat for cat in categories if cat['name'] == test_category]
        if existing:
            print(f"📋 分类已存在: {test_category} (ID: {existing[0]['id']})")
        else:
            new_cat = publisher.create_category(test_category, "测试分类，用于Twitter推文自动发布测试")
            if new_cat:
                print(f"✅ 成功创建测试分类: {test_category}")
            else:
                print(f"❌ 创建测试分类失败")
        
        return True
        
    except Exception as e:
        print(f"❌ 分类测试异常: {str(e)}")
        return False

def create_test_tweet_data():
    """创建测试推文数据"""
    from datetime import datetime
    
    test_tweets = {
        'test_user': [{
            'id': '1234567890',
            'text': '这是一条测试推文，用于验证WordPress发布功能。包含表情符号 🚀 和链接 https://example.com',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'retweet_count': 10,
            'like_count': 50,
            'reply_count': 5,
            'quote_count': 2,
            'language': 'zh',
            'url': 'https://twitter.com/test_user/status/1234567890'
        }]
    }
    
    return test_tweets

def test_wordpress_publish(publisher):
    """测试WordPress发布功能"""
    print("\n📝 WordPress发布测试")
    print("=" * 40)
    
    try:
        # 创建测试数据
        test_tweets = create_test_tweet_data()
        
        print("📋 测试推文数据:")
        for username, tweets in test_tweets.items():
            print(f"   @{username}: {len(tweets)} 条推文")
            for tweet in tweets:
                print(f"     - {tweet['text'][:50]}...")
        
        print("\n🚀 开始发布测试...")
        results = publisher.publish_tweets_as_posts(
            test_tweets,
            post_status='draft',  # 使用草稿状态测试
            category_name='Twitter推文测试'
        )
        
        if results:
            success_count = len([r for r in results if r['status'] == 'success'])
            print(f"\n✅ 发布测试完成!")
            print(f"   成功: {success_count} 篇")
            print(f"   总计: {len(results)} 篇")
            
            for result in results:
                if result['status'] == 'success':
                    print(f"   📄 文章: {result['post_url']}")
            
            return True
        else:
            print("❌ 发布测试失败 - 无结果返回")
            return False
            
    except Exception as e:
        print(f"❌ 发布测试异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🧪 Twitter to WordPress 集成测试")
    print("=" * 50)
    
    # 检查Twitter Bearer Token
    if not os.getenv('TWITTER_BEARER_TOKEN'):
        print("⚠️  注意: 未设置 TWITTER_BEARER_TOKEN，将跳过Twitter API测试")
    
    # 测试WordPress配置
    if not test_wordpress_config():
        print("\n❌ WordPress配置测试失败，无法继续")
        return
    
    # 测试WordPress连接
    publisher = test_wordpress_connection()
    if not publisher:
        print("\n❌ WordPress连接测试失败，无法继续")
        return
    
    # 测试分类功能
    if not test_wordpress_categories(publisher):
        print("\n❌ WordPress分类测试失败")
        return
    
    # 询问是否进行发布测试
    print("\n" + "=" * 50)
    choice = input("🤔 是否进行WordPress发布测试？这将创建一篇草稿文章 (y/N): ").lower()
    
    if choice in ['y', 'yes']:
        if test_wordpress_publish(publisher):
            print("\n🎉 所有测试通过!")
            print("💡 请登录WordPress后台查看测试文章")
        else:
            print("\n❌ 发布测试失败")
    else:
        print("\n✅ 跳过发布测试，连接和分类测试已通过")
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")

if __name__ == '__main__':
    main()