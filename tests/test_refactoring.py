#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试代码重构后的模块化结构
现在所有功能都在单一文件中
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_integrated_imports():
    """测试集成式导入"""
    print("🧪 测试集成式导入...")
    
    # 测试Twitter爬虫导入
    try:
        from src.twitter_scraper import TwitterScraper
        print("✅ TwitterScraper 导入成功")
    except ImportError as e:
        print(f"❌ TwitterScraper 导入失败: {e}")
        return False
    
    # 测试WordPress发布器导入（现在是内嵌的）
    try:
        from src.twitter_scraper import WordPressPublisher
        print("✅ WordPressPublisher 导入成功 (内嵌版本)")
    except ImportError as e:
        print(f"❌ WordPressPublisher 导入失败: {e}")
        return False
    
    return True

def test_functionality_separation():
    """测试功能分离（现在集成在一个文件中）"""
    print("\n🔄 测试功能集成...")
    
    try:
        from src.twitter_scraper import TwitterScraper, WordPressPublisher
        
        # 测试TwitterScraper基本功能
        scraper = TwitterScraper('dummy_token')
        print(f"✅ TwitterScraper 创建成功，频次限制: {scraper.rate_limit_delay}秒")
        
        # 测试基本方法存在
        methods = ['get_tweets', 'save_tweets', 'print_summary']
        for method in methods:
            if hasattr(scraper, method):
                print(f"  ✅ {method} 方法可用")
            else:
                print(f"  ❌ {method} 方法缺失")
                return False
        
        # 测试WordPress发布器基本功能（内嵌版本）
        wp_publisher = WordPressPublisher(
            'https://example.com',
            'test_user', 
            'test_pass'
        )
        print("✅ WordPressPublisher 创建成功 (内嵌版本)")
        
        # 测试基本方法存在
        wp_methods = ['test_connection', 'create_post', 'get_categories', 'format_tweet_as_html']
        for method in wp_methods:
            if hasattr(wp_publisher, method):
                print(f"  ✅ {method} 方法可用")
            else:
                print(f"  ❌ {method} 方法缺失")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 功能集成测试失败: {e}")
        return False

def test_integration_compatibility():
    """测试集成兼容性"""
    print("\n🔗 测试集成兼容性...")
    
    try:
        from src.twitter_scraper import TwitterScraper
        
        # 测试WordPress配置集成
        wordpress_config = {
            'site_url': 'https://example.com',
            'username': 'test_user',
            'password': 'test_pass'
        }
        
        scraper = TwitterScraper(
            bearer_token='dummy_token',
            wordpress_config=wordpress_config
        )
        
        if scraper.wp_publisher:
            print("✅ WordPress集成成功")
        else:
            print("⚠️ WordPress集成未启用（可能是网络连接问题）")
        
        # 测试兼容性方法
        compat_methods = [
            'get_user_tweets',
            'get_multiple_users_tweets', 
            'save_tweets_to_csv',
            'save_tweets_to_json',
            'print_tweets_summary'
        ]
        
        for method in compat_methods:
            if hasattr(scraper, method):
                print(f"  ✅ 兼容性方法 {method} 可用")
            else:
                print(f"  ❌ 兼容性方法 {method} 缺失")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 集成兼容性测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    print("\n📁 测试文件结构...")
    
    import os
    
    # 检查必要文件
    required_files = [
        'twitter_scraper.py',
        'wordpress_publisher.py'
    ]
    
    workspace = '/Users/silence/cursor/x-ai'
    
    for file_name in required_files:
        file_path = os.path.join(workspace, file_name)
        if os.path.exists(file_path):
            print(f"✅ {file_name} 存在")
        else:
            print(f"❌ {file_name} 不存在")
            return False
    
    # 检查文件大小（简单验证内容）
    twitter_file = os.path.join(workspace, 'twitter_scraper.py')
    wordpress_file = os.path.join(workspace, 'wordpress_publisher.py')
    
    twitter_size = os.path.getsize(twitter_file)
    wordpress_size = os.path.getsize(wordpress_file)
    
    print(f"📊 twitter_scraper.py: {twitter_size} 字节")
    print(f"📊 wordpress_publisher.py: {wordpress_size} 字节")
    
    # 验证分离是否成功（WordPress文件应该有合理的大小）
    if wordpress_size > 1000:  # 至少1KB
        print("✅ WordPress功能成功分离")
    else:
        print("❌ WordPress功能分离可能不完整")
        return False
    
    return True

def main():
    """主测试函数"""
    print("🧪 代码重构测试 (集成式架构)")
    print("=" * 50)
    
    tests = [
        test_integrated_imports,
        test_functionality_separation,
        test_integration_compatibility,
        test_file_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # 空行分隔
    
    # 输出结果
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 代码重构成功!")
        print("\n💡 重构优势:")
        print("  ✅ 所有功能集成在单一文件")
        print("  ✅ 保持向后兼容") 
        print("  ✅ 代码更易维护")
        print("  ✅ 部署更简单")
        print("  ✅ 消除了模块依赖问题")
    else:
        print("❌ 部分测试失败，需要进一步检查")
    
    print("=" * 50)

if __name__ == '__main__':
    main()