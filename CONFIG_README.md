# Twitter爬虫用户配置说明

## 配置文件说明

`users_config.txt` 文件用于配置需要爬取的Twitter用户名列表。

### 文件格式

- 每行一个用户名，不需要包含 `@` 符号
- 以 `#` 开头的行为注释，会被忽略
- 空行会被自动忽略
- 支持中文注释

### 示例配置

```
# Twitter用户名配置文件
# 每行一个用户名，不需要@符号
# 以#开头的行为注释，会被忽略

elonmusk
sundarpichai
tim_cook
satyanadella

# 可以继续添加更多用户名
# jack
# billgates
```

### 使用方法

1. 编辑 `users_config.txt` 文件
2. 添加或删除需要爬取的用户名
3. 保存文件
4. 运行脚本：`python twitter_scraper.py`

### 注意事项

- 用户名不区分大小写
- 如果用户名格式不正确，程序会显示警告
- 如果配置文件不存在，程序会使用默认用户列表
- 程序会自动去除用户名前的 `@` 符号（如果存在）

### 自定义配置文件

你也可以使用自定义的配置文件名，修改代码中的这一行：

```python
USERNAMES = load_users_from_config('your_custom_config.txt')
```

这样就可以避免每次修改代码来更换要爬取的用户了！