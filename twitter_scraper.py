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
    def __init__(self, bearer_token: str, rate_limit_delay: float = 1.0, 
                 wordpress_config: Optional[Dict] = None):
        """
        初始化Twitter爬虫
        
        Args:
            bearer_token: Twitter API v2的Bearer Token
            rate_limit_delay: API请求间隔时间（秒），默认1秒
            wordpress_config: WordPress配置字典 {'site_url': str, 'username': str, 'password': str}
        """
        self.client = tweepy.Client(bearer_token=bearer_token)
        self.rate_limit_delay = rate_limit_delay
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
        
    def _wait_for_rate_limit(self):
        """
        确保请求间隔符合频次限制
        """
        with self._request_lock:
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            
            if time_since_last_request < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last_request
                print(f"⏳ 频次限制：等待 {sleep_time:.2f} 秒...")
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
    
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
            print(f"⚙️  当前频次限制设置: 每 {self.rate_limit_delay} 秒一次请求")
            
            tweets = self._get_single_user_tweets(username, days)
            all_tweets[username] = tweets
            
            # 处理完一个用户后的额外延迟（避免连续请求）
            if i < total_users:
                extra_delay = max(0.5, self.rate_limit_delay * 0.5)  # 额外延迟，至少0.5秒
                print(f"⏱️  用户间延迟: {extra_delay}秒")
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
            # 频次限制控制
            self._wait_for_rate_limit()
            
            # 获取用户信息
            print(f"🔍 正在查询用户 @{username} 的信息...")
            user_response = self.client.get_user(username=username)
            if not user_response or not hasattr(user_response, 'data') or not user_response.data:  # type: ignore
                print(f"用户 @{username} 不存在")
                return []
            
            user = user_response.data  # type: ignore
            user_id = user.id
            print(f"找到用户: {user.name} (@{username})")
            
            # 计算时间范围（使用一天的开始和结束时间）
            end_time = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
            start_time = (end_time - timedelta(days=days-1)).replace(hour=0, minute=0, second=0, microsecond=0)
            
            print(f"正在获取 {start_time.strftime('%Y-%m-%d %H:%M')} 到 {end_time.strftime('%Y-%m-%d %H:%M')} 的推文...")
            
            # 频次限制控制（获取推文前再次检查）
            self._wait_for_rate_limit()
            
            # 获取推文
            print(f"📡 正在请求 @{username} 的推文数据...")
            tweets = tweepy.Paginator(
                self.client.get_users_tweets,
                id=user_id,
                start_time=start_time,
                end_time=end_time,
                tweet_fields=['created_at', 'public_metrics', 'context_annotations', 'lang', 'reply_settings'],
                user_fields=['name', 'username', 'verified', 'public_metrics'],
                expansions=['author_id'],
                max_results=100
            ).flatten(limit=1000)
            
            tweet_list = []
            for tweet in tweets:
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
            
            print(f"✅ 成功获取 {len(tweet_list)} 条推文")
            return tweet_list
            
        except tweepy.TooManyRequests as e:
            print(f"⚠️  API请求频率限制 - {str(e)}")
            print(f"💡 建议增加延迟时间或稍后再试")
            print(f"🔄 当前延迟设置: {self.rate_limit_delay}秒")
            return []
        except tweepy.Unauthorized as e:
            print(f"🔐 API认证失败 - {str(e)}")
            print("💡 请检查Bearer Token是否正确")
            return []
        except Exception as e:
            print(f"❌ 获取推文时发生错误: {str(e)}")
            print(f"🔄 当前延迟设置: {self.rate_limit_delay}秒")
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

