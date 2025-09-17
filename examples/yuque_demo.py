#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语雀发布功能演示脚本
演示如何使用新的语雀发布功能替代WordPress
"""

import os
import sys
from pathlib import Path

# 添加src目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

def main():
    """主演示函数"""
    print("🚀 语雀发布功能演示")
    print("=" * 60)
    
    # 检查环境变量配置
    print("📋 检查环境变量配置...")
    
    twitter_token = os.getenv('TWITTER_BEARER_TOKEN')
    yuque_token = os.getenv('YUQUE_TOKEN')
    yuque_namespace = os.getenv('YUQUE_NAMESPACE')
    
    if not twitter_token:
        print("❌ 缺少 TWITTER_BEARER_TOKEN 环境变量")
        print("💡 请设置Twitter API Bearer Token")
        return False
    
    if not yuque_token:
        print("❌ 缺少 YUQUE_TOKEN 环境变量")
        print("💡 请设置语雀API Token")
        print("🔗 获取地址: https://www.yuque.com/settings/tokens")
        return False
    
    if not yuque_namespace:
        print("❌ 缺少 YUQUE_NAMESPACE 环境变量")
        print("💡 请设置知识库命名空间，格式：owner_login/book_slug")
        return False
    
    print("✅ 环境变量配置检查通过")
    print(f"  📊 Twitter Token: {twitter_token[:10]}...")
    print(f"  📚 语雀 Token: {yuque_token[:10]}...")
    print(f"  📖 知识库命名空间: {yuque_namespace}")
    
    # 导入并创建爬虫实例
    try:
        from twitter_scraper import TwitterScraper
        
        # 配置语雀发布参数
        yuque_config = {
            'yuque_token': yuque_token,
            'yuque_namespace': yuque_namespace,
            'yuque_base_url': os.getenv('YUQUE_BASE_URL', 'https://yuque-api.antfin-inc.com')
        }
        
        print(f"\n🔧 创建Twitter爬虫实例...")
        scraper = TwitterScraper(
            bearer_token=twitter_token,
            api_tier=os.getenv('TWITTER_API_TIER', 'free'),
            safety_factor=float(os.getenv('TWITTER_SAFETY_FACTOR', '0.8')),
            wordpress_config=yuque_config  # 复用参数名保持兼容性
        )
        
        if not scraper.yuque_publisher:
            print("❌ 语雀发布器初始化失败")
            return False
        
        print("✅ 语雀发布器初始化成功")
        
        # 测试API连接
        print(f"\n🔗 测试语雀API连接...")
        if not scraper.yuque_publisher.test_connection():
            print("❌ 语雀API连接测试失败")
            return False
        
        # 演示推文获取和发布
        print(f"\n🐦 演示推文获取和发布...")
        
        # 使用一个知名的测试用户（推文较多且稳定）
        test_user = 'elonmusk'
        print(f"📱 获取 @{test_user} 的最新推文...")
        
        tweets = scraper.get_tweets([test_user], days=1)
        
        if tweets and tweets.get(test_user):
            user_tweets = tweets[test_user]
            print(f"✅ 成功获取 {len(user_tweets)} 条推文")
            
            if len(user_tweets) > 0:
                print(f"\n📝 演示发布第一条推文到语雀...")
                
                # 只发布第一条推文作为演示
                demo_tweets = {test_user: user_tweets[:1]}
                
                results = scraper.yuque_publisher.publish_tweets_as_documents(
                    demo_tweets,
                    doc_format=os.getenv('YUQUE_DOC_FORMAT', 'markdown'),
                    public=int(os.getenv('YUQUE_DOC_PUBLIC', '0')),
                    avoid_duplicates=True
                )
                
                if results:
                    success_count = len([r for r in results if r['status'] == 'success'])
                    skipped_count = len([r for r in results if r['status'] == 'skipped'])
                    failed_count = len([r for r in results if r['status'] == 'failed'])
                    
                    print(f"\n🎯 发布结果统计:")
                    print(f"  ✅ 成功: {success_count}")
                    print(f"  ⏭️ 跳过: {skipped_count}")
                    print(f"  ❌ 失败: {failed_count}")
                    
                    for result in results:
                        if result['status'] == 'success':
                            print(f"  🔗 文档链接: {result['doc_url']}")
                        elif result['status'] == 'skipped':
                            print(f"  ⚠️ 跳过原因: {result.get('reason', 'unknown')}")
                    
                    print(f"\n🎉 语雀发布功能演示完成！")
                    return True
                else:
                    print("❌ 发布结果为空")
                    return False
            else:
                print("⚠️ 没有获取到推文数据，无法演示发布功能")
                return False
        else:
            print(f"❌ 未能获取到 @{test_user} 的推文")
            return False
            
    except ImportError as e:
        print(f"❌ 导入模块失败: {str(e)}")
        print("💡 请确保在项目根目录运行此脚本")
        return False
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {str(e)}")
        return False


def show_configuration_help():
    """显示配置帮助信息"""
    print("\n📚 环境变量配置帮助")
    print("=" * 60)
    print("请设置以下环境变量：")
    print()
    print("# Twitter API配置")
    print("export TWITTER_BEARER_TOKEN='your_twitter_token'")
    print()
    print("# 语雀API配置")
    print("export YUQUE_TOKEN='your_yuque_token'")
    print("export YUQUE_NAMESPACE='owner_login/book_slug'")
    print()
    print("# 可选配置")
    print("export YUQUE_BASE_URL='https://yuque-api.antfin-inc.com'")
    print("export YUQUE_DOC_FORMAT='markdown'  # 或 'html'")
    print("export YUQUE_DOC_PUBLIC='0'  # 0-私密, 1-公开")
    print("export TWITTER_API_TIER='free'")
    print("export TWITTER_SAFETY_FACTOR='0.8'")
    print()
    print("🔗 获取语雀Token: https://www.yuque.com/settings/tokens")
    print("📖 详细配置说明: 查看 YUQUE_GUIDE.md")


if __name__ == "__main__":
    print("🌟 欢迎使用语雀发布功能演示")
    print()
    
    # 检查是否需要显示帮助
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_configuration_help()
        sys.exit(0)
    
    # 运行演示
    success = main()
    
    if not success:
        print("\n💡 如需帮助，请运行：")
        print("python examples/yuque_demo.py --help")
        print("\n📖 或查看详细配置指南：")
        print("cat YUQUE_GUIDE.md")
        sys.exit(1)
    else:
        print("\n🎊 演示成功完成！")
        print("💡 您现在可以使用 python main.py 运行完整的爬虫程序")
        sys.exit(0)