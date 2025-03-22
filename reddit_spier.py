import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import praw
import pandas as pd
import datetime
import time
import webbrowser  # 用于打开URL
import re  # 用于关键词匹配
import json  # 用于保存和加载API配置
import os  # 用于文件路径操作
import sys  # 用于获取可执行文件路径

class RedditSpierApp:
    """
    Reddit关键词采集工具主应用类
    """
    def __init__(self, root):
        """
        初始化应用
        
        @param {tk.Tk} root - Tkinter根窗口
        """
        self.root = root
        self.root.title("Reddit关键词采集工具|九先生779059811")
        self.root.geometry("870x750")  # 增加窗口高度
        
        # 配置文件路径 - 修改为使用可执行文件所在目录
        try:
            # 尝试获取PyInstaller打包后的路径
            base_path = sys._MEIPASS
        except Exception:
            # 如果不是通过PyInstaller运行，使用脚本所在目录
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.config_file = os.path.join(base_path, "reddit_config.json")
        
        # 如果是打包后的环境，使用当前工作目录
        if getattr(sys, 'frozen', False):
            self.config_file = os.path.join(os.getcwd(), "reddit_config.json")
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建主框架，使用网格布局
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建API认证框架
        self.create_auth_frame(main_frame)
        
        # 创建Subreddit搜索框架
        self.create_subreddit_search_frame(main_frame)
        
        # 创建帖子采集参数框架
        self.create_post_params_frame(main_frame)
        
        # 创建数据表格框架
        self.create_data_table_frame(main_frame)
        
        # 创建操作按钮框架
        self.create_action_buttons_frame(main_frame)
        
        # 创建日志框架
        self.create_log_frame(main_frame)
        
        # 初始化Reddit API客户端
        self.reddit = None
        
        # 采集线程
        self.scraping_thread = None
        self.stop_scraping = False
        
        # 加载保存的API配置
        self.load_api_config()

    def create_auth_frame(self, parent):
        """
        创建API认证框架
        
        @param {ttk.Frame} parent - 父框架
        """
        auth_frame = ttk.LabelFrame(parent, text="Reddit API配置")
        auth_frame.pack(fill="x", padx=5, pady=5)
        
        # 使用网格布局，更好地控制组件位置
        auth_grid = ttk.Frame(auth_frame)
        auth_grid.pack(fill="x", padx=5, pady=5)
        
        # Client ID
        ttk.Label(auth_grid, text="Client ID:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.client_id_var = tk.StringVar()
        ttk.Entry(auth_grid, textvariable=self.client_id_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        # Client Secret
        ttk.Label(auth_grid, text="Client Secret:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.client_secret_var = tk.StringVar()
        ttk.Entry(auth_grid, textvariable=self.client_secret_var, width=40, show="*").grid(row=1, column=1, padx=5, pady=5)
        
        # User Agent
        ttk.Label(auth_grid, text="User Agent:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.user_agent_var = tk.StringVar(value="RedditSpier v1.0")
        ttk.Entry(auth_grid, textvariable=self.user_agent_var, width=40).grid(row=2, column=1, padx=5, pady=5)
        
        # 连接按钮
        ttk.Button(auth_grid, text="连接Reddit", command=self.connect_reddit).grid(row=2, column=2, padx=5, pady=5)
        
        # 保存配置按钮
        ttk.Button(auth_grid, text="保存配置", command=self.save_api_config).grid(row=2, column=3, padx=5, pady=5)

    def create_subreddit_search_frame(self, parent):
        """
        创建Subreddit搜索框架 - 使用普通Frame并保留标题
        
        @param {ttk.Frame} parent - 父框架
        """
        # 使用普通Frame代替LabelFrame
        subreddit_frame = ttk.Frame(parent)
        subreddit_frame.pack(fill="x", padx=5, pady=2)  # 减小pady值
        
        # 添加标题标签
        ttk.Label(subreddit_frame, text="Subreddit搜索", font=("", 10, "bold")).pack(anchor="w", padx=5, pady=2)
        
        # 创建左右分栏布局
        search_pane = ttk.Frame(subreddit_frame)
        search_pane.pack(fill="x", padx=5, pady=2)  # 减小pady值
        search_pane.columnconfigure(0, weight=2)  # 左侧搜索区域
        search_pane.columnconfigure(1, weight=3)  # 右侧已选区域 - 增加权重比例
        
        # 左侧搜索区域
        left_frame = ttk.Frame(search_pane)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        
        # 搜索关键词
        ttk.Label(left_frame, text="关键词:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.subreddit_keyword_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.subreddit_keyword_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(left_frame, text="搜索", command=self.search_subreddits).grid(row=0, column=2, padx=5, pady=5)
        
        # 结果列表
        ttk.Label(left_frame, text="结果列表:").grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        self.subreddit_listbox = tk.Listbox(left_frame, width=45, height=5, selectmode=tk.MULTIPLE)
        self.subreddit_listbox.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.subreddit_listbox.yview)
        scrollbar.grid(row=1, column=3, sticky="ns")
        self.subreddit_listbox.config(yscrollcommand=scrollbar.set)
        
        # 创建搜索结果右键菜单 - 添加更多选项
        self.search_result_menu = tk.Menu(self.root, tearoff=0)
        self.search_result_menu.add_command(label="添加到已选择", command=self.add_selected_subreddits)
        self.search_result_menu.add_command(label="全选", command=self.select_all_subreddits)
        self.search_result_menu.add_command(label="取消全选", command=self.deselect_all_subreddits)
        
        # 绑定右键菜单
        self.subreddit_listbox.bind("<Button-3>", self.show_search_result_menu)
        
        # 右侧已选择区域 - 使用普通Frame并添加标题标签
        right_frame = ttk.Frame(search_pane)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        # 添加标题标签
        ttk.Label(right_frame, text="已选择社区", font=("", 9, "bold")).pack(anchor="w", padx=5, pady=2)
        
        # 已选择列表
        self.selected_subreddits_var = tk.StringVar()
        self.selected_subreddits_list = tk.Listbox(right_frame, width=50, height=5, listvariable=self.selected_subreddits_var)
        self.selected_subreddits_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 添加滚动条
        selected_scrollbar = ttk.Scrollbar(self.selected_subreddits_list, orient="vertical", command=self.selected_subreddits_list.yview)
        selected_scrollbar.pack(side="right", fill="y")
        self.selected_subreddits_list.config(yscrollcommand=selected_scrollbar.set)
        
        # 创建已选择列表右键菜单 - 修改选项
        self.selected_subreddit_menu = tk.Menu(self.root, tearoff=0)
        self.selected_subreddit_menu.add_command(label="移除", command=self.remove_selected_subreddit)
        self.selected_subreddit_menu.add_command(label="全部移除", command=self.remove_all_subreddits)
        
        # 绑定右键菜单
        self.selected_subreddits_list.bind("<Button-3>", self.show_selected_subreddit_menu)
        
        # 初始化已选择列表
        self.selected_subreddits = []

    def create_post_params_frame(self, parent):
        """
        创建帖子采集参数框架 - 修改为一行显示并调整间距
        
        @param {ttk.Frame} parent - 父框架
        """
        # 创建无标题的框架
        params_frame = ttk.Frame(parent)
        params_frame.pack(fill="x", padx=5, pady=2)  # 减小pady值
        
        # 所有元素放在一行
        # 关键词
        ttk.Label(params_frame, text="关键词:").pack(side="left", padx=5, pady=2)  # 减小pady值
        self.post_keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(params_frame, textvariable=self.post_keyword_var, width=40)
        keyword_entry.pack(side="left", padx=5, pady=2)  # 减小pady值
        
        # 提示文本
        ttk.Label(params_frame, text="(用,分隔)").pack(side="left", padx=0, pady=5)
        
        # 数量
        ttk.Label(params_frame, text="数量:").pack(side="left", padx=10, pady=5)
        self.post_limit_var = tk.StringVar(value="10")
        limit_combo = ttk.Combobox(params_frame, textvariable=self.post_limit_var, values=["10", "50", "100", "200"], width=5)
        limit_combo.pack(side="left", padx=5, pady=5)
        
        # 排序方式
        ttk.Label(params_frame, text="排序:").pack(side="left", padx=10, pady=5)
        self.sort_var = tk.StringVar(value="热门")
        sort_combo = ttk.Combobox(params_frame, textvariable=self.sort_var, values=["热门", "最新", "相关"], width=10)
        sort_combo.pack(side="left", padx=5, pady=5)

    def create_data_table_frame(self, parent):
        """
        创建数据表格框架 - 移除标题并调整间距
        
        @param {ttk.Frame} parent - 父框架
        """
        # 使用普通Frame代替LabelFrame，取消标题
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=5, pady=2)  # 减小pady值
        
        # 创建Treeview表格
        columns = ("社区", "标题", "关键词", "作者", "点赞", "评论数", "发布时间", "帖子内容", "详情")
        self.data_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=5)
        
        # 设置列标题
        for col in columns:
            self.data_table.heading(col, text=col)
            if col in ["标题", "详情"]:
                self.data_table.column(col, width=180)
            elif col in ["社区", "关键词"]:
                self.data_table.column(col, width=100)
            elif col == "帖子内容":
                self.data_table.column(col, width=200)  # 帖子内容列宽度较大
            else:
                self.data_table.column(col, width=70)
        
        # 添加滚动条
        y_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.data_table.yview)
        y_scrollbar.pack(side="right", fill="y")
        
        x_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.data_table.xview)
        x_scrollbar.pack(side="bottom", fill="x")
        
        self.data_table.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        self.data_table.pack(fill="both", expand=True)
        
        # 绑定右键菜单
        self.data_table.bind("<Button-3>", self.show_context_menu)
        
        # 创建右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="打开帖子", command=self.open_post_url)
        self.context_menu.add_command(label="复制地址", command=self.copy_post_url)

    def create_action_buttons_frame(self, parent):
        """
        创建操作按钮框架 - 调整位置和间距
        
        @param {ttk.Frame} parent - 父框架
        """
        # 减小上下间距
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", padx=5, pady=2)  # 减小pady值
        
        # 使用水平布局，更加紧凑
        ttk.Button(button_frame, text="开始采集", command=self.start_scraping).pack(side="left", padx=10, pady=2)
        ttk.Button(button_frame, text="停止采集", command=self.stop_scraping_process).pack(side="left", padx=10, pady=2)
        ttk.Button(button_frame, text="导出CSV", command=self.export_csv).pack(side="left", padx=10, pady=2)
        ttk.Button(button_frame, text="清空数据", command=self.clear_data).pack(side="left", padx=10, pady=2)

    def create_log_frame(self, parent):
        """
        创建日志框架 - 移除标题并调整间距
        
        @param {ttk.Frame} parent - 父框架
        """
        # 使用普通Frame代替LabelFrame，取消标题
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill="x", padx=5, pady=2)  # 减小pady值
        
        # 调整日志框高度
        self.log_text = tk.Text(log_frame, height=4, width=80)
        self.log_text.pack(fill="both", padx=5, pady=2)  # 减小pady值
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.log_text, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

    def log_message(self, message):
        """
        记录日志消息
        
        @param {str} message - 日志消息
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # 自动滚动到最新日志

    def connect_reddit(self):
        """
        连接Reddit API
        """
        client_id = self.client_id_var.get().strip()
        client_secret = self.client_secret_var.get().strip()
        user_agent = self.user_agent_var.get().strip()
        
        if not client_id or not client_secret or not user_agent:
            messagebox.showerror("错误", "请填写所有API配置信息")
            return
        
        try:
            # 修改初始化方式，明确指定所有必要参数
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                check_for_updates=False,  # 禁用更新检查
                comment_kind="t1",        # 明确指定类型
                message_kind="t4",
                redditor_kind="t2",
                submission_kind="t3",
                subreddit_kind="t5",
                trophy_kind="t6",
                oauth_url="https://oauth.reddit.com",
                reddit_url="https://www.reddit.com",
                short_url="https://redd.it",
                ratelimit_seconds=5,      # 设置速率限制
                timeout=16                # 设置超时
            )
            
            # 测试连接 - 尝试获取热门帖子而不是用户信息
            try:
                # 使用更可靠的测试方法
                subreddit = self.reddit.subreddit("announcements")
                for _ in subreddit.hot(limit=1):
                    break
                
                self.log_message("已成功连接到Reddit API")
                messagebox.showinfo("成功", "已成功连接到Reddit API")
                
                # 连接成功后自动保存配置
                self.save_api_config()
            except Exception as e:
                self.log_message(f"API连接测试失败: {str(e)}")
                messagebox.showerror("错误", f"API连接测试失败: {str(e)}")
        except Exception as e:
            self.log_message(f"连接Reddit API时出错: {str(e)}")
            messagebox.showerror("错误", f"连接Reddit API时出错: {str(e)}")

    def save_api_config(self):
        """
        保存API配置到本地文件
        """
        config = {
            "client_id": self.client_id_var.get().strip(),
            "client_secret": self.client_secret_var.get().strip(),
            "user_agent": self.user_agent_var.get().strip()
        }
        
        try:
            # 确保使用正确的路径
            config_path = self.config_file
            
            # 如果是打包后的环境，使用当前工作目录
            if getattr(sys, 'frozen', False):
                config_path = os.path.join(os.getcwd(), "reddit_config.json")
            
            with open(config_path, "w") as f:
                json.dump(config, f)
            self.log_message(f"API配置已保存到本地: {config_path}")
        except Exception as e:
            self.log_message(f"保存API配置时出错: {str(e)}")
            messagebox.showerror("错误", f"保存API配置时出错: {str(e)}")

    def load_api_config(self):
        """
        从本地文件加载API配置
        """
        # 确保使用正确的路径
        config_path = self.config_file
        
        # 如果是打包后的环境，使用当前工作目录
        if getattr(sys, 'frozen', False):
            config_path = os.path.join(os.getcwd(), "reddit_config.json")
        
        if not os.path.exists(config_path):
            self.log_message("未找到保存的API配置")
            return
        
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            
            self.client_id_var.set(config.get("client_id", ""))
            self.client_secret_var.set(config.get("client_secret", ""))
            self.user_agent_var.set(config.get("user_agent", "RedditSpier v1.0"))
            
            self.log_message(f"已加载保存的API配置: {config_path}")
            
            # 如果有完整的配置信息，自动尝试连接
            if config.get("client_id") and config.get("client_secret") and config.get("user_agent"):
                self.connect_reddit()
        except Exception as e:
            self.log_message(f"加载API配置时出错: {str(e)}")

    def search_subreddits(self):
        """
        搜索Subreddit
        """
        if not self.reddit:
            messagebox.showerror("错误", "请先连接Reddit API")
            return
        
        keyword = self.subreddit_keyword_var.get().strip()
        if not keyword:
            messagebox.showerror("错误", "请输入搜索关键词")
            return
        
        self.log_message(f"正在搜索Subreddit: {keyword}")
        self.subreddit_listbox.delete(0, tk.END)  # 清空列表
        
        try:
            # 使用线程防止GUI卡顿
            threading.Thread(target=self._search_subreddits_thread, args=(keyword,), daemon=True).start()
        except Exception as e:
            self.log_message(f"搜索Subreddit失败: {str(e)}")
            messagebox.showerror("错误", f"搜索Subreddit失败: {str(e)}")

    def _search_subreddits_thread(self, keyword):
        """
        Subreddit搜索线程
        
        @param {str} keyword - 搜索关键词
        """
        try:
            results = self.reddit.subreddits.search(keyword, limit=20)
            count = 0
            
            for subreddit in results:
                self.root.after(0, lambda s=subreddit: self.subreddit_listbox.insert(tk.END, f"{s.display_name} ({s.subscribers} 订阅者)"))
                count += 1
            
            self.root.after(0, lambda: self.log_message(f"找到 {count} 个相关Subreddit"))
            
            if count == 0:
                self.root.after(0, lambda: messagebox.showinfo("结果", "没有找到相关Subreddit"))
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"搜索Subreddit时出错: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"搜索Subreddit时出错: {str(e)}"))

    def add_selected_subreddits(self):
        """
        添加选中的Subreddit到已选择列表
        """
        selected_indices = self.subreddit_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("提示", "请先选择Subreddit")
            return
        
        for index in selected_indices:
            subreddit_text = self.subreddit_listbox.get(index)
            subreddit_name = subreddit_text.split(" ")[0]  # 提取Subreddit名称
            
            # 检查是否已经在列表中
            if subreddit_name not in self.selected_subreddits:
                self.selected_subreddits.append(subreddit_name)
        
        # 更新显示
        self._update_selected_subreddits_display()
        self.log_message(f"已添加 {len(selected_indices)} 个Subreddit到选择列表")

    def remove_selected_subreddit(self):
        """
        从已选择列表中移除选中的Subreddit
        """
        selected_indices = self.selected_subreddits_list.curselection()
        if not selected_indices:
            messagebox.showinfo("提示", "请先选择要移除的Subreddit")
            return
        
        # 从后往前删除，避免索引变化问题
        for index in sorted(selected_indices, reverse=True):
            del self.selected_subreddits[index]
        
        # 更新显示
        self._update_selected_subreddits_display()
        self.log_message(f"已移除 {len(selected_indices)} 个Subreddit")

    def _update_selected_subreddits_display(self):
        """
        更新已选择Subreddit的显示
        """
        self.selected_subreddits_var.set(self.selected_subreddits)

    def start_scraping(self):
        """
        开始采集数据
        """
        if not self.reddit:
            messagebox.showerror("错误", "请先连接Reddit API")
            return
        
        # 使用已选择的Subreddit列表
        if not self.selected_subreddits:
            messagebox.showerror("错误", "请选择至少一个Subreddit")
            return
        
        # 获取关键词 - 支持多个关键词，用逗号分隔
        keyword_text = self.post_keyword_var.get().strip()
        keywords = [k.strip() for k in keyword_text.split(",")] if keyword_text else []
        
        # 过滤空关键词
        keywords = [k for k in keywords if k]
        
        # 获取其他参数
        limit = int(self.post_limit_var.get())
        sort_type = self.sort_var.get()
        
        # 转换排序方式
        sort_map = {"热门": "hot", "最新": "new", "相关": "relevance"}
        sort_by = sort_map.get(sort_type, "hot")
        
        keywords_str = ", ".join(keywords) if keywords else "无"
        self.log_message(f"开始采集数据: Subreddits={', '.join(self.selected_subreddits)}, 关键词={keywords_str}, 数量={limit}, 排序={sort_type}")
        
        # 重置停止标志
        self.stop_scraping = False
        
        # 启动采集线程
        self.scraping_thread = threading.Thread(
            target=self._scrape_data_thread,
            args=(self.selected_subreddits, keywords, limit, sort_by),
            daemon=True
        )
        self.scraping_thread.start()

    def _scrape_data_thread(self, subreddits, keywords, limit, sort_by):
        """
        数据采集线程
        
        @param {list} subreddits - Subreddit名称列表
        @param {list} keywords - 关键词列表
        @param {int} limit - 采集数量限制
        @param {str} sort_by - 排序方式
        """
        try:
            # 清空表格
            self.root.after(0, lambda: self.data_table.delete(*self.data_table.get_children()))
            
            total_posts = 0  # 初始化总帖子数
            
            for subreddit_name in subreddits:
                if self.stop_scraping:
                    self.root.after(0, lambda: self.log_message("采集已停止"))
                    break
                
                self.root.after(0, lambda: self.log_message(f"正在采集 r/{subreddit_name}..."))
                
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # 如果有关键词，则对每个关键词进行搜索
                if keywords:
                    for keyword in keywords:
                        if self.stop_scraping:
                            break
                        
                        self.root.after(0, lambda k=keyword: self.log_message(f"搜索关键词: {k}"))
                        
                        try:
                            posts = subreddit.search(keyword, sort=sort_by, limit=limit)
                            # 传递当前总数，并获取处理后的新总数
                            total_posts = self._process_posts(posts, subreddit_name, keyword, total_posts)
                        except Exception as e:
                            self.root.after(0, lambda err=e: self.log_message(f"搜索关键词 '{keyword}' 时出错: {str(err)}"))
                else:
                    # 没有关键词，直接获取帖子
                    if sort_by == "hot":
                        posts = subreddit.hot(limit=limit)
                    elif sort_by == "new":
                        posts = subreddit.new(limit=limit)
                    else:
                        posts = subreddit.hot(limit=limit)  # 默认为热门
                
                # 传递当前总数，并获取处理后的新总数
                total_posts = self._process_posts(posts, subreddit_name, "", total_posts)
            
            self.root.after(0, lambda: self.log_message(f"采集完成，共获取 {total_posts} 个帖子"))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"采集数据时出错: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"采集数据时出错: {str(e)}"))

    def _process_posts(self, posts, subreddit_name, keyword, total_posts):
        """
        处理帖子数据
        
        @param {praw.models.listing.generator.ListingGenerator} posts - 帖子生成器
        @param {str} subreddit_name - Subreddit名称
        @param {str} keyword - 搜索关键词
        @param {int} total_posts - 当前已处理的帖子总数
        @return {int} - 更新后的帖子总数
        """
        post_count = 0  # 当前批次处理的帖子数
        
        for post in posts:
            if self.stop_scraping:
                break
            
            # 转换时间戳为可读时间
            created_time = datetime.datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M")
            
            # 获取帖子内容
            post_content = post.selftext
            # 截断过长的内容
            if len(post_content) > 200:
                post_content = post_content[:197] + "..."
            
            # 添加到表格
            values = (
                subreddit_name,
                post.title,
                keyword if keyword else "无",
                post.author.name if post.author else "[已删除]",
                post.score,
                post.num_comments,
                created_time,
                post_content,
                f"https://www.reddit.com{post.permalink}"
            )
            
            self.root.after(0, lambda v=values: self.data_table.insert("", "end", values=v))
            post_count += 1  # 增加当前批次的帖子计数
            
            # 防止API速率限制
            time.sleep(0.5)
        
        # 更新并返回总帖子数
        return total_posts + post_count

    def stop_scraping_process(self):
        """
        停止采集过程
        """
        if self.scraping_thread and self.scraping_thread.is_alive():
            self.stop_scraping = True
            self.log_message("正在停止采集...")
        else:
            self.log_message("没有正在进行的采集任务")

    def export_csv(self):
        """
        导出数据为CSV文件
        """
        items = self.data_table.get_children()
        if not items:
            messagebox.showerror("错误", "没有数据可导出")
            return
        
        # 获取保存文件路径
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="保存数据"
        )
        
        if not file_path:
            return  # 用户取消了保存
        
        try:
            # 获取所有数据
            data = []
            columns = ["社区", "标题", "关键词", "作者", "点赞", "评论数", "发布时间", "帖子内容", "详情"]
            
            for item in items:
                values = self.data_table.item(item, "values")
                data.append(dict(zip(columns, values)))
            
            # 创建DataFrame并保存
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, encoding="utf-8-sig")  # 使用带BOM的UTF-8编码，解决中文乱码
            
            self.log_message(f"数据已成功导出到 {file_path}")
            messagebox.showinfo("成功", f"数据已成功导出到 {file_path}")
        except Exception as e:
            self.log_message(f"导出数据时出错: {str(e)}")
            messagebox.showerror("错误", f"导出数据时出错: {str(e)}")

    def clear_data(self):
        """
        清空表格数据
        """
        self.data_table.delete(*self.data_table.get_children())
        self.log_message("已清空数据表格")

    def show_context_menu(self, event):
        """
        显示右键菜单
        
        @param {tk.Event} event - 鼠标事件
        """
        # 获取点击的行
        item = self.data_table.identify_row(event.y)
        if item:
            # 选中该行
            self.data_table.selection_set(item)
            # 显示菜单
            self.context_menu.post(event.x_root, event.y_root)

    def open_post_url(self):
        """
        打开选中帖子的URL
        """
        selected_items = self.data_table.selection()
        if not selected_items:
            return
        
        # 获取选中行的URL（详情列）
        item = selected_items[0]
        values = self.data_table.item(item, "values")
        url = values[8]  # 详情列的索引
        
        # 打开URL
        webbrowser.open(url)
        self.log_message(f"已打开帖子: {url}")

    def copy_post_url(self):
        """
        复制选中帖子的URL到剪贴板
        """
        selected_items = self.data_table.selection()
        if not selected_items:
            return
        
        # 获取选中行的URL（详情列）
        item = selected_items[0]
        values = self.data_table.item(item, "values")
        url = values[8]  # 详情列的索引
        
        # 复制到剪贴板
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.log_message(f"已复制帖子地址: {url}")

    def show_search_result_menu(self, event):
        """
        显示搜索结果右键菜单
        
        @param {tk.Event} event - 鼠标事件
        """
        # 确保有选中项
        if self.subreddit_listbox.curselection():
            self.search_result_menu.post(event.x_root, event.y_root)

    def show_selected_subreddit_menu(self, event):
        """
        显示已选择列表右键菜单
        
        @param {tk.Event} event - 鼠标事件
        """
        # 确保有选中项
        if self.selected_subreddits_list.curselection():
            self.selected_subreddit_menu.post(event.x_root, event.y_root)

    def select_all_subreddits(self):
        """
        全选搜索结果列表中的所有Subreddit
        """
        # 获取列表中的项目数量
        count = self.subreddit_listbox.size()
        if count > 0:
            # 选择所有项目（从0到最后一项）
            self.subreddit_listbox.selection_set(0, count - 1)
            self.log_message("已全选搜索结果")

    def deselect_all_subreddits(self):
        """
        取消全选搜索结果列表中的Subreddit
        """
        self.subreddit_listbox.selection_clear(0, tk.END)
        self.log_message("已取消全选")

    def remove_all_subreddits(self):
        """
        移除所有已选择的Subreddit
        """
        if not self.selected_subreddits:
            return
        
        # 清空已选择列表
        self.selected_subreddits = []
        self.selected_subreddits_var.set(self.selected_subreddits)
        self.log_message("已移除所有已选择的Subreddit")

    def create_menu_bar(self):
        """
        创建菜单栏
        """
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        # 文件菜单
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出CSV", command=self.export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 操作菜单
        action_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="操作", menu=action_menu)
        action_menu.add_command(label="开始采集", command=self.start_scraping)
        action_menu.add_command(label="停止采集", command=self.stop_scraping_process)
        action_menu.add_separator()
        action_menu.add_command(label="清空数据", command=self.clear_data)
        
        # 帮助菜单
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)

    def show_help(self):
        """
        显示使用说明
        """
        help_text = """
        Reddit关键词采集工具使用说明
        
        1. API配置
           - 首先需要在Reddit开发者平台(https://www.reddit.com/prefs/apps)创建应用
           - 填写Client ID、Client Secret和User Agent
           - 点击"连接Reddit"按钮测试连接
           - 连接成功后，可以点击"保存配置"保存API信息
        
        2. Subreddit搜索
           - 在搜索框中输入关键词，点击"搜索"按钮
           - 在结果列表中选择需要的Subreddit
           - 右键点击选中项，选择"添加到已选择"
           - 也可以右键选择"全选"或"取消全选"
           - 已选择的Subreddit会显示在右侧列表中
           - 右键点击已选择列表中的项目可以移除或全部移除
        
        3. 帖子采集参数
           - 关键词：输入要搜索的关键词，多个关键词用逗号分隔
           - 数量：选择每个Subreddit要采集的帖子数量
           - 排序：选择帖子的排序方式（热门、最新、相关）
        
        4. 数据采集
           - 点击"开始采集"按钮开始采集数据
           - 采集过程中可以点击"停止采集"按钮停止
           - 采集完成后，数据会显示在表格中
           - 右键点击表格中的行可以打开帖子或复制地址
        
        5. 数据导出
           - 点击"导出CSV"按钮将数据导出为CSV文件
           - 导出的文件可以用Excel等软件打开
        
        6. 其他功能
           - 点击"清空数据"按钮可以清空表格数据
           - 操作日志会显示在底部，记录所有操作
        """
        
        # 创建帮助窗口
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("600x500")
        
        # 添加文本框显示帮助内容
        text = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text.pack(fill="both", expand=True)
        text.insert(tk.END, help_text)
        text.config(state="disabled")  # 设置为只读
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(text, orient="vertical", command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.config(yscrollcommand=scrollbar.set)

    def show_about(self):
        """
        显示关于信息
        """
        about_text = """
        Reddit关键词采集工具
        
        版本: 1.0.0
        
        功能:
        - 搜索和选择Reddit社区(Subreddit)
        - 根据关键词采集Reddit帖子
        - 导出数据为CSV格式
        
        本工具使用Python和Tkinter开发，
        基于PRAW(Python Reddit API Wrapper)实现Reddit数据采集。
        
        欢迎添加作者微信779059811
        注意: 使用本工具需要遵守Reddit的API使用条款。
        """
        
        messagebox.showinfo("关于", about_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = RedditSpierApp(root)
    root.mainloop() 