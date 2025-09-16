#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter推文爬取脚本
自动爬取指定用户最近一天的推文信息，支持WordPress自动发布
"""

import tweepy
import json
from datetime import datetime, timedelta
import os
import time
from typing import List, Dict, Optional, Any, Union
import threading
import requests
import base64
from urllib.parse import urljoin
from dataclasses import dataclass
from enum import Enum
import logging
from collections import defaultdict, deque


class TwitterAPITier(Enum):
    """Twitter API 计划等级"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class RateLimit:
    """速率限制配置"""
    requests_per_window: int  # 时间窗口内请求数
    window_minutes: int  # 时间窗口（分钟）
    is_per_user: bool = False  # 是否按用户计算
    is_per_app: bool = True   # 是否按应用计算
    
    @property
    def window_seconds(self) -> int:
        return self.window_minutes * 60
    
    @property
    def min_interval(self) -> float:
        """最小请求间隔（秒）"""
        return self.window_seconds / self.requests_per_window


class TwitterRateLimitManager:
    """Twitter API 速率限制管理器"""
    
    # API v2 速率限制配置（基于官方文档）
    RATE_LIMITS = {
        TwitterAPITier.FREE: {
            'get_user': RateLimit(1, 24 * 60, is_per_user=True),  # 1/24h per user
            'get_users_tweets': RateLimit(1, 15, is_per_user=True),  # 1/15min per user
            'search_recent': RateLimit(1, 15, is_per_user=True),  # 1/15min per user
        },
        TwitterAPITier.BASIC: {
            'get_user': RateLimit(500, 24 * 60, is_per_app=True),  # 500/24h per app
            'get_users_tweets': RateLimit(10, 15, is_per_app=True),  # 10/15min per app  
            'search_recent': RateLimit(60, 15, is_per_app=True),  # 60/15min per app
        },
        TwitterAPITier.PRO: {
            'get_user': RateLimit(300, 15, is_per_app=True),  # 300/15min per app
            'get_users_tweets': RateLimit(1500, 15, is_per_app=True),  # 1500/15min per app
            'search_recent': RateLimit(450, 15, is_per_app=True),  # 450/15min per app
        }
    }
    
    def __init__(self, api_tier: TwitterAPITier = TwitterAPITier.FREE, 
                 safety_factor: float = 0.8, enable_monitoring: bool = True):
        """
        初始化速率限制管理器
        
        Args:
            api_tier: API 计划等级
            safety_factor: 安全系数，降低实际请求频率以避免限制
            enable_monitoring: 是否启用请求监控
        """
        self.api_tier = api_tier
        self.safety_factor = safety_factor
        self.enable_monitoring = enable_monitoring
        
        # 请求时间记录 {endpoint: deque of timestamps}
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque())
        
        # 锁定机制
        self._lock = threading.Lock()
        
        # 响应头信息记录
        self.rate_limit_status: Dict[str, Dict] = {}
        
        # 设置日志
        self.logger = logging.getLogger(f"{__name__}.RateLimitManager")
        
        # 指数退避参数
        self.backoff_base = 1.0  # 基础退避时间
        self.backoff_max = 300.0  # 最大退避时间（5分钟）
        self.retry_attempts: Dict[str, int] = defaultdict(int)
        
        print(f"🔧 速率限制管理器初始化完成")
        print(f"  📊 API 等级: {api_tier.value.upper()}")
        print(f"  🛡️ 安全系数: {safety_factor:.1%}")
        print(f"  📈 监控状态: {'启用' if enable_monitoring else '禁用'}")
    
    def get_rate_limit(self, endpoint: str) -> RateLimit:
        """获取指定端点的速率限制配置"""
        limits = self.RATE_LIMITS.get(self.api_tier, {})
        return limits.get(endpoint, RateLimit(1, 15))  # 默认最严格限制
    
    def wait_for_rate_limit(self, endpoint: str) -> None:
        """等待满足速率限制要求"""
        with self._lock:
            rate_limit = self.get_rate_limit(endpoint)
            current_time = time.time()
            
            # 清理过期的请求记录
            self._cleanup_request_history(endpoint, current_time, rate_limit.window_seconds)
            
            # 计算当前时间窗口内的请求数
            recent_requests = len(self.request_history[endpoint])
            max_requests = int(rate_limit.requests_per_window * self.safety_factor)
            
            if recent_requests >= max_requests:
                # 需要等待
                if recent_requests > 0:  # 确保有历史记录再访问
                    oldest_request = self.request_history[endpoint][0]
                    wait_time = rate_limit.window_seconds - (current_time - oldest_request)
                    
                    if wait_time > 0:
                        print(f"⏳ [{endpoint}] 速率限制：需要等待 {wait_time:.1f} 秒")
                        print(f"   📊 当前窗口内请求数: {recent_requests}/{max_requests}")
                        time.sleep(wait_time)
            
            # 记录当前请求时间
            self.request_history[endpoint].append(current_time)
            
            if self.enable_monitoring:
                self._log_request_status(endpoint, rate_limit)
    
    def _cleanup_request_history(self, endpoint: str, current_time: float, window_seconds: int) -> None:
        """清理过期的请求记录"""
        history = self.request_history[endpoint]
        cutoff_time = current_time - window_seconds
        
        while history and history[0] < cutoff_time:
            history.popleft()
    
    def _log_request_status(self, endpoint: str, rate_limit: RateLimit) -> None:
        """记录请求状态"""
        recent_requests = len(self.request_history[endpoint])
        max_requests = int(rate_limit.requests_per_window * self.safety_factor)
        
        print(f"📊 [{endpoint}] 请求状态: {recent_requests}/{max_requests} "f"({rate_limit.window_minutes}分钟窗口)")
    
    def handle_rate_limit_response(self, endpoint: str, response_headers: Dict[str, str]) -> None:
        """处理API响应中的速率限制信息"""
        if not self.enable_monitoring:
            return
        
        # 解析速率限制响应头
        rate_info = {
            'limit': response_headers.get('x-rate-limit-limit'),
            'remaining': response_headers.get('x-rate-limit-remaining'), 
            'reset': response_headers.get('x-rate-limit-reset')
        }
        
        self.rate_limit_status[endpoint] = rate_info
        
        # 输出速率限制状态
        if rate_info['remaining']:
            remaining = int(rate_info['remaining'])
            if remaining <= 5:
                print(f"⚠️ [{endpoint}] 剩余请求数较低: {remaining}")
                if rate_info['reset']:
                    reset_time = datetime.fromtimestamp(int(rate_info['reset']))
                    print(f"   🕐 重置时间: {reset_time.strftime('%H:%M:%S')}")
    
    def handle_rate_limit_exceeded(self, endpoint: str, retry_after: Optional[int] = None) -> float:
        """处理速率限制超出，返回等待时间"""
        self.retry_attempts[endpoint] += 1
        attempt = self.retry_attempts[endpoint]
        
        if retry_after:
            wait_time = retry_after
            print(f"🚫 [{endpoint}] API速率限制，服务器要求等待 {wait_time} 秒")
        else:
            # 指数退避策略
            wait_time = min(self.backoff_base * (2 ** (attempt - 1)), self.backoff_max)
            print(f"🚫 [{endpoint}] 速率限制，指数退避等待 {wait_time:.1f} 秒 (尝试 #{attempt})")
        
        print(f"   💡 建议升级到更高等级的API计划以获得更多配额")
        time.sleep(wait_time)
        
        return wait_time
    
    def reset_retry_attempts(self, endpoint: str) -> None:
        """重置重试计数"""
        if endpoint in self.retry_attempts:
            self.retry_attempts[endpoint] = 0
    
    def get_recommended_delay(self, endpoint: str) -> float:
        """获取推荐的请求间隔"""
        rate_limit = self.get_rate_limit(endpoint)
        base_interval = rate_limit.min_interval
        
        # 应用安全系数
        safe_interval = base_interval / self.safety_factor
        
        # 考虑当前重试状态
        retry_multiplier = 1.0
        if endpoint in self.retry_attempts and self.retry_attempts[endpoint] > 0:
            retry_multiplier = 1.5 ** self.retry_attempts[endpoint]
        
        return safe_interval * retry_multiplier
    
    def print_status_summary(self) -> None:
        """打印速率限制状态摘要"""
        print("\n" + "="*50)
        print("=== 速率限制状态摘要 ===")
        print("="*50)
        print(f"API 等级: {self.api_tier.value.upper()}")
        print(f"安全系数: {self.safety_factor:.1%}")
        
        for endpoint, history in self.request_history.items():
            rate_limit = self.get_rate_limit(endpoint)
            max_requests = int(rate_limit.requests_per_window * self.safety_factor)
            recent_requests = len(history)
            
            print(f"\n📊 {endpoint}:")
            print(f"   配额使用: {recent_requests}/{max_requests} ({rate_limit.window_minutes}分钟窗口)")
            print(f"   推荐间隔: {self.get_recommended_delay(endpoint):.1f}秒")
            
            if endpoint in self.rate_limit_status:
                status = self.rate_limit_status[endpoint]
                if status.get('remaining'):
                    print(f"   API剩余: {status['remaining']}")


