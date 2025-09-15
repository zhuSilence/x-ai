#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WordPress发布器
用于将推文内容自动发布到WordPress站点
"""

import requests
import json
import time
import base64
from urllib.parse import urljoin
from typing import Dict, List, Optional


class WordPressPublisher:
    def __init__(self, site_url: str, username: str, password: str):
        """
        初始化WordPress发布器
        
        Args:
            site_url: WordPress站点URL (例如: https://example.com)
            username: WordPress用户名或应用密码的用户名
            password: WordPress密码或应用密码
        """
        self.site_url = site_url.rstrip('/')
        self.api_url = urljoin(self.site_url + '/', 'wp-json/wp/v2/')
        self.username = username
        self.password = password
        
        # 创建认证头
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json',
            'User-Agent': 'Twitter-WordPress-Publisher/1.0'
        }
    
    def test_connection(self) -> bool:
        """
        测试WordPress API连接
        
        Returns:
            连接是否成功
        """
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
                print(f"错误信息: {response.text}")
                return False
        except Exception as e:
            print(f"❌ WordPress连接测试失败: {str(e)}")
            return False
    
    def create_post(self, title: str, content: str, status: str = 'draft', 
                   category_ids: List[int] = None, tag_ids: List[int] = None) -> Optional[Dict]:
        """
        创建WordPress文章
        
        Args:
            title: 文章标题
            content: 文章内容(HTML格式)
            status: 文章状态 ('draft', 'publish', 'private')
            category_ids: 分类ID列表
            tag_ids: 标签ID列表
            
        Returns:
            创建的文章信息或None
        """
        post_data = {
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
            
            if response.status_code == 201:  # Created
                post_info = response.json()
                print(f"✅ 文章创建成功: {post_info['title']['rendered']}")
                print(f"📝 文章ID: {post_info['id']}")
                print(f"🔗 文章链接: {post_info['link']}")
                return post_info
            else:
                print(f"❌ 文章创建失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 创建文章时发生错误: {str(e)}")
            return None
    
    def get_categories(self) -> List[Dict]:
        """
        获取WordPress分类列表
        
        Returns:
            分类列表
        """
        try:
            response = requests.get(
                urljoin(self.api_url, 'categories'),
                headers=self.headers,
                params={'per_page': 100},
                timeout=10
            )
            
            if response.status_code == 200:
                categories = response.json()
                print(f"📁 获取到 {len(categories)} 个分类")
                return categories
            else:
                print(f"❌ 获取分类失败，状态码: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ 获取分类时发生错误: {str(e)}")
            return []
    
    def create_category(self, name: str, description: str = '') -> Optional[Dict]:
        """
        创建WordPress分类
        
        Args:
            name: 分类名称
            description: 分类描述
            
        Returns:
            创建的分类信息或None
        """
        category_data = {
            'name': name,
            'description': description
        }
        
        try:
            response = requests.post(
                urljoin(self.api_url, 'categories'),
                headers=self.headers,
                json=category_data,
                timeout=10
            )
            
            if response.status_code == 201:
                category_info = response.json()
                print(f"✅ 分类创建成功: {category_info['name']} (ID: {category_info['id']})")
                return category_info
            else:
                print(f"❌ 分类创建失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 创建分类时发生错误: {str(e)}")
            return None
    
    def format_tweet_as_html(self, tweet: Dict, username: str) -> str:
        """
        将推文格式化为HTML内容
        
        Args:
            tweet: 推文数据
            username: Twitter用户名
            
        Returns:
            格式化的HTML内容
        """
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
        """
        将推文数据发布为WordPress文章
        
        Args:
            tweets_data: 推文数据字典 {username: [tweets]}
            post_status: 文章发布状态
            category_name: 分类名称
            
        Returns:
            发布结果列表
        """
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
                if len(tweet['text']) > 50:
                    title += f" - {tweet['text'][:50]}..."
                else:
                    title += f" - {tweet['text']}"
                
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
    
    def publish_single_tweet(self, tweet: Dict, username: str, 
                           post_status: str = 'draft',
                           category_name: str = 'Twitter推文') -> Optional[Dict]:
        """
        发布单条推文
        
        Args:
            tweet: 推文数据
            username: Twitter用户名
            post_status: 文章发布状态
            category_name: 分类名称
            
        Returns:
            发布结果或None
        """
        tweets_data = {username: [tweet]}
        results = self.publish_tweets_as_posts(tweets_data, post_status, category_name)
        return results[0] if results else None
    
    def get_site_info(self) -> Optional[Dict]:
        """
        获取WordPress站点信息
        
        Returns:
            站点信息或None
        """
        try:
            response = requests.get(
                self.site_url + '/wp-json/',
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"❌ 获取站点信息失败: {str(e)}")
            return None
    
    def delete_post(self, post_id: int) -> bool:
        """
        删除WordPress文章
        
        Args:
            post_id: 文章ID
            
        Returns:
            删除是否成功
        """
        try:
            response = requests.delete(
                urljoin(self.api_url, f'posts/{post_id}'),
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ 文章删除成功: ID {post_id}")
                return True
            else:
                print(f"❌ 文章删除失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 删除文章时发生错误: {str(e)}")
            return False