#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter推文爬取脚本
自动爬取指定用户最近一天的推文信息
"""

import tweepy
import pandas as pd
import json
from datetime import datetime, timedelta
import os
import time
from typing import List, Dict, Optional

class TwitterScraper:
    def __init__(self, bearer_token: str):
        """
        初始化Twitter爬虫
        
        Args:
            bearer_token: Twitter API v2的Bearer Token
        """
        self.client = tweepy.Client(bearer_token=bearer_token)
        
    def get_user_tweets(self, username: str, days: int = 1) -> List[Dict]:
        """
        获取指定用户最近指定天数的推文
        
        Args:
            username: Twitter用户名（不包含@符号）
            days: 获取最近几天的推文，默认1天
            
        Returns:
            推文列表，每个推文包含详细信息
        """
        try:
            # 获取用户信息
            user_response = self.client.get_user(username=username)
            if not user_response or not hasattr(user_response, 'data') or not user_response.data:  # type: ignore
                print(f"用户 @{username} 不存在")
                return []
            
            user = user_response.data  # type: ignore
            user_id = user.id
            print(f"找到用户: {user.name} (@{username})")
            
            # 计算时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            print(f"正在获取 {start_time.strftime('%Y-%m-%d %H:%M')} 到 {end_time.strftime('%Y-%m-%d %H:%M')} 的推文...")
            
            # 获取推文
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
            
            print(f"成功获取 {len(tweet_list)} 条推文")
            return tweet_list
            
        except tweepy.TooManyRequests:
            print("API请求频率限制，请稍后再试")
            return []
        except tweepy.Unauthorized:
            print("API认证失败，请检查Bearer Token")
            return []
        except Exception as e:
            print(f"获取推文时发生错误: {str(e)}")
            return []
    
    def save_tweets_to_csv(self, tweets: List[Dict], filename: Optional[str] = None):
        """
        将推文保存为CSV文件
        
        Args:
            tweets: 推文列表
            filename: 文件名，如果不提供则自动生成
        """
        if not tweets:
            print("没有推文数据可保存")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tweets_{timestamp}.csv"
        
        df = pd.DataFrame(tweets)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"推文已保存到: {filename}")
    
    def save_tweets_to_json(self, tweets: List[Dict], filename: Optional[str] = None):
        """
        将推文保存为JSON文件
        
        Args:
            tweets: 推文列表
            filename: 文件名，如果不提供则自动生成
        """
        if not tweets:
            print("没有推文数据可保存")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tweets_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(tweets, f, ensure_ascii=False, indent=2)
        print(f"推文已保存到: {filename}")
    
    def get_multiple_users_tweets(self, usernames: List[str], days: int = 1) -> Dict[str, List[Dict]]:
        """
        获取多个用户的推文
        
        Args:
            usernames: 用户名列表
            days: 获取最近几天的推文，默认1天
            
        Returns:
            字典，键为用户名，值为该用户的推文列表
        """
        all_tweets = {}
        total_users = len(usernames)
        
        print(f"开始获取 {total_users} 个用户的推文...\n")
        
        for i, username in enumerate(usernames, 1):
            print(f"[{i}/{total_users}] 正在处理用户: @{username}")
            tweets = self.get_user_tweets(username, days)
            all_tweets[username] = tweets
            
            # 添加延迟以避免API限制
            if i < total_users:
                time.sleep(1)
        
        return all_tweets
    
    def save_multiple_users_tweets(self, all_tweets: Dict[str, List[Dict]], format_type: str = 'both'):
        """
        保存多个用户的推文数据
        
        Args:
            all_tweets: 多用户推文数据字典
            format_type: 保存格式 ('csv', 'json', 'both')
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 合并所有推文并添加用户信息
        combined_tweets = []
        for username, tweets in all_tweets.items():
            for tweet in tweets:
                tweet_with_user = tweet.copy()
                tweet_with_user['username'] = username
                combined_tweets.append(tweet_with_user)
        
        if not combined_tweets:
            print("没有推文数据可保存")
            return
        
        # 按时间排序
        combined_tweets.sort(key=lambda x: x['created_at'], reverse=True)
        
        if format_type in ['csv', 'both']:
            filename = f"tweets_multiple_users_{timestamp}.csv"
            df = pd.DataFrame(combined_tweets)
            # 调整列顺序，将username放在前面
            cols = ['username'] + [col for col in df.columns if col != 'username']
            df = df[cols]
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"合并推文已保存到: {filename}")
        
        if format_type in ['json', 'both']:
            filename = f"tweets_multiple_users_{timestamp}.json"
            output_data = {
                'timestamp': timestamp,
                'total_users': len(all_tweets),
                'total_tweets': len(combined_tweets),
                'users_data': all_tweets,
                'combined_tweets': combined_tweets
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"详细数据已保存到: {filename}")
        
        # 为每个用户单独保存文件
        for username, tweets in all_tweets.items():
            if tweets:
                if format_type in ['csv', 'both']:
                    user_filename = f"tweets_{username}_{timestamp}.csv"
                    df = pd.DataFrame(tweets)
                    df.to_csv(user_filename, index=False, encoding='utf-8-sig')
                
                if format_type in ['json', 'both']:
                    user_filename = f"tweets_{username}_{timestamp}.json"
                    with open(user_filename, 'w', encoding='utf-8') as f:
                        json.dump(tweets, f, ensure_ascii=False, indent=2)
        
        print(f"单独用户文件也已保存")
    
    def print_tweets_summary(self, tweets: List[Dict]):
        """
        打印推文摘要信息
        
        Args:
            tweets: 推文列表
        """
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
    
    def print_multiple_users_summary(self, all_tweets: Dict[str, List[Dict]]):
        """
        打印多用户推文统计摘要
        
        Args:
            all_tweets: 多用户推文数据字典
        """
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
    主函数 - 使用示例
    """
    # 配置参数
    BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')  # 从环境变量获取
    
    # 从配置文件加载用户名
    USERNAMES = load_users_from_config('users_config.txt')
    
    # 也可以指定其他配置文件
    # USERNAMES = load_users_from_config('custom_users.txt')
    
    DAYS = 1  # 获取最近几天的推文
    USE_MULTIPLE_USERS = True  # 设置为True使用多用户模式，False使用单用户模式
    
    if not BEARER_TOKEN:
        print("错误: 请设置环境变量 TWITTER_BEARER_TOKEN")
        print("或者直接在代码中设置 BEARER_TOKEN 变量")
        print("\n获取Twitter API密钥的步骤:")
        print("1. 访问 https://developer.twitter.com/")
        print("2. 创建开发者账号")
        print("3. 创建新应用")
        print("4. 获取Bearer Token")
        print("\n用户配置说明:")
        print("请编辑 users_config.txt 文件来修改要爬取的用户名列表")
        print("每行一个用户名，以#开头的行为注释")
        return
    
    if not USERNAMES:
        print("错误: 未找到任何可用的用户名")
        print("请检查 users_config.txt 文件并添加用户名")
        return
    
    # 创建爬虫实例
    scraper = TwitterScraper(BEARER_TOKEN)
    
    if USE_MULTIPLE_USERS:
        # 多用户模式
        print(f"开始爬取 {len(USERNAMES)} 个用户最近 {DAYS} 天的推文...")
        print(f"用户列表: {', '.join(['@' + u for u in USERNAMES])}\n")
        
        all_tweets = scraper.get_multiple_users_tweets(USERNAMES, DAYS)
        
        if any(tweets for tweets in all_tweets.values()):
            # 显示多用户推文摘要
            scraper.print_multiple_users_summary(all_tweets)
            
            # 保存推文（包含合并文件和单独文件）
            scraper.save_multiple_users_tweets(all_tweets, format_type='both')
            
            # 显示各用户最新推文预览
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
        else:
            print("没有获取到任何推文数据")
    
    else:
        # 单用户模式（保持原有功能）
        USERNAME = USERNAMES[0]  # 使用列表中第一个用户
        
        print(f"开始爬取 @{USERNAME} 最近 {DAYS} 天的推文...")
        tweets = scraper.get_user_tweets(USERNAME, DAYS)
        
        if tweets:
            # 显示推文摘要
            scraper.print_tweets_summary(tweets)
            
            # 保存推文
            scraper.save_tweets_to_csv(tweets)
            scraper.save_tweets_to_json(tweets)
            
            # 显示前几条推文
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