def load_users_from_config(config_file: str = 'users_config.txt') -> List[str]:
    """
    从配置文件中加载用户名列表
    
    Args:
        config_file: 配置文件路径，默认为'users_config.txt'
        
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
    RATE_LIMIT_DELAY = float(os.getenv('TWITTER_RATE_DELAY', '1.0'))  # 频次限制延迟（秒）
    
    # WordPress配置（可选）
    WORDPRESS_SITE_URL = os.getenv('WORDPRESS_SITE_URL')  # WordPress站点URL
    WORDPRESS_USERNAME = os.getenv('WORDPRESS_USERNAME')  # WordPress用户名
    WORDPRESS_PASSWORD = os.getenv('WORDPRESS_PASSWORD')  # WordPress密码或应用密码
    
    # WordPress发布设置
    PUBLISH_TO_WORDPRESS = os.getenv('PUBLISH_TO_WORDPRESS', 'false').lower() == 'true'
    WORDPRESS_POST_STATUS = os.getenv('WORDPRESS_POST_STATUS', 'draft')  # draft, publish, private
    WORDPRESS_CATEGORY = os.getenv('WORDPRESS_CATEGORY', 'Twitter推文')  # WordPress分类
    
    # 从配置文件加载用户名
    USERNAMES = load_users_from_config('users_config.txt')
    
    DAYS = 1  # 获取最近几天的推文
    
    print("🐦 Twitter推文爬虫启动")
    print(f"⚙️  频次限制设置: 每 {RATE_LIMIT_DELAY} 秒一次请求")
    print(f"📊 环境变量 TWITTER_RATE_DELAY 可调整延迟时间（当前: {RATE_LIMIT_DELAY}s）")
    
    # WordPress配置检查
    wordpress_config = None
    if PUBLISH_TO_WORDPRESS:
        if WORDPRESS_SITE_URL and WORDPRESS_USERNAME and WORDPRESS_PASSWORD:
            wordpress_config = {
                'site_url': WORDPRESS_SITE_URL,
                'username': WORDPRESS_USERNAME,
                'password': WORDPRESS_PASSWORD
            }
            print(f"📝 WordPress发布已启用")
            print(f"  🌐 站点: {WORDPRESS_SITE_URL}")
            print(f"  👤 用户: {WORDPRESS_USERNAME}")
            print(f"  📝 状态: {WORDPRESS_POST_STATUS}")
            print(f"  📁 分类: {WORDPRESS_CATEGORY}")
        else:
            print("⚠️ WordPress配置不完整，将跳过WordPress发布")
            print("💡 需要设置: WORDPRESS_SITE_URL, WORDPRESS_USERNAME, WORDPRESS_PASSWORD")
            PUBLISH_TO_WORDPRESS = False
    else:
        print("📝 WordPress发布已禁用")
    
    if not BEARER_TOKEN:
        print("错误: 请设置环境变量 TWITTER_BEARER_TOKEN")
        print("或者直接在代码中设置 BEARER_TOKEN 变量")
        print("\n获取Twitter API密钥的步骤:")
        print("1. 访问 https://developer.twitter.com/")
        print("2. 创建开发者账号")
        print("3. 创建新应用")
        print("4. 获取Bearer Token")
        print("\n频次限制配置说明:")
        print("- 设置环境变量TWITTER_RATE_DELAY来调整请求间隔")
        print("- 默认值: 1.0秒 (推荐值，平衡速度和稳定性)")
        print("- 最小值: 0.5秒 (更快但可能被限制)")
        print("- 建议值: 1.5-2.0秒 (更稳定，适合大量用户)")
        print("\nWordPress配置说明 (可选):")
        print("- PUBLISH_TO_WORDPRESS=true  # 启用WordPress发布")
        print("- WORDPRESS_SITE_URL=https://yoursite.com  # WordPress站点URL")
        print("- WORDPRESS_USERNAME=your_username  # WordPress用户名")
        print("- WORDPRESS_PASSWORD=your_password  # WordPress密码")
        print("- WORDPRESS_POST_STATUS=draft  # 文章状态(draft/publish/private)")
        print("- WORDPRESS_CATEGORY=Twitter推文  # WordPress分类")
        print("\n用户配置说明:")
        print("请编辑 users_config.txt 文件来修改要爬取的用户名列表")
        print("每行一个用户名，以#开头的行为注释")
        return
    
    if not USERNAMES:
        print("错误: 未找到任何可用的用户名")
        print("请检查 users_config.txt 文件并添加用户名")
        return
    
    # 创建爬虫实例
    scraper = TwitterScraper(
        BEARER_TOKEN, 
        rate_limit_delay=RATE_LIMIT_DELAY,
        wordpress_config=wordpress_config
    )
    
    # 爬取推文
    print(f"🎯 目标用户: {', '.join(['@' + u for u in USERNAMES]) if isinstance(USERNAMES, list) else '@' + USERNAMES}")
    print(f"🕰️ 时间范围: 最近 {DAYS} 天")
    
    all_tweets = scraper.get_tweets(USERNAMES, DAYS)
    
    if any(tweets for tweets in all_tweets.values()):
        # 显示统计摘要
        scraper.print_summary(all_tweets)
        
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
        print("没有获取到推文数据")

if __name__ == "__main__":
    main()