class WordPressPublisher:
    """WordPress发布器"""
    
    def __init__(self, site_url: str, username: str, password: str):
        self.site_url = site_url.rstrip('/')
        self.api_url = urljoin(self.site_url + '/', 'wp-json/wp/v2/')
        self.username = username
        self.password = password
        
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json',
            'User-Agent': 'Twitter-WordPress-Publisher/1.0'
        }
    
    def test_connection(self) -> bool:
        try:
            response = requests.get(
                urljoin(self.api_url, 'users/me'),
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                user_info = response.json()
                print(f"✅ WordPress连接成功，当前用户: {user_info.get('name', 'Unknown')}")
                return True
            else:
                print(f"❌ WordPress连接失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ WordPress连接测试失败: {str(e)}")
            return False
    
    def create_post(self, title: str, content: str, status: str = 'draft', 
                   category_ids: Optional[List[int]] = None, tag_ids: Optional[List[int]] = None) -> Optional[Dict]:
        post_data: Dict[str, Union[str, List[int]]] = {
            'title': title,
            'content': content,
            'status': status,
            'format': 'standard'
        }
        
        if category_ids:
            post_data['categories'] = category_ids
        if tag_ids:
            post_data['tags'] = tag_ids
        
        try:
            response = requests.post(
                urljoin(self.api_url, 'posts'),
                headers=self.headers,
                json=post_data,
                timeout=30
            )
            
            if response.status_code == 201:
                post_info = response.json()
                print(f"✅ 文章创建成功: {post_info['title']['rendered']}")
                return post_info
            else:
                print(f"❌ 文章创建失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 创建文章时发生错误: {str(e)}")
            return None
    
    def get_categories(self) -> List[Dict]:
        try:
            response = requests.get(
                urljoin(self.api_url, 'categories'),
                headers=self.headers,
                params={'per_page': 100},
                timeout=10
            )
            
            if response.status_code == 200:
                categories = response.json()
                return categories
            else:
                return []
        except Exception as e:
            print(f"❌ 获取分类时发生错误: {str(e)}")
            return []
    
    def create_category(self, name: str, description: str = '') -> Optional[Dict]:
        category_data = {'name': name, 'description': description}
        
        try:
            response = requests.post(
                urljoin(self.api_url, 'categories'),
                headers=self.headers,
                json=category_data,
                timeout=10
            )
            
            if response.status_code == 201:
                category_info = response.json()
                print(f"✅ 分类创建成功: {category_info['name']}")
                return category_info
            else:
                return None
        except Exception as e:
            print(f"❌ 创建分类时发生错误: {str(e)}")
            return None
    
    def format_tweet_as_html(self, tweet: Dict, username: str) -> str:
        html_content = f"""
        <div class="twitter-post">
            <div class="tweet-header">
                <h3>🐦 来自 @{username} 的推文</h3>
                <p class="tweet-meta">
                    <strong>发布时间:</strong> {tweet['created_at']}<br>
                    <strong>原文链接:</strong> <a href="{tweet['url']}" target="_blank">{tweet['url']}</a>
                </p>
            </div>
            
            <div class="tweet-content">
                <blockquote>
                    {tweet['text'].replace(chr(10), '<br>')}
                </blockquote>
            </div>
            
            <div class="tweet-stats">
                <p class="engagement-stats">
                    👍 <strong>{tweet['like_count']:,}</strong> 点赞 | 
                    🔄 <strong>{tweet['retweet_count']:,}</strong> 转发 | 
                    💬 <strong>{tweet['reply_count']:,}</strong> 回复 | 
                    📝 <strong>{tweet['quote_count']:,}</strong> 引用
                </p>
            </div>
            
            <div class="tweet-footer">
                <p><small>📱 语言: {tweet.get('language', 'unknown')} | 推文ID: {tweet['id']}</small></p>
            </div>
        </div>
        
        <style>
        .twitter-post {{
            border: 1px solid #e1e8ed;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            background: #f8f9fa;
        }}
        .tweet-header h3 {{
            color: #1da1f2;
            margin-bottom: 10px;
        }}
        .tweet-content blockquote {{
            font-size: 18px;
            line-height: 1.6;
            margin: 15px 0;
            padding: 15px;
            background: white;
            border-left: 4px solid #1da1f2;
            border-radius: 8px;
        }}
        .engagement-stats {{
            background: white;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
        }}
        .tweet-meta, .tweet-footer {{
            color: #657786;
            font-size: 14px;
        }}
        </style>
        """
        return html_content
    
    def publish_tweets_as_posts(self, tweets_data: Dict[str, List[Dict]], 
                               post_status: str = 'draft',
                               category_name: str = 'Twitter推文') -> List[Dict]:
        results = []
        
        # 获取或创建分类
        categories = self.get_categories()
        category_id = None
        
        for cat in categories:
            if cat['name'] == category_name:
                category_id = cat['id']
                break
        
        if not category_id:
            new_category = self.create_category(category_name, 'Twitter推文自动发布分类')
            if new_category:
                category_id = new_category['id']
        
        category_ids = [category_id] if category_id else []
        
        # 发布每个用户的推文
        for username, tweets in tweets_data.items():
            if not tweets:
                continue
                
            print(f"\n📝 正在发布 @{username} 的推文...")
            
            for i, tweet in enumerate(tweets):
                # 创建文章标题
                title = f"@{username} 的推文 - {tweet['created_at'][:10]}"
                
                # 格式化内容
                content = self.format_tweet_as_html(tweet, username)
                
                # 创建文章
                post_result = self.create_post(
                    title=title,
                    content=content,
                    status=post_status,
                    category_ids=category_ids
                )
                
                if post_result:
                    results.append({
                        'username': username,
                        'tweet_id': tweet['id'],
                        'post_id': post_result['id'],
                        'post_url': post_result['link'],
                        'status': 'success'
                    })
                else:
                    results.append({
                        'username': username,
                        'tweet_id': tweet['id'],
                        'status': 'failed'
                    })
                
                # 发布间隔，避免过快请求
                time.sleep(1)
                
                # 限制每个用户最多发布的推文数量
                if i >= 4:  # 每个用户最多发布5条推文
                    print(f"⚠️ @{username} 推文数量较多，仅发布前5条")
                    break
        
        return results


class TwitterScraper:
    def __init__(self, bearer_token: str, api_tier: str = 'free', 
                 safety_factor: float = 0.8, wordpress_config: Optional[Dict] = None):
        """
        初始化Twitter爬虫
        
        Args:
            bearer_token: Twitter API v2的Bearer Token
            api_tier: API 计划等级 ('free', 'basic', 'pro', 'enterprise')
            safety_factor: 安全系数，降低实际请求频率以避免限制
            wordpress_config: WordPress配置字典 {'site_url': str, 'username': str, 'password': str}
        """
        self.client = tweepy.Client(bearer_token=bearer_token)
        
        # 初始化速率限制管理器
        try:
            tier_enum = TwitterAPITier(api_tier.lower())
        except ValueError:
            print(f"⚠️ 不支持的API等级: {api_tier}，使用默认的 'free' 等级")
            tier_enum = TwitterAPITier.FREE
        
        self.rate_manager = TwitterRateLimitManager(
            api_tier=tier_enum,
            safety_factor=safety_factor,
            enable_monitoring=True
        )
        
        # 旧的属性保持兼容性
        self.rate_limit_delay = self.rate_manager.get_recommended_delay('get_users_tweets')
        self.last_request_time = 0
        self._request_lock = threading.Lock()
        
        # 初始化WordPress发布器
        self.wp_publisher = None
        if wordpress_config:
            try:
                self.wp_publisher = WordPressPublisher(
                    wordpress_config['site_url'],
                    wordpress_config['username'],
                    wordpress_config['password']
                )
                print("📝 WordPress发布器初始化成功")
            except Exception as e:
                print(f"⚠️ WordPress发布器初始化失败: {str(e)}")
                self.wp_publisher = None
        
        # 显示初始化信息
        print(f"\n🚀 TwitterScraper 初始化完成")
        print(f"  📊 API 等级: {tier_enum.value.upper()}")
        print(f"  ⏱️ 推荐间隔: {self.rate_limit_delay:.1f}秒")
        print(f"  🛡️ 安全系数: {safety_factor:.1%}")
        
    def _wait_for_rate_limit(self, endpoint: str = 'get_users_tweets'):
        """
        使用新的速率限制管理器
        保持向后兼容性
        """
        self.rate_manager.wait_for_rate_limit(endpoint)
    
    def get_tweets(self, usernames, days: int = 1) -> Dict[str, List[Dict]]:
        """
        获取用户推文
        
        Args:
            usernames: 用户名（字符串）或用户名列表
            days: 获取最近几天的推文，默认1天
            
        Returns:
            字典，键为用户名，值为该用户的推文列表
        """
        # 统一处理为列表格式
        if isinstance(usernames, str):
            usernames = [usernames]
        
        all_tweets = {}
        total_users = len(usernames)
        
        print(f"🐦 开始获取 {total_users} 个用户的推文...\n")
        
        for i, username in enumerate(usernames, 1):
            print(f"\n[{i}/{total_users}] 正在处理用户: @{username}")
            
            tweets = self._get_single_user_tweets(username, days)
            all_tweets[username] = tweets
            
            # 处理完一个用户后的额外延迟（避免连续请求）
            if i < total_users:
                extra_delay = self.rate_manager.get_recommended_delay('get_users_tweets') * 0.3
                print(f"⏱️  用户间延迟: {extra_delay:.1f}秒")
                time.sleep(extra_delay)
        
        return all_tweets
    
    def _get_single_user_tweets(self, username: str, days: int = 1) -> List[Dict]:
        """
        获取单个用户的推文
        
        Args:
            username: Twitter用户名（不包含@符号）
            days: 获取最近几天的推文，默认1天
            
        Returns:
            推文列表，每个推文包含详细信息
        """
        try:
            # 频次限制控制 - 查询用户信息
            self._wait_for_rate_limit('get_user')
            
            # 获取用户信息
            print(f"🔍 正在查询用户 @{username} 的信息...")
            user_response = self.client.get_user(username=username)
            
            # 处理响应头信息
            if hasattr(user_response, 'headers'):
                self.rate_manager.handle_rate_limit_response('get_user', user_response.headers)
            
            if not user_response or not hasattr(user_response, 'data') or not user_response.data:  # type: ignore
                print(f"用户 @{username} 不存在")
                return []
            
            user = user_response.data  # type: ignore
            user_id = user.id
            print(f"找到用户: {user.name} (@{username})")
            
            # 重置重试计数（成功获取用户信息）
            self.rate_manager.reset_retry_attempts('get_user')
            
            # 计算时间范围（使用一天的开始和结束时间）
            end_time = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
            start_time = (end_time - timedelta(days=days-1)).replace(hour=0, minute=0, second=0, microsecond=0)
            
            print(f"正在获取 {start_time.strftime('%Y-%m-%d %H:%M')} 到 {end_time.strftime('%Y-%m-%d %H:%M')} 的推文...")
            
            # 频次限制控制 - 获取推文
            self._wait_for_rate_limit('get_users_tweets')
            
            # 获取推文
            print(f"📡 正在请求 @{username} 的推文数据...")
            tweets_response = tweepy.Paginator(
                self.client.get_users_tweets,
                id=user_id,
                start_time=start_time,
                end_time=end_time,
                tweet_fields=['created_at', 'public_metrics', 'context_annotations', 'lang', 'reply_settings'],
                user_fields=['name', 'username', 'verified', 'public_metrics'],
                expansions=['author_id'],
                max_results=100
            ).flatten(limit=1000)
            
            # 处理响应头信息（对于tweepy.Paginator，需要特殊处理）
            # 注意：tweepy.Paginator可能不直接提供响应头，这里可以优化
            
            tweet_list = []
            for tweet in tweets_response:
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'retweet_count': tweet.public_metrics['retweet_count'],
                    'like_count': tweet.public_metrics['like_count'],
                    'reply_count': tweet.public_metrics['reply_count'],
                    'quote_count': tweet.public_metrics['quote_count'],
                    'language': tweet.lang,
                    'url': f"https://twitter.com/{username}/status/{tweet.id}"
                }
                tweet_list.append(tweet_data)
            
            # 重置重试计数（成功获取推文）
            self.rate_manager.reset_retry_attempts('get_users_tweets')
            
            print(f"✅ 成功获取 {len(tweet_list)} 条推文")
            return tweet_list
            
        except tweepy.TooManyRequests as e:
            print(f"⚠️  API请求频率限制 - {str(e)}")
            
            # 获取retry-after头
            retry_after = None
            if hasattr(e, 'response') and e.response and hasattr(e.response, 'headers'):
                retry_after = e.response.headers.get('retry-after')
                if retry_after:
                    retry_after = int(retry_after)
            
            # 使用新的限制处理方法
            wait_time = self.rate_manager.handle_rate_limit_exceeded('get_users_tweets', retry_after)
            
            print(f"💡 建议：")
            print(f"   - 升级到更高等级的API计划")
            print(f"   - 增加safety_factor参数降低请求频率")
            print(f"   - 当前配置: {self.rate_manager.api_tier.value.upper()} 计划")
            
            return []
            
        except tweepy.Unauthorized as e:
            print(f"🔐 API认证失败 - {str(e)}")
            print("💡 请检查Bearer Token是否正确")
            return []
            
        except Exception as e:
            print(f"❌ 获取推文时发生错误: {str(e)}")
            print(f"🔄 当前配置: {self.rate_manager.api_tier.value.upper()} 计划")
            return []
    
    def save_tweets(self, tweets_data, filename_prefix: str = 'tweets'):
        """
        保存推文数据为JSON格式
        
        Args:
            tweets_data: 推文数据（列表或字典格式）
            filename_prefix: 文件名前缀
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 统一处理数据格式
        if isinstance(tweets_data, list):
            # 单用户数据转换为字典格式
            tweets_data = {'tweets': tweets_data}
            is_single_user = True
        else:
            is_single_user = False
        
        if not any(tweets for tweets in tweets_data.values()):
            print("没有推文数据可保存")
            return
        
        # 生成合并数据
        combined_tweets = []
        for username, tweets in tweets_data.items():
            for tweet in tweets:
                tweet_with_user = tweet.copy()
                if not is_single_user:
                    tweet_with_user['username'] = username
                combined_tweets.append(tweet_with_user)
        
        # 按时间排序
        combined_tweets.sort(key=lambda x: x['created_at'], reverse=True)
        
        if is_single_user:
            filename = f"{filename_prefix}_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(combined_tweets, f, ensure_ascii=False, indent=2)
            print(f"📄 JSON文件已保存: {filename}")
        else:
            filename = f"{filename_prefix}_multiple_users_{timestamp}.json"
            output_data = {
                'timestamp': timestamp,
                'total_users': len(tweets_data),
                'total_tweets': len(combined_tweets),
                'users_data': tweets_data,
                'combined_tweets': combined_tweets
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"📄 详细JSON文件已保存: {filename}")
        
        # 为每个用户单独保存JSON文件
        if not is_single_user:
            for username, tweets in tweets_data.items():
                if tweets:
                    user_filename = f"{filename_prefix}_{username}_{timestamp}.json"
                    with open(user_filename, 'w', encoding='utf-8') as f:
                        json.dump(tweets, f, ensure_ascii=False, indent=2)
            
            print(f"📁 单独用户JSON文件也已保存")
    

    def print_summary(self, tweets_data):
        """
        打印推文统计摘要
        
        Args:
            tweets_data: 推文数据（列表或字典格式）
        """
        # 统一处理数据格式
        if isinstance(tweets_data, list):
            # 单用户格式
            tweets = tweets_data
            if not tweets:
                print("没有推文数据")
                return
            
            total_tweets = len(tweets)
            total_likes = sum(tweet['like_count'] for tweet in tweets)
            total_retweets = sum(tweet['retweet_count'] for tweet in tweets)
            total_replies = sum(tweet['reply_count'] for tweet in tweets)
            
            print("\n=== 推文统计摘要 ===")
            print(f"总推文数: {total_tweets}")
            print(f"总点赞数: {total_likes:,}")
            print(f"总转发数: {total_retweets:,}")
            print(f"总回复数: {total_replies:,}")
            
            if total_tweets > 0:
                print(f"平均点赞数: {total_likes/total_tweets:.1f}")
                print(f"平均转发数: {total_retweets/total_tweets:.1f}")
                print(f"平均回复数: {total_replies/total_tweets:.1f}")
        else:
            # 多用户格式
            all_tweets = tweets_data
            print("\n" + "="*50)
            print("=== 多用户推文统计摘要 ===")
            print("="*50)
            
            total_users = len(all_tweets)
            total_tweets_all = 0
            total_likes_all = 0
            total_retweets_all = 0
            total_replies_all = 0
            
            print(f"\n📊 用户数量: {total_users}")
            print("\n📈 各用户统计:")
            
            for username, tweets in all_tweets.items():
                tweet_count = len(tweets)
                total_tweets_all += tweet_count
                
                if tweets:
                    likes = sum(tweet['like_count'] for tweet in tweets)
                    retweets = sum(tweet['retweet_count'] for tweet in tweets)
                    replies = sum(tweet['reply_count'] for tweet in tweets)
                    
                    total_likes_all += likes
                    total_retweets_all += retweets
                    total_replies_all += replies
                    
                    print(f"  @{username}:")
                    print(f"    推文: {tweet_count:,} | 点赞: {likes:,} | 转发: {retweets:,} | 回复: {replies:,}")
                else:
                    print(f"  @{username}: 无推文数据")
            
            print(f"\n🎯 总计统计:")
            print(f"  总推文数: {total_tweets_all:,}")
            print(f"  总点赞数: {total_likes_all:,}")
            print(f"  总转发数: {total_retweets_all:,}")
            print(f"  总回复数: {total_replies_all:,}")
            
            if total_tweets_all > 0:
                print(f"\n📈 平均数据:")
                print(f"  每用户推文: {total_tweets_all/total_users:.1f}")
                print(f"  每推文点赞: {total_likes_all/total_tweets_all:.1f}")
                print(f"  每推文转发: {total_retweets_all/total_tweets_all:.1f}")
                print(f"  每推文回复: {total_replies_all/total_tweets_all:.1f}")
    

    def publish_to_wordpress(self, tweets_data, 
                           post_status: str = 'draft', 
                           category_name: str = 'Twitter推文') -> Optional[List[Dict]]:
        """
        将获取的推文发布到WordPress
        
        Args:
            tweets_data: 推文数据（列表或字典格式）
            post_status: 文章发布状态 ('draft', 'publish', 'private')
            category_name: WordPress分类名称
            
        Returns:
            发布结果列表或None
        """
        if not self.wp_publisher:
            print("❌ WordPress发布器未初始化，无法发布推文")
            print("💡 请在初始化TwitterScraper时提供wordpress_config参数")
            return None
        
        # 测试WordPress连接
        if not self.wp_publisher.test_connection():
            print("❌ WordPress连接测试失败，取消发布")
            return None
        
        print(f"\n🚀 开始将推文发布到WordPress...")
        print(f"📝 发布状态: {post_status}")
        print(f"📁 分类名称: {category_name}")
        
        # 统一处理数据格式
        if isinstance(tweets_data, list):
            # 单用户数据转换为字典格式
            tweets_data = {'tweets': tweets_data}
        
        # 过滤有效的推文数据
        valid_tweets = {k: v for k, v in tweets_data.items() if v}
        if not valid_tweets:
            print("⚠️ 没有有效的推文数据可发布")
            return []
        
        # 发布推文
        results = self.wp_publisher.publish_tweets_as_posts(
            valid_tweets, 
            post_status=post_status, 
            category_name=category_name
        )
        
        # 统计发布结果
        success_count = len([r for r in results if r['status'] == 'success'])
        failed_count = len([r for r in results if r['status'] == 'failed'])
        
        print(f"\n📊 WordPress发布统计:")
        print(f"  ✅ 成功: {success_count} 篇文章")
        print(f"  ❌ 失败: {failed_count} 篇文章")
        print(f"  📝 总计: {len(results)} 篇文章")
        
        # 显示成功发布的文章链接
        if success_count > 0:
            print(f"\n🔗 成功发布的文章:")
            for result in results:
                if result['status'] == 'success':
                    print(f"  - @{result['username']}: {result['post_url']}")
        
        return results

def load_users_from_config(config_file: str = 'config/users_config.txt') -> List[str]:
    """
    从配置文件中加载用户名列表
    
    Args:
        config_file: 配置文件路径，默认为'config/users_config.txt'
        
    Returns:
        用户名列表
    """
    users = []
    
    if not os.path.exists(config_file):
        print(f"警告: 配置文件 {config_file} 不存在，使用默认用户列表")
        return ['elonmusk', 'sundarpichai', 'tim_cook', 'satyanadella']
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # 去除首尾空白字符
                line = line.strip()
                
                # 忽略空行和注释行
                if not line or line.startswith('#'):
                    continue
                
                # 移除@符号（如果用户添加了）
                username = line.lstrip('@')
                
                # 验证用户名格式（简单验证）
                if username and username.replace('_', '').replace('.', '').isalnum():
                    users.append(username)
                else:
                    print(f"警告: 第{line_num}行的用户名格式可能不正确: {line}")
        
        print(f"从配置文件 {config_file} 中加载了 {len(users)} 个用户")
        if users:
            print(f"用户列表: {', '.join(['@' + u for u in users])}")
        
        return users
        
    except Exception as e:
        print(f"读取配置文件时发生错误: {str(e)}")
        print("使用默认用户列表")
        return ['elonmusk', 'sundarpichai', 'tim_cook', 'satyanadella']

def main():
    """
    主函数
    """
    # 配置参数
    BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')  # 从环境变量获取
    
    # 新的速率限制配置
    API_TIER = os.getenv('TWITTER_API_TIER', 'free').lower()  # API等级
    SAFETY_FACTOR = float(os.getenv('TWITTER_SAFETY_FACTOR', '0.8'))  # 安全系数
    
    # 向后兼容的配置（已弃用但仍支持）
    RATE_LIMIT_DELAY = float(os.getenv('TWITTER_RATE_DELAY', '10.0'))  # 频次限制延迟（秒），默认10秒
    
    # WordPress配置（可选）
    WORDPRESS_SITE_URL = os.getenv('WORDPRESS_SITE_URL')  # WordPress站点URL
    WORDPRESS_USERNAME = os.getenv('WORDPRESS_USERNAME')  # WordPress用户名
    WORDPRESS_PASSWORD = os.getenv('WORDPRESS_PASSWORD')  # WordPress密码或应用密码
    
    # WordPress发布设置
    PUBLISH_TO_WORDPRESS = os.getenv('PUBLISH_TO_WORDPRESS', 'false').lower() == 'true'
    WORDPRESS_POST_STATUS = os.getenv('WORDPRESS_POST_STATUS', 'draft')  # draft, publish, private
    WORDPRESS_CATEGORY = os.getenv('WORDPRESS_CATEGORY', 'Twitter推文')  # WordPress分类
    
    # 从配置文件加载用户名
    USERNAMES = load_users_from_config('config/users_config.txt')
    
    DAYS = 1  # 获取最近几天的推文
    
    print("🐦 Twitter推文爬虫启动")
    print("="*50)
    print("📊 速率限制配置 (基于官方API文档)")
    print(f"  🏷️  API等级: {API_TIER.upper()}")
    print(f"  🛡️  安全系数: {SAFETY_FACTOR:.1%}")
    print(f"  ⚙️  智能限流: 启用")
    
    # 显示向后兼容性信息
    if os.getenv('TWITTER_RATE_DELAY'):
        print(f"\n⚠️  检测到旧配置 TWITTER_RATE_DELAY={RATE_LIMIT_DELAY}s")
        print(f"   新版本使用智能限流，建议移除此配置")
    
    print(f"\n🔧 环境变量说明:")
    print(f"   TWITTER_API_TIER={API_TIER} (free/basic/pro/enterprise)")
    print(f"   TWITTER_SAFETY_FACTOR={SAFETY_FACTOR} (0.1-1.0, 推荐0.8)")
    
    # WordPress配置检查
    wordpress_config = None
    if PUBLISH_TO_WORDPRESS:
        if WORDPRESS_SITE_URL and WORDPRESS_USERNAME and WORDPRESS_PASSWORD:
            wordpress_config = {
                'site_url': WORDPRESS_SITE_URL,
                'username': WORDPRESS_USERNAME,
                'password': WORDPRESS_PASSWORD
            }
            print(f"\n📝 WordPress发布已启用")
            print(f"  🌐 站点: {WORDPRESS_SITE_URL}")
            print(f"  👤 用户: {WORDPRESS_USERNAME}")
            print(f"  📝 状态: {WORDPRESS_POST_STATUS}")
            print(f"  📁 分类: {WORDPRESS_CATEGORY}")
        else:
            print("\n⚠️ WordPress配置不完整，将跳过WordPress发布")
            print("💡 需要设置: WORDPRESS_SITE_URL, WORDPRESS_USERNAME, WORDPRESS_PASSWORD")
            PUBLISH_TO_WORDPRESS = False
    else:
        print("\n📝 WordPress发布已禁用")
    
    if not BEARER_TOKEN:
        print("\n" + "="*50)
        print("❌ 错误: 请设置环境变量 TWITTER_BEARER_TOKEN")
        print("或者直接在代码中设置 BEARER_TOKEN 变量")
        print("\n🔑 获取Twitter API密钥的步骤:")
        print("1. 访问 https://developer.twitter.com/")
        print("2. 创建开发者账号")
        print("3. 创建新应用")
        print("4. 获取Bearer Token")
        print("\n📊 速率限制配置说明 (新版本):")
        print("环境变量配置:")
        print("  export TWITTER_API_TIER=free        # API等级 (free/basic/pro)")
        print("  export TWITTER_SAFETY_FACTOR=0.8    # 安全系数 (0.1-1.0)")
        print("\n🎯 不同API等级的限制:")
        print("  FREE: 1请求/15分钟 (用户推文), 1请求/24小时 (用户信息)")
        print("  BASIC: 10请求/15分钟 (用户推文), 500请求/24小时 (用户信息)")
        print("  PRO: 1500请求/15分钟 (用户推文), 300请求/15分钟 (用户信息)")
        print("\n💡 推荐配置:")
        print("  - FREE等级: SAFETY_FACTOR=0.8 (更稳定)")
        print("  - BASIC/PRO等级: SAFETY_FACTOR=0.9 (更高效)")
        print("\n📝 WordPress配置说明 (可选):")
        print("  export PUBLISH_TO_WORDPRESS=true")
        print("  export WORDPRESS_SITE_URL=https://yoursite.com")
        print("  export WORDPRESS_USERNAME=your_username")
        print("  export WORDPRESS_PASSWORD=your_password")
        print("  export WORDPRESS_POST_STATUS=draft")
        print("  export WORDPRESS_CATEGORY=Twitter推文")
        print("\n👥 用户配置说明:")
        print("请编辑 config/users_config.txt 文件来修改要爬取的用户名列表")
        print("每行一个用户名，以#开头的行为注释")
        return
    
    if not USERNAMES:
        print("❌ 错误: 未找到任何可用的用户名")
        print("请检查 config/users_config.txt 文件并添加用户名")
        return
    
    # 创建爬虫实例
    scraper = TwitterScraper(
        BEARER_TOKEN, 
        api_tier=API_TIER,
        safety_factor=SAFETY_FACTOR,
        wordpress_config=wordpress_config
    )
    
    # 显示目标信息
    print(f"\n🎯 爬取任务配置:")
    print(f"  👥 目标用户: {', '.join(['@' + u for u in USERNAMES]) if isinstance(USERNAMES, list) else '@' + USERNAMES}")
    print(f"  🕰️ 时间范围: 最近 {DAYS} 天")
    print(f"  📊 用户数量: {len(USERNAMES) if isinstance(USERNAMES, list) else 1}")
    
    # 爬取推文
    all_tweets = scraper.get_tweets(USERNAMES, DAYS)
    
    if any(tweets for tweets in all_tweets.values()):
        # 显示统计摘要
        scraper.print_summary(all_tweets)
        
        # 显示速率限制状态
        scraper.rate_manager.print_status_summary()
        
        # 保存推文数据
        scraper.save_tweets(all_tweets)
        
        # WordPress发布（如果启用）
        if PUBLISH_TO_WORDPRESS and scraper.wp_publisher:
            wp_results = scraper.publish_to_wordpress(
                all_tweets,
                post_status=WORDPRESS_POST_STATUS,
                category_name=WORDPRESS_CATEGORY
            )
            
            if wp_results:
                # 保存WordPress发布结果
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                wp_results_file = f"wordpress_publish_results_{timestamp}.json"
                with open(wp_results_file, 'w', encoding='utf-8') as f:
                    json.dump(wp_results, f, ensure_ascii=False, indent=2)
                print(f"💾 WordPress发布结果已保存到: {wp_results_file}")
        
        # 显示最新推文预览（多用户模式）
        if isinstance(USERNAMES, list) and len(USERNAMES) > 1:
            print("\n" + "="*50)
            print("=== 各用户最新推文预览 ===")
            print("="*50)
            
            for username, tweets in all_tweets.items():
                if tweets:
                    print(f"\n🐦 @{username} 的最新推文:")
                    for i, tweet in enumerate(tweets[:2], 1):  # 显示每个用户最新2条
                        print(f"  [{i}] {tweet['created_at']}")
                        print(f"      {tweet['text'][:80]}...")
                        print(f"      👍 {tweet['like_count']} | 🔄 {tweet['retweet_count']} | 💬 {tweet['reply_count']}")
                        print(f"      🔗 {tweet['url']}")
                else:
                    print(f"\n❌ @{username}: 未获取到推文数据")
        elif isinstance(USERNAMES, str) or len(USERNAMES) == 1:
            # 单用户模式预览
            username = USERNAMES if isinstance(USERNAMES, str) else USERNAMES[0]
            tweets = all_tweets.get(username, [])
            if tweets:
                print("\n=== 最新推文预览 ===")
                for i, tweet in enumerate(tweets[:3]):
                    print(f"\n推文 {i+1}:")
                    print(f"时间: {tweet['created_at']}")
                    print(f"内容: {tweet['text'][:100]}...")
                    print(f"点赞: {tweet['like_count']} | 转发: {tweet['retweet_count']} | 回复: {tweet['reply_count']}")
                    print(f"链接: {tweet['url']}")
    else:
        print("\n❌ 没有获取到推文数据")
        print("\n💡 可能的原因:")
        print("  1. API速率限制过严格 - 尝试降低 SAFETY_FACTOR")
        print("  2. 用户没有最近的推文")
        print("  3. API认证问题")
        print("  4. 网络连接问题")
        
        # 显示当前配置建议
        scraper.rate_manager.print_status_summary()

if __name__ == "__main__":
    main()