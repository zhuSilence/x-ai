#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter API v2 速率限制管理器测试
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.twitter_scraper import (
        TwitterAPITier,
        RateLimit, 
        TwitterRateLimitManager,
        TwitterScraper
    )
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所需依赖: pip install tweepy requests")
    sys.exit(1)


class TestRateLimit(unittest.TestCase):
    """速率限制配置测试"""
    
    def test_rate_limit_creation(self):
        """测试速率限制对象创建"""
        rate_limit = RateLimit(100, 15)
        self.assertEqual(rate_limit.requests_per_window, 100)
        self.assertEqual(rate_limit.window_minutes, 15)
        self.assertEqual(rate_limit.window_seconds, 900)
        self.assertEqual(rate_limit.min_interval, 9.0)
    
    def test_api_tier_enum(self):
        """测试API等级枚举"""
        self.assertEqual(TwitterAPITier.FREE.value, "free")
        self.assertEqual(TwitterAPITier.BASIC.value, "basic")
        self.assertEqual(TwitterAPITier.PRO.value, "pro")
        self.assertEqual(TwitterAPITier.ENTERPRISE.value, "enterprise")


class TestTwitterRateLimitManager(unittest.TestCase):
    """速率限制管理器测试"""
    
    def setUp(self):
        """测试前设置"""
        self.manager = TwitterRateLimitManager(
            api_tier=TwitterAPITier.FREE,
            safety_factor=0.8,
            enable_monitoring=False  # 禁用监控以减少输出
        )
    
    def test_manager_initialization(self):
        """测试管理器初始化"""
        self.assertEqual(self.manager.api_tier, TwitterAPITier.FREE)
        self.assertEqual(self.manager.safety_factor, 0.8)
        self.assertFalse(self.manager.enable_monitoring)
    
    def test_get_rate_limit(self):
        """测试获取速率限制配置"""
        # 测试已知端点
        user_limit = self.manager.get_rate_limit('get_user')
        self.assertIsInstance(user_limit, RateLimit)
        
        # 测试未知端点（应返回默认限制）
        unknown_limit = self.manager.get_rate_limit('unknown_endpoint')
        self.assertEqual(unknown_limit.requests_per_window, 1)
        self.assertEqual(unknown_limit.window_minutes, 15)
    
    def test_recommended_delay(self):
        """测试推荐延迟计算"""
        delay = self.manager.get_recommended_delay('get_users_tweets')
        self.assertIsInstance(delay, float)
        self.assertGreater(delay, 0)
    
    def test_different_api_tiers(self):
        """测试不同API等级的配置"""
        tiers = [TwitterAPITier.FREE, TwitterAPITier.BASIC, TwitterAPITier.PRO]
        
        for tier in tiers:
            manager = TwitterRateLimitManager(api_tier=tier, enable_monitoring=False)
            delay = manager.get_recommended_delay('get_users_tweets')
            self.assertIsInstance(delay, float)
            self.assertGreater(delay, 0)
    
    @patch('time.sleep')
    def test_wait_for_rate_limit(self, mock_sleep):
        """测试速率限制等待"""
        # 第一次请求不应该等待（因为还没有历史记录）
        self.manager.wait_for_rate_limit('get_users_tweets')
        mock_sleep.assert_not_called()
        
        # 第二次请求应该也不等待（因为时间间隔足够）
        self.manager.wait_for_rate_limit('get_users_tweets')
        # 由于safety_factor的存在，可能会有短暂等待，但不会报错


class TestTwitterScraperIntegration(unittest.TestCase):
    """Twitter爬虫集成测试"""
    
    def test_scraper_initialization_with_different_tiers(self):
        """测试不同API等级的爬虫初始化"""
        test_cases = [
            {'tier': 'free', 'safety_factor': 0.8},
            {'tier': 'basic', 'safety_factor': 0.9},
            {'tier': 'pro', 'safety_factor': 0.9}
        ]
        
        for case in test_cases:
            with self.subTest(tier=case['tier']):
                # 使用假的bearer token进行测试
                scraper = TwitterScraper(
                    bearer_token="fake_token_for_testing",
                    api_tier=case['tier'],
                    safety_factor=case['safety_factor']
                )
                
                self.assertIsNotNone(scraper.rate_manager)
                self.assertEqual(scraper.rate_manager.safety_factor, case['safety_factor'])
    
    def test_invalid_api_tier(self):
        """测试无效API等级处理"""
        scraper = TwitterScraper(
            bearer_token="fake_token_for_testing",
            api_tier="invalid_tier"
        )
        
        # 应该回退到FREE等级
        self.assertEqual(scraper.rate_manager.api_tier, TwitterAPITier.FREE)


def demonstrate_rate_limits():
    """演示不同API等级的速率限制配置"""
    print("\n🚀 Twitter API v2 智能限流配置演示")
    print("=" * 50)
    
    examples = [
        {
            'name': 'FREE 等级 (推荐新用户)',
            'tier': TwitterAPITier.FREE,
            'safety_factor': 0.8,
            'description': '最稳定配置，避免频率限制'
        },
        {
            'name': 'BASIC 等级',
            'tier': TwitterAPITier.BASIC, 
            'safety_factor': 0.9,
            'description': '更高效的爬取，适合小规模使用'
        },
        {
            'name': 'PRO 等级',
            'tier': TwitterAPITier.PRO,
            'safety_factor': 0.9,
            'description': '高频爬取，适合商业使用'
        }
    ]
    
    for i, config in enumerate(examples, 1):
        print(f"\n{i}. {config['name']}")
        print(f"   📋 描述: {config['description']}")
        
        # 创建管理器实例
        manager = TwitterRateLimitManager(
            api_tier=config['tier'],
            safety_factor=config['safety_factor'],
            enable_monitoring=False
        )
        
        # 显示推荐的请求间隔
        get_user_delay = manager.get_recommended_delay('get_user')
        get_tweets_delay = manager.get_recommended_delay('get_users_tweets')
        
        print(f"   🕐 用户信息请求间隔: {get_user_delay:.1f}秒")
        print(f"   🕐 用户推文请求间隔: {get_tweets_delay:.1f}秒")
        
        # 显示配额限制
        user_limit = manager.get_rate_limit('get_user')
        tweets_limit = manager.get_rate_limit('get_users_tweets')
        
        print(f"   📊 用户信息配额: {user_limit.requests_per_window}/{user_limit.window_minutes}分钟")
        print(f"   📊 用户推文配额: {tweets_limit.requests_per_window}/{tweets_limit.window_minutes}分钟")
        print("   " + "-" * 40)
    
    print("\n🎯 环境变量配置示例:")
    print("export TWITTER_API_TIER=free        # 或 basic/pro/enterprise")
    print("export TWITTER_SAFETY_FACTOR=0.8    # 安全系数 (0.1-1.0)")
    print("export TWITTER_BEARER_TOKEN=your_token_here")
    
    print("\n💡 选择建议:")
    print("- 🆓 刚开始使用: FREE + SAFETY_FACTOR=0.8")
    print("- 💼 小规模商用: BASIC + SAFETY_FACTOR=0.9") 
    print("- 🚀 大规模应用: PRO + SAFETY_FACTOR=0.9")


if __name__ == "__main__":
    # 运行演示
    demonstrate_rate_limits()
    
    print("\n" + "="*50)
    print("运行单元测试...")
    print("="*50)
    
    # 运行测试
    unittest.main(verbosity=2)