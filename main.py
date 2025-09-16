#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter Scraper 主入口脚本
"""

import os
import sys

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# 导入并运行主函数
from src.twitter_scraper import main

if __name__ == '__main__':
    main()