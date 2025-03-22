# Reddit关键词采集工具

## 简介
这是一个基于Python的Reddit关键词采集工具，可以帮助用户搜索特定Subreddit并采集相关帖子数据。

## 功能特点
- Reddit API认证配置
- Subreddit搜索与选择
- 帖子关键词搜索
- 自定义采集数量和排序方式
- 数据表格展示
- CSV导出功能
- 操作日志记录

## 安装步骤
1. 确保已安装Python 3.6或更高版本
2. 运行安装脚本安装依赖：
   ```
   python install_dependencies.py
   ```
3. 启动程序：
   ```
   python reddit_spier.py
   ```

## 使用前准备
使用本工具前，您需要获取Reddit API密钥：
1. 访问 https://www.reddit.com/prefs/apps
2. 点击"create app"或"create another app"
3. 填写应用名称，选择"script"类型
4. 重定向URI可填写 http://localhost:8080
5. 创建后，您将获得Client ID和Client Secret

## 使用说明
1. 启动程序后，首先在"Reddit API配置"区域填写您的API密钥信息
2. 点击"连接Reddit"按钮测试连接
3. 在"Subreddit搜索"区域输入关键词搜索相关Subreddit
4. 从结果列表中选择一个或多个Subreddit
5. 在"帖子采集参数"区域设置关键词、数量和排序方式
6. 点击"开始采集"按钮开始数据采集
7. 采集完成后，可以查看数据表格中的结果
8. 点击"导出CSV"按钮将数据保存为CSV文件

## 注意事项
- Reddit API有速率限制，短时间内大量请求可能导致暂时封禁
- 请遵守Reddit的API使用条款
- 本工具仅用于学习和研究目的，请勿用于违反法律法规的活动 