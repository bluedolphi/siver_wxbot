#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""main.py
dolphin_wxbot 现代化配置管理器 V3.0
说明：
    现代化UI设计的配置管理器，采用渐变色标题栏、卡片式布局、标签页切换等特色功能，
    提供完整的机器人控制功能和实时日志系统。
    
作者：dolphi
"""

import json         # 处理JSON数据
import os           # 文件操作
import tkinter as tk    # 图形界面库
from tkinter import messagebox, ttk as tk_ttk, simpledialog  # 弹窗、主题控件及简单对话框
import ttkbootstrap as ttk   # 美化版tkinter组件库
from ttkbootstrap.constants import *
import sys
import traceback    # 异常追踪
import threading    # 多线程支持
import ctypes       # 用于在线程中抛出异常
import inspect      # 检查对象类型
import queue        # 队列，用于线程间传递数据
import wxbot_preview  # 导入机器人服务模块
import time
from datetime import datetime
import tkinter       # 添加tkinter导入以处理TclError

# 配置文件名称常量
CONFIG_FILE = "config.json"

def _async_raise(tid, exctype):
    """
    在线程中抛出异常（仅限 CPython，不安全）
    参数：
        tid: 线程ID
        exctype: 要抛出的异常类型
    """
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("无效的线程 ID")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
        raise SystemError("PyThreadState_SetAsyncExc 失败")

class QueueWriter:
    """
    将写入的文本放入队列，用于捕获机器人线程的输出
    """
    def __init__(self, out_queue):
        self.out_queue = out_queue

    def write(self, text):
        if text:
            self.out_queue.put(text)

    def flush(self):
        pass

class ModernTooltip:
    """
    现代化提示工具类：带渐变背景和平滑动画的提示信息
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        """显示现代化提示信息"""
        if self.tooltip_window:
            return
        
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # 现代化样式的提示框
        frame = ttk.Frame(self.tooltip_window, bootstyle="secondary")
        frame.pack()
        
        label = ttk.Label(
            frame,
            text=self.text,
            bootstyle="inverse-secondary",
            padding=(10, 5),
            font=("微软雅黑", 9)
        )
        label.pack()
        
        # 添加阴影效果
        self.tooltip_window.attributes('-topmost', True)

    def hide_tooltip(self, event=None):
        """隐藏提示信息"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class ModernModal:
    """
    现代化模态对话框类：替换简单的对话框
    """
    def __init__(self, parent, title, message, input_type="text"):
        self.parent = parent
        self.result = None
        self.modal = tk.Toplevel(parent)
        self.modal.title(title)
        self.modal.geometry("400x200")
        self.modal.resizable(False, False)
        self.modal.transient(parent)
        self.modal.grab_set()
        
        # 居中显示
        self.center_window()
        
        self.create_ui(title, message, input_type)
        
    def center_window(self):
        """窗口居中显示"""
        self.modal.update_idletasks()
        x = (self.modal.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.modal.winfo_screenheight() // 2) - (200 // 2)
        self.modal.geometry(f"400x200+{x}+{y}")
        
    def create_ui(self, title, message, input_type):
        """创建模态框UI"""
        # 标题栏
        title_frame = ttk.Frame(self.modal, bootstyle="primary")
        title_frame.pack(fill=tk.X, padx=2, pady=2)
        ttk.Label(title_frame, text=title, font=("微软雅黑", 12, "bold"), 
                 bootstyle="inverse-primary").pack(pady=10)
        
        # 内容区
        content_frame = ttk.Frame(self.modal)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ttk.Label(content_frame, text=message, font=("微软雅黑", 10)).pack(pady=10)
        
        self.entry = ttk.Entry(content_frame, font=("微软雅黑", 10))
        self.entry.pack(fill=tk.X, pady=10)
        self.entry.focus_set()
        
        # 按钮区
        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="确定", command=self.ok_clicked, 
                  bootstyle="success-outline").pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=self.cancel_clicked,
                  bootstyle="secondary-outline").pack(side=tk.LEFT, padx=10)
        
        # 绑定回车键
        self.modal.bind('<Return>', lambda e: self.ok_clicked())
        
    def ok_clicked(self):
        self.result = self.entry.get()
        self.modal.destroy()
        
    def cancel_clicked(self):
        self.result = None
        self.modal.destroy()
        
    def show(self):
        self.modal.wait_window()
        return self.result

class ConfigEditor:
    """
    配置管理器类：
    1. 加载、显示、保存新版配置文件（config.json），支持文本、列表、多行、开关等输入组件；
    2. 提供机器人控制功能，包括启动、关闭、重启机器人，并将机器人的标准输出显示在界面上。
    """
    def __init__(self, root):
        self.root = root
        self.root.title("dolphin_wxbot 管理器 V2.0  dolphi")
        self.root.geometry("800x800")
        
        # 机器人控制相关属性
        self.bot_thread = None   # 机器人线程引用
        self.status_var = tk.StringVar(value="状态：未运行")
        self.status_style = "inverse-danger"  # 初始状态显示红色（未运行）
        self.output_queue = queue.Queue()     # 队列用于捕获机器人线程的输出
        
        # 配置项提示说明
        self.tooltips = {
            # API配置相关
            "api_name": "API配置的显示名称，便于识别",
            "platform": "API平台类型：openai, coze, dify, fastgpt, n8n, ragflow",
            "api_key": "在此处填写从开放平台获取的API密钥",
            "base_url": "填写开放平台的接口网址/链接",
            "model": "你在开发平台要调用的模型名称",
            "enabled": "是否启用此API配置",
            "is_default": "是否设为默认API（用于未指定API的场景）",
            # 机器人设置相关
            "机器人名字": "机器人在被询问身份时回复的名称",
            "prompt": "系统提示词，用于定义机器人的基本行为和回复规则",
            "管理员": "管理员名称，用于识别机器人管理者",
            "default_api_id": "默认使用的API配置ID",
            # 监听规则相关
            "群机器人开关": "启用/禁用群机器人功能",
            "user_name": "用户名称或ID",
            "user_api_id": "该用户专用的API配置ID",
            "user_enabled": "是否启用对该用户的监听",
            "group_name": "群组名称",
            "group_api_id": "该群组专用的API配置ID",
            "group_enabled": "是否启用对该群组的监听",
            "at_required": "是否需要@机器人才回复",
            "group_admins": "群组管理员列表",
            # 备忘录相关
            "备忘录1": "备忘信息1，用于记录重要信息",
            "备忘录2": "备忘信息2，用于记录其他信息"
        }
        
        self.style = ttk.Style(theme="minty")
        self.setup_ui()
        self.load_config()
        
        # 初始化异步日志跟踪
        self._last_async_log_count = 0
        
        # 开始定时更新机器人输出显示
        self.update_output()
        
        # 启动后添加欢迎日志和检测wxauto库
        self.root.after(1000, lambda: self.log_message("dolphin_wxbot 配置管理器启动完成 - dolphi"))
        self.root.after(1200, self.detect_wx_library_and_log)
        self.root.after(1300, lambda: self.log_message("提示：配置修改会自动保存，重启机器人后生效。"))
    
    def setup_ui(self):
        """构建主界面布局（现代化：渐变标题栏 + 卡片式 + 标签页 + 响应式）"""
        # 顶部渐变标题栏
        self.create_gradient_header(self.root)



        # Notebook 标签页
        notebook = tk_ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # — 控制面板页（启动/停止/重启 等卡片按钮）
        self.tab_control = ttk.Frame(notebook)
        notebook.add(self.tab_control, text="控制面板")
        self.build_control_tab(self.tab_control)

        # — API配置页
        self.tab_api = ttk.Frame(notebook)
        notebook.add(self.tab_api, text="API配置")
        self.build_api_config_tab(self.tab_api)

        # — 机器人设置页
        self.tab_bot_settings = ttk.Frame(notebook)
        notebook.add(self.tab_bot_settings, text="机器人设置")
        self.build_bot_settings_tab(self.tab_bot_settings)

        # — 监听规则页
        self.tab_listen_rules = ttk.Frame(notebook)
        notebook.add(self.tab_listen_rules, text="监听规则")
        self.build_listen_rules_tab(self.tab_listen_rules)

        # — 备忘录页
        self.tab_memo = ttk.Frame(notebook)
        notebook.add(self.tab_memo, text="备忘录")
        self.build_memo_tab(self.tab_memo)

        # 移除独立的日志标签页，日志功能已集成到控制面板中

        # 响应式：在根窗口大小变化时调整组件
        self.root.update_idletasks()

    def create_gradient_header(self, parent):
        """渐变色标题栏：Canvas 绘制线性渐变 + 标题文本"""
        header_h = 64
        canvas = tk.Canvas(parent, height=header_h, highlightthickness=0, bd=0)
        canvas.pack(fill=tk.X)
        # 线性渐变（从 #7C4DFF 到 #00BCD4）
        start_color = (124, 77, 255)
        end_color = (0, 188, 212)
        width = parent.winfo_screenwidth()
        steps = max(width, 600)
        for i in range(steps):
            r = int(start_color[0] + (end_color[0] - start_color[0]) * i / steps)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * i / steps)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * i / steps)
            color = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(i, 0, i, header_h, fill=color)
        canvas.create_text(18, header_h//2, anchor="w", fill="white",
                           font=("微软雅黑", 16, "bold"),
                           text="dolphin_wxbot 管理器 · 现代化UI")

    def build_api_config_tab(self, parent):
        """API配置页：多API接口管理"""
        card = ttk.Frame(parent, bootstyle="light")
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题和操作按钮
        header_frame = ttk.Frame(card)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(header_frame, text="API接口配置", bootstyle="secondary",
                 font=("微软雅黑", 11, "bold")).pack(side=tk.LEFT)
        
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        btn_add_api = ttk.Button(btn_frame, text="+ 添加API", command=self.add_api_config, bootstyle="success")
        btn_add_api.pack(side=tk.LEFT, padx=(0, 5))
        self.attach_hover(btn_add_api, "success")
        
        btn_save_api = ttk.Button(btn_frame, text="保存配置", command=self.save_api_config, bootstyle="primary")
        btn_save_api.pack(side=tk.LEFT)
        self.attach_hover(btn_save_api, "primary")
        
        # API列表容器（添加滚动条支持）
        list_main_frame = ttk.Frame(card)
        list_main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建画布和滚动条
        canvas = tk.Canvas(list_main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_main_frame, orient="vertical", command=canvas.yview)
        self.api_list_frame = ttk.Frame(canvas)
        
        self.api_list_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.api_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        
        # 初始化API配置列表
        self.api_configs = []
    
    def build_bot_settings_tab(self, parent):
        """机器人设置页：机器人名称、提示词和管理员配置"""
        card = ttk.Frame(parent, bootstyle="light")
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题和保存按钮
        header_frame = ttk.Frame(card)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(header_frame, text="机器人设置", bootstyle="secondary",
                 font=("微软雅黑", 11, "bold")).pack(side=tk.LEFT)
        
        btn_save_bot = ttk.Button(header_frame, text="保存设置", command=self.save_bot_settings, bootstyle="primary")
        btn_save_bot.pack(side=tk.RIGHT)
        self.attach_hover(btn_save_bot, "primary")
        
        # 滚动区域
        main_frame = ttk.Frame(card)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.bot_settings_frame = ttk.Frame(canvas)
        
        self.bot_settings_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.bot_settings_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        
        # 初始化机器人设置字段
        self.bot_fields = {}
        self.create_bot_settings_fields()
    
    def build_listen_rules_tab(self, parent):
        """监听规则页：用户列表、群组列表和开关设置"""
        card = ttk.Frame(parent, bootstyle="light")
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题和保存按钮
        header_frame = ttk.Frame(card)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(header_frame, text="监听规则", bootstyle="secondary",
                 font=("微软雅黑", 11, "bold")).pack(side=tk.LEFT)
        
        btn_save_rules = ttk.Button(header_frame, text="保存规则", command=self.save_listen_rules, bootstyle="primary")
        btn_save_rules.pack(side=tk.RIGHT)
        self.attach_hover(btn_save_rules, "primary")
        
        # 创建notebook用于分组显示
        rules_notebook = ttk.Notebook(card)
        rules_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 全局设置页
        global_frame = ttk.Frame(rules_notebook)
        rules_notebook.add(global_frame, text="全局设置")
        self.build_global_rules(global_frame)
        
        # 用户规则页
        users_frame = ttk.Frame(rules_notebook)
        rules_notebook.add(users_frame, text="用户规则")
        self.build_user_rules(users_frame)
        
        # 群组规则页
        groups_frame = ttk.Frame(rules_notebook)
        rules_notebook.add(groups_frame, text="群组规则")
        self.build_group_rules(groups_frame)
    
    def build_memo_tab(self, parent):
        """备忘录页：备忘录内容管理。备忘录用于存储重要信息，可以通过命令查看和管理。"""
        card = ttk.Frame(parent, bootstyle="light")
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题和保存按钮
        header_frame = ttk.Frame(card)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(header_frame, text="备忘录管理", bootstyle="secondary",
                 font=("微软雅黑", 11, "bold")).pack(side=tk.LEFT)
        
        btn_save_memo = ttk.Button(header_frame, text="保存备忘录", command=self.save_memo, bootstyle="primary")
        btn_save_memo.pack(side=tk.RIGHT)
        self.attach_hover(btn_save_memo, "primary")
        
        # 备忘录内容
        memo_frame = ttk.Frame(card)
        memo_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 备忘录说明
        info_frame = ttk.Frame(memo_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(info_frame, text="备忘录用于存储重要信息，用户可以通过 '@机器人名 查看备忘录' 命令查看内容。", 
                 bootstyle="info", font=("微软雅黑", 9)).pack(anchor="w")
        
        # 初始化备忘录字段
        self.memo_fields = {}
        
        # 备忘录项目列表
        self.memo_items = [
            {"title": "备忘录1", "content": "请输入重要信息..."},
            {"title": "备忘录2", "content": "请输入其他信息..."}
        ]
        
        # 操作按钮
        btn_frame = ttk.Frame(memo_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_add_memo = ttk.Button(btn_frame, text="+ 新增备忘录", command=self.add_memo_item, bootstyle="success")
        btn_add_memo.pack(side=tk.LEFT)
        self.attach_hover(btn_add_memo, "success")
        
        # 备忘录列表容器
        self.memo_list_frame = ttk.Frame(memo_frame)
        self.memo_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_memo_fields()
    
    def add_api_config(self):
        """添加新的API配置"""
        api_id = f"api_{len(self.api_configs) + 1}"
        new_config = {
            "id": api_id,
            "name": f"API配置{len(self.api_configs) + 1}",
            "platform": "openai",
            "api_key": "",
            "base_url": "",
            "enabled": True,
            "is_default": len(self.api_configs) == 0
        }
        self.api_configs.append(new_config)
        self.log_message(f"添加新API配置: {new_config['name']} ({api_id})")
        self.refresh_api_list()
    
    def refresh_api_list(self):
        """刷新API配置列表显示"""
        # 清理旧的widgets引用
        if hasattr(self, 'api_widgets'):
            self.api_widgets.clear()
        
        # 清空显示区域
        for widget in self.api_list_frame.winfo_children():
            widget.destroy()
        
        # 重新创建API配置组件
        for i, config in enumerate(self.api_configs):
            self.create_api_config_widget(self.api_list_frame, config, i)
    
    def log_message(self, message):
        """向日志窗口输出消息"""
        try:
            if hasattr(self, 'output_text'):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{timestamp}] {message}\n"
                self.output_text.config(state=tk.NORMAL)
                self.output_text.insert(tk.END, log_entry)
                self.output_text.see(tk.END)
                self.output_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"日志输出错误: {e}")

    def save_api_config(self):
        """保存API配置"""
        try:
            # 收集所有API配置
            api_configs = []
            if hasattr(self, 'api_widgets'):
                for key, widgets in self.api_widgets.items():
                    try:
                        api_config = {
                            "id": self.api_configs[int(key.split('_')[1])].get('id', f"api_{len(api_configs)+1}"),
                            "name": widgets['name'].get(),
                            "platform": widgets['platform'].get(),
                            "api_key": widgets['api_key'].get(),
                            "base_url": widgets['base_url'].get(),
                            "enabled": widgets['enabled'].get(),
                            "is_default": widgets['is_default'].get()
                        }
                        api_configs.append(api_config)
                        
                        # 记录每个API配置的更改
                        self.log_message(f"API配置更新: {api_config['name']} ({api_config['platform']}) - {'启用' if api_config['enabled'] else '禁用'}")
                        
                    except (KeyError, IndexError, tkinter.TclError):
                        # 组件已被销毁或不存在，跳过
                        continue
            
            # 如果没有收集到数据，使用当前内存中的配置
            if not api_configs:
                api_configs = self.api_configs
            
            # 保存到配置文件
            if hasattr(self, 'config'):
                self.config['api_configs'] = api_configs
                # 更新内存中的配置
                self.api_configs = api_configs
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=4)
            
            self.log_message(f"已保存 {len(api_configs)} 个API配置")
            messagebox.showinfo("成功", "API配置已保存")
        except Exception as e:
            error_msg = f"保存API配置失败: {str(e)}"
            self.log_message(f"错误: {error_msg}")
            messagebox.showerror("错误", error_msg)

    def save_listen_rules(self):
        """保存监听规则"""
        try:
            # 收集用户规则数据
            user_rules = []
            if hasattr(self, 'user_widgets'):
                for key, widgets in self.user_widgets.items():
                    try:
                        # 从API选择框获取选中的API ID
                        api_id = ""
                        if widgets['api_combo'].current() >= 0:
                            selected_index = widgets['api_combo'].current()
                            if selected_index < len(self.api_configs):
                                api_id = self.api_configs[selected_index].get('id', '')
                        
                        user_rule = {
                            "name": widgets['name'].get(),
                            "api_id": api_id,
                            "enabled": widgets['enabled'].get()
                        }
                        user_rules.append(user_rule)
                        
                        # 记录用户规则更改
                        self.log_message(f"用户规则更新: {user_rule['name']} - API: {api_id} - {'\u542f\u7528' if user_rule['enabled'] else '\u7981\u7528'}")
                        
                    except (KeyError, tkinter.TclError):
                        continue
            
            # 收集群组规则数据
            group_rules = []
            if hasattr(self, 'group_widgets'):
                for key, widgets in self.group_widgets.items():
                    try:
                        # 从API选择框获取选中的API ID
                        api_id = ""
                        if widgets['api_combo'].current() >= 0:
                            selected_index = widgets['api_combo'].current()
                            if selected_index < len(self.api_configs):
                                api_id = self.api_configs[selected_index].get('id', '')
                        
                        group_rule = {
                            "name": widgets['name'].get(),
                            "api_id": api_id,
                            "enabled": widgets['enabled'].get(),
                            "at_required": widgets['at_required'].get(),
                            "admins": []
                        }
                        group_rules.append(group_rule)
                        
                        # 记录群组规则更改
                        at_text = ", 需要@" if group_rule['at_required'] else ""
                        self.log_message(f"群组规则更新: {group_rule['name']} - API: {api_id} - {'\u542f\u7528' if group_rule['enabled'] else '\u7981\u7528'}{at_text}")
                        
                    except (KeyError, tkinter.TclError):
                        continue
            
            # 收集消息类型过滤配置
            message_types_filter = {
                "enabled": self.message_filter_enabled.get() if hasattr(self, 'message_filter_enabled') else True,
                "allowed_types": [],
                "description": "控制哪些消息类型需要处理。如果enabled为false，则处理所有类型"
            }

            # 收集选中的消息类型
            if hasattr(self, 'message_type_vars'):
                for type_key, var in self.message_type_vars.items():
                    if var.get():
                        message_types_filter["allowed_types"].append(type_key)
            else:
                # 如果没有UI组件，默认允许所有类型
                message_types_filter["allowed_types"] = ["text", "link", "location", "image", "file", "voice", "video", "emotion"]

            # 收集监听规则数据
            listen_rules = {
                "global_bot_enabled": self.global_bot_switch.get() if hasattr(self, 'global_bot_switch') else True,
                "default_api_id": self.default_api_var.get() if hasattr(self, 'default_api_var') else "",
                "message_types_filter": message_types_filter,
                "user_rules": user_rules,
                "group_rules": group_rules
            }
            
            # 更新内存中的规则
            self.user_rules = user_rules
            self.group_rules = group_rules
            
            # 保存到配置文件
            if hasattr(self, 'config'):
                self.config['listen_rules'] = listen_rules
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=4)
            
            # 记录全局设置
            global_status = "启用" if listen_rules['global_bot_enabled'] else "禁用"
            self.log_message(f"全局设置: 群机器人{global_status}, 默认API: {listen_rules['default_api_id']}")
            self.log_message(f"已保存 {len(user_rules)} 个用户规则, {len(group_rules)} 个群组规则")
            
            messagebox.showinfo("成功", "监听规则已保存")
        except Exception as e:
            error_msg = f"保存监听规则失败: {str(e)}"
            self.log_message(f"错误: {error_msg}")
            messagebox.showerror("错误", error_msg)

    def save_bot_settings(self):
        """保存机器人设置"""
        try:
            # 收集机器人设置数据
            bot_settings = {}
            if hasattr(self, 'bot_fields'):
                if "机器人名字" in self.bot_fields:
                    bot_settings["机器人名字"] = self.bot_fields["机器人名字"].get()
                    self.log_message(f"机器人名字更新: {bot_settings['机器人名字']}")
                    
                if "管理员" in self.bot_fields:
                    bot_settings["管理员"] = self.bot_fields["管理员"].get()
                    self.log_message(f"管理员更新: {bot_settings['管理员']}")
                    
                if "prompt" in self.bot_fields:
                    bot_settings["prompt"] = self.bot_fields["prompt"].get("1.0", tk.END).strip()
                    self.log_message(f"系统提示词已更新 ({len(bot_settings['prompt'])}个字符)")
                    
                if "default_api_id" in self.bot_fields:
                    # 从选择框获取选中的API ID
                    selected_text = self.bot_fields["default_api_id"].get()
                    api_id = ""
                    if selected_text and "(" in selected_text and ")" in selected_text:
                        # 从 "API名称 (api_id)" 格式中提取 api_id
                        api_id = selected_text.split("(")[1].split(")")[0]
                    bot_settings["default_api_id"] = api_id
                    self.log_message(f"默认API更新: {api_id}")
            
            # 保存到配置文件
            if hasattr(self, 'config'):
                self.config.update(bot_settings)
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=4)
            
            self.log_message("机器人设置已保存")
            messagebox.showinfo("成功", "机器人设置已保存")
        except Exception as e:
            error_msg = f"保存机器人设置失败: {str(e)}"
            self.log_message(f"错误: {error_msg}")
            messagebox.showerror("错误", error_msg)

    def save_memo(self):
        """保存备忘录"""
        try:
            # 收集备忘录数据
            memo_data = []
            for key, widgets in self.memo_fields.items():
                if key.startswith("memo_"):
                    memo_item = {
                        "title": widgets["title"].get(),
                        "content": widgets["content"].get("1.0", tk.END).strip()
                    }
                    memo_data.append(memo_item)
                    # 记录备忘录更改
                    self.log_message(f"备忘录更新: {memo_item['title']} ({len(memo_item['content'])}个字符)")
            
            # 保存到配置文件
            if hasattr(self, 'config'):
                self.config['memo_data'] = memo_data
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=4)
            
            self.log_message(f"已保存 {len(memo_data)} 个备忘录项目")
            messagebox.showinfo("成功", "备忘录已保存")
        except Exception as e:
            error_msg = f"保存备忘录失败: {str(e)}"
            self.log_message(f"错误: {error_msg}")
            messagebox.showerror("错误", error_msg)
    
    def build_global_rules(self, parent):
        """构建全局监听规则设置"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 群机器人开关
        switch_frame = ttk.Frame(frame)
        switch_frame.pack(fill=tk.X, pady=5)
        ttk.Label(switch_frame, text="群机器人开关:").pack(side=tk.LEFT)
        self.global_bot_switch = tk.BooleanVar(value=True)
        ttk.Checkbutton(switch_frame, variable=self.global_bot_switch).pack(side=tk.LEFT, padx=10)

        # 默认API选择
        api_frame = ttk.Frame(frame)
        api_frame.pack(fill=tk.X, pady=5)
        ttk.Label(api_frame, text="默认API接口:").pack(side=tk.LEFT)
        self.default_api_var = tk.StringVar()
        self.default_api_combo = ttk.Combobox(api_frame, textvariable=self.default_api_var, state="readonly")
        self.default_api_combo.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # 绑定下拉事件
        def update_global_api_options(event=None):
            """更新全局设置的API选项"""
            api_names = [f"{api.get('name', api.get('id', ''))} ({api.get('id', '')})" for api in self.api_configs]
            current_selection = self.default_api_combo.get()
            self.default_api_combo['values'] = api_names
            # 保持当前选择（如果仍然有效）
            if current_selection in api_names:
                self.default_api_combo.set(current_selection)

        self.default_api_combo.bind('<Button-1>', update_global_api_options)
        self.default_api_combo.bind('<Down>', update_global_api_options)

        # 消息类型过滤设置
        self.build_message_type_filter(frame)

    def build_message_type_filter(self, parent):
        """构建消息类型过滤设置"""
        # 消息类型过滤框架
        filter_frame = ttk.LabelFrame(parent, text="消息类型过滤设置", padding=10)
        filter_frame.pack(fill=tk.X, pady=(10, 5))

        # 过滤功能开关
        switch_frame = ttk.Frame(filter_frame)
        switch_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(switch_frame, text="启用消息类型过滤:").pack(side=tk.LEFT)
        self.message_filter_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(switch_frame, variable=self.message_filter_enabled,
                       command=self.on_message_filter_toggle).pack(side=tk.LEFT, padx=10)

        # 消息类型选择区域
        types_frame = ttk.Frame(filter_frame)
        types_frame.pack(fill=tk.X)

        ttk.Label(types_frame, text="允许处理的消息类型:",
                 font=("微软雅黑", 9, "bold")).pack(anchor=tk.W, pady=(0, 5))

        # 消息类型复选框容器
        self.message_types_frame = ttk.Frame(types_frame)
        self.message_types_frame.pack(fill=tk.X)

        # 定义消息类型及其显示名称
        self.message_types = [
            ("text", "文本消息", "普通的文字消息"),
            ("link", "链接消息", "分享的网页链接"),
            ("location", "位置消息", "地理位置信息"),
            ("image", "图片消息", "图片和照片"),
            ("file", "文件消息", "各种文档和文件"),
            ("voice", "语音消息", "语音和音频"),
            ("video", "视频消息", "视频文件"),
            ("emotion", "表情消息", "表情包和动画表情")
        ]

        # 创建消息类型复选框变量
        self.message_type_vars = {}

        # 创建两列布局
        left_frame = ttk.Frame(self.message_types_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_frame = ttk.Frame(self.message_types_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 分配消息类型到两列
        for i, (type_key, type_name, type_desc) in enumerate(self.message_types):
            # 创建复选框变量
            var = tk.BooleanVar(value=True)
            self.message_type_vars[type_key] = var

            # 选择放置的列
            parent_frame = left_frame if i < 4 else right_frame

            # 创建复选框框架
            cb_frame = ttk.Frame(parent_frame)
            cb_frame.pack(fill=tk.X, pady=2)

            # 复选框
            cb = ttk.Checkbutton(cb_frame, text=type_name, variable=var)
            cb.pack(side=tk.LEFT)

            # 添加提示信息
            self.attach_hover(cb, type_desc)

        # 快捷操作按钮
        btn_frame = ttk.Frame(filter_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="全选", command=self.select_all_message_types,
                  bootstyle="secondary-outline").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="全不选", command=self.deselect_all_message_types,
                  bootstyle="secondary-outline").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="仅文本", command=self.select_text_only,
                  bootstyle="secondary-outline").pack(side=tk.LEFT, padx=5)

    def on_message_filter_toggle(self):
        """消息过滤开关切换事件"""
        enabled = self.message_filter_enabled.get()
        state = "normal" if enabled else "disabled"

        # 更新所有消息类型复选框的状态
        for widget in self.message_types_frame.winfo_children():
            for child in widget.winfo_children():
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.Checkbutton):
                        grandchild.configure(state=state)

    def select_all_message_types(self):
        """选择所有消息类型"""
        for var in self.message_type_vars.values():
            var.set(True)

    def deselect_all_message_types(self):
        """取消选择所有消息类型"""
        for var in self.message_type_vars.values():
            var.set(False)

    def select_text_only(self):
        """仅选择文本消息"""
        for type_key, var in self.message_type_vars.items():
            var.set(type_key == "text")

    def build_user_rules(self, parent):
        """构建用户监听规则"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 用户列表操作按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_add_user = ttk.Button(btn_frame, text="+ 添加用户", command=self.add_user_rule, bootstyle="success")
        btn_add_user.pack(side=tk.LEFT)
        self.attach_hover(btn_add_user, "success")
        
        # 用户列表容器（添加滚动条支持）
        users_main_frame = ttk.Frame(frame)
        users_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建画布和滚动条
        users_canvas = tk.Canvas(users_main_frame, highlightthickness=0)
        users_scrollbar = ttk.Scrollbar(users_main_frame, orient="vertical", command=users_canvas.yview)
        self.users_list_frame = ttk.Frame(users_canvas)
        
        self.users_list_frame.bind("<Configure>",
            lambda e: users_canvas.configure(scrollregion=users_canvas.bbox("all")))
        users_canvas.create_window((0, 0), window=self.users_list_frame, anchor="nw")
        users_canvas.configure(yscrollcommand=users_scrollbar.set)
        users_canvas.pack(side="left", fill="both", expand=True)
        users_scrollbar.pack(side="right", fill="y")
        users_canvas.bind("<MouseWheel>", lambda event: users_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        
        self.user_rules = []
    
    def build_group_rules(self, parent):
        """构建群组监听规则"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 群组列表操作按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_add_group = ttk.Button(btn_frame, text="+ 添加群组", command=self.add_group_rule, bootstyle="success")
        btn_add_group.pack(side=tk.LEFT)
        self.attach_hover(btn_add_group, "success")
        
        # 群组列表容器（添加滚动条支持）
        groups_main_frame = ttk.Frame(frame)
        groups_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建画布和滚动条
        groups_canvas = tk.Canvas(groups_main_frame, highlightthickness=0)
        groups_scrollbar = ttk.Scrollbar(groups_main_frame, orient="vertical", command=groups_canvas.yview)
        self.groups_list_frame = ttk.Frame(groups_canvas)
        
        self.groups_list_frame.bind("<Configure>",
            lambda e: groups_canvas.configure(scrollregion=groups_canvas.bbox("all")))
        groups_canvas.create_window((0, 0), window=self.groups_list_frame, anchor="nw")
        groups_canvas.configure(yscrollcommand=groups_scrollbar.set)
        groups_canvas.pack(side="left", fill="both", expand=True)
        groups_scrollbar.pack(side="right", fill="y")
        groups_canvas.bind("<MouseWheel>", lambda event: groups_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        
        self.group_rules = []
    
    def add_user_rule(self):
        """添加用户规则"""
        user_rule = {
            "name": "",
            "api_id": "api_1",
            "enabled": True
        }
        self.user_rules.append(user_rule)
        self.log_message("添加新用户规则")
        self.refresh_user_rules()
    
    def add_group_rule(self):
        """添加群组规则"""
        group_rule = {
            "name": "",
            "api_id": "api_1", 
            "enabled": True,
            "at_required": False,
            "admins": []
        }
        self.group_rules.append(group_rule)
        self.log_message("添加新群组规则")
        self.refresh_group_rules()
    
    def refresh_user_rules(self):
        """刷新用户规则显示"""
        # 清理旧的widgets引用
        if hasattr(self, 'user_widgets'):
            self.user_widgets.clear()
        
        # 清空显示区域
        for widget in self.users_list_frame.winfo_children():
            widget.destroy()
        
        # 重新创建用户规则组件
        for i, rule in enumerate(self.user_rules):
            self.create_user_rule_widget(self.users_list_frame, rule, i)
    
    def refresh_group_rules(self):
        """刷新群组规则显示"""
        # 清理旧的widgets引用
        if hasattr(self, 'group_widgets'):
            self.group_widgets.clear()
        
        # 清空显示区域
        for widget in self.groups_list_frame.winfo_children():
            widget.destroy()
        
        # 重新创建群组规则组件
        for i, rule in enumerate(self.group_rules):
            self.create_group_rule_widget(self.groups_list_frame, rule, i)
    
    def create_api_config_widget(self, parent, config, index):
        """创建API配置组件"""
        card = ttk.Frame(parent, bootstyle="light")
        card.pack(fill=tk.X, padx=5, pady=5)
        
        # API配置标题
        header = ttk.Frame(card)
        header.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header, text=f"API配置 {index+1}", font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT)
        
        # 删除按钮
        btn_delete = ttk.Button(header, text="删除", command=lambda: self.delete_api_config(index), bootstyle="danger")
        btn_delete.pack(side=tk.RIGHT)
        self.attach_hover(btn_delete, "danger")
        
        # 配置字段
        fields_frame = ttk.Frame(card)
        fields_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 初始化组件字典
        widgets = {}
        
        # 名称和平台
        row1 = ttk.Frame(fields_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="名称:", width=8).pack(side=tk.LEFT)
        name_entry = ttk.Entry(row1, width=20)
        name_entry.pack(side=tk.LEFT, padx=(0, 10))
        name_entry.insert(0, config.get("name", ""))
        widgets['name'] = name_entry
        
        ttk.Label(row1, text="平台:", width=8).pack(side=tk.LEFT)
        platform_combo = ttk.Combobox(row1, values=["openai", "coze", "dify", "fastgpt", "n8n", "ragflow"], width=15)
        platform_combo.pack(side=tk.LEFT)
        platform_combo.set(config.get("platform", "openai"))
        widgets['platform'] = platform_combo
        
        # API Key
        row2 = ttk.Frame(fields_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="API Key:", width=8).pack(side=tk.LEFT)
        key_entry = ttk.Entry(row2, show="*")
        key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        key_entry.insert(0, config.get("api_key", ""))
        widgets['api_key'] = key_entry
        
        # Base URL
        row3 = ttk.Frame(fields_frame)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="Base URL:", width=8).pack(side=tk.LEFT)
        url_entry = ttk.Entry(row3)
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        url_entry.insert(0, config.get("base_url", ""))
        widgets['base_url'] = url_entry
        
        # 状态选项
        row4 = ttk.Frame(fields_frame)
        row4.pack(fill=tk.X, pady=2)
        
        enabled_var = tk.BooleanVar(value=config.get("enabled", True))
        ttk.Checkbutton(row4, text="启用", variable=enabled_var).pack(side=tk.LEFT, padx=10)
        widgets['enabled'] = enabled_var
        
        default_var = tk.BooleanVar(value=config.get("is_default", False))
        ttk.Checkbutton(row4, text="默认", variable=default_var).pack(side=tk.LEFT)
        widgets['is_default'] = default_var
        
        # 存储组件引用
        if not hasattr(self, 'api_widgets'):
            self.api_widgets = {}
        self.api_widgets[f'api_{index}'] = widgets
    
    def create_user_rule_widget(self, parent, rule, index):
        """创建用户规则组件"""
        card = ttk.Frame(parent, bootstyle="light")
        card.pack(fill=tk.X, padx=5, pady=2)
        
        row = ttk.Frame(card)
        row.pack(fill=tk.X, padx=10, pady=5)
        
        # 初始化组件字典
        widgets = {}
        
        ttk.Label(row, text="用户:", width=8).pack(side=tk.LEFT)
        user_entry = ttk.Entry(row, width=15)
        user_entry.pack(side=tk.LEFT, padx=(0, 10))
        user_entry.insert(0, rule.get("name", ""))
        widgets['name'] = user_entry
        
        ttk.Label(row, text="API:", width=8).pack(side=tk.LEFT)
        api_combo = ttk.Combobox(row, width=15, state="readonly")
        api_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # 设置API选项并绑定下拉事件
        def update_api_options(event=None):
            """更新API选项"""
            api_names = [f"{api.get('name', api.get('id', ''))} ({api.get('id', '')})" for api in self.api_configs]
            current_selection = api_combo.get()
            api_combo['values'] = api_names
            # 保持当前选择（如果仍然有效）
            if current_selection in api_names:
                api_combo.set(current_selection)
                
        api_combo.bind('<Button-1>', update_api_options)
        api_combo.bind('<Down>', update_api_options)
        
        # 初始设置
        update_api_options()
        current_api_id = rule.get("api_id", "")
        for i, api in enumerate(self.api_configs):
            if api.get('id') == current_api_id:
                api_combo.current(i)
                break
        widgets['api_combo'] = api_combo
        
        enabled_var = tk.BooleanVar(value=rule.get("enabled", True))
        ttk.Checkbutton(row, text="启用", variable=enabled_var).pack(side=tk.LEFT, padx=10)
        widgets['enabled'] = enabled_var
        
        btn_delete = ttk.Button(row, text="删除", command=lambda: self.delete_user_rule(index), bootstyle="danger")
        btn_delete.pack(side=tk.RIGHT)
        self.attach_hover(btn_delete, "danger")
        
        # 存储组件引用
        if not hasattr(self, 'user_widgets'):
            self.user_widgets = {}
        self.user_widgets[f'user_{index}'] = widgets
    
    def create_group_rule_widget(self, parent, rule, index):
        """创建群组规则组件"""
        card = ttk.Frame(parent, bootstyle="light")
        card.pack(fill=tk.X, padx=5, pady=2)
        
        # 初始化组件字典
        widgets = {}
        
        # 第一行：群组名称和API
        row1 = ttk.Frame(card)
        row1.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(row1, text="群组:", width=8).pack(side=tk.LEFT)
        group_entry = ttk.Entry(row1, width=15)
        group_entry.pack(side=tk.LEFT, padx=(0, 10))
        group_entry.insert(0, rule.get("name", ""))
        widgets['name'] = group_entry
        
        ttk.Label(row1, text="API:", width=8).pack(side=tk.LEFT)
        api_combo = ttk.Combobox(row1, width=15, state="readonly")
        api_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # 设置API选项并绑定下拉事件
        def update_group_api_options(event=None):
            """更新群组API选项"""
            api_names = [f"{api.get('name', api.get('id', ''))} ({api.get('id', '')})" for api in self.api_configs]
            current_selection = api_combo.get()
            api_combo['values'] = api_names
            # 保持当前选择（如果仍然有效）
            if current_selection in api_names:
                api_combo.set(current_selection)
                
        api_combo.bind('<Button-1>', update_group_api_options)
        api_combo.bind('<Down>', update_group_api_options)
        
        # 初始设置
        update_group_api_options()
        current_api_id = rule.get("api_id", "")
        for i, api in enumerate(self.api_configs):
            if api.get('id') == current_api_id:
                api_combo.current(i)
                break
        widgets['api_combo'] = api_combo
        
        # 第二行：选项和删除按钮
        row2 = ttk.Frame(card)
        row2.pack(fill=tk.X, padx=10, pady=2)
        
        enabled_var = tk.BooleanVar(value=rule.get("enabled", True))
        ttk.Checkbutton(row2, text="启用", variable=enabled_var).pack(side=tk.LEFT, padx=(0, 10))
        widgets['enabled'] = enabled_var
        
        at_var = tk.BooleanVar(value=rule.get("at_required", False))
        ttk.Checkbutton(row2, text="需要@", variable=at_var).pack(side=tk.LEFT, padx=(0, 10))
        widgets['at_required'] = at_var
        
        btn_delete = ttk.Button(row2, text="删除", command=lambda: self.delete_group_rule(index), bootstyle="danger")
        btn_delete.pack(side=tk.RIGHT)
        self.attach_hover(btn_delete, "danger")
        
        # 存储组件引用
        if not hasattr(self, 'group_widgets'):
            self.group_widgets = {}
        self.group_widgets[f'group_{index}'] = widgets
    
    def delete_api_config(self, index):
        """删除API配置"""
        if len(self.api_configs) > 1:
            deleted_config = self.api_configs[index]
            del self.api_configs[index]
            self.log_message(f"删除API配置: {deleted_config.get('name', 'Unknown')} ({deleted_config.get('id', 'Unknown')})")
            self.refresh_api_list()
        else:
            self.log_message("删除失败: 至少需要保留一个API配置")
            messagebox.showwarning("警告", "至少需要保留一个API配置")
    
    def delete_user_rule(self, index):
        """删除用户规则"""
        deleted_rule = self.user_rules[index]
        del self.user_rules[index]
        self.log_message(f"删除用户规则: {deleted_rule.get('name', '未命名')}")
        self.refresh_user_rules()
    
    def delete_group_rule(self, index):
        """删除群组规则"""
        deleted_rule = self.group_rules[index]
        del self.group_rules[index]
        self.log_message(f"删除群组规则: {deleted_rule.get('name', '未命名')}")
        self.refresh_group_rules()
    
    def build_config_section(self, parent, section_name, config_keys):
        """构建配置区域的通用方法"""
        card = ttk.Frame(parent, bootstyle="light")
        card.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(card, text=section_name, bootstyle="secondary",
                           font=("微软雅黑", 11, "bold"), padding=(10, 8))
        header.pack(anchor="w")

        main_frame = ttk.Frame(card)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        
        # 为每个标签页创建独立的滚动区域
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        
        # 存储滚动框架引用
        setattr(self, f'{section_name}_scrollable_frame', scrollable_frame)
        setattr(self, f'{section_name}_config_keys', config_keys)

    def create_bot_settings_fields(self):
        """创建机器人设置字段"""
        # 机器人名字
        name_frame = ttk.Frame(self.bot_settings_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="机器人名字:", width=15).pack(side=tk.LEFT)
        self.bot_fields["机器人名字"] = ttk.Entry(name_frame, width=30)
        self.bot_fields["机器人名字"].pack(side=tk.LEFT, padx=5)
        self.add_help_tooltip(name_frame, "机器人名字")
        
        # 管理员
        admin_frame = ttk.Frame(self.bot_settings_frame)
        admin_frame.pack(fill=tk.X, pady=5)
        ttk.Label(admin_frame, text="管理员:", width=15).pack(side=tk.LEFT)
        self.bot_fields["管理员"] = ttk.Entry(admin_frame, width=30)
        self.bot_fields["管理员"].pack(side=tk.LEFT, padx=5)
        self.add_help_tooltip(admin_frame, "管理员")
        
        # 系统提示词
        prompt_frame = ttk.Frame(self.bot_settings_frame)
        prompt_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(prompt_frame, text="系统提示词:", width=15).pack(anchor="nw")
        
        text_frame = ttk.Frame(prompt_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=(100, 0))
        
        self.bot_fields["prompt"] = tk.Text(text_frame, height=8, wrap=tk.WORD, font=("微软雅黑", 9))
        scroll = ttk.Scrollbar(text_frame, command=self.bot_fields["prompt"].yview)
        self.bot_fields["prompt"].configure(yscrollcommand=scroll.set)
        self.bot_fields["prompt"].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 默认API配置
        api_frame = ttk.Frame(self.bot_settings_frame)
        api_frame.pack(fill=tk.X, pady=5)
        ttk.Label(api_frame, text="默认API:", width=15).pack(side=tk.LEFT)
        self.bot_fields["default_api_id"] = ttk.Combobox(api_frame, width=25, state="readonly")
        self.bot_fields["default_api_id"].pack(side=tk.LEFT, padx=5)
        
        # 绑定下拉事件
        def update_bot_api_options(event=None):
            """更新机器人设置的API选项"""
            api_names = [f"{api.get('name', api.get('id', ''))} ({api.get('id', '')})" for api in self.api_configs]
            current_selection = self.bot_fields["default_api_id"].get()
            self.bot_fields["default_api_id"]['values'] = api_names
            # 保持当前选择（如果仍然有效）
            if current_selection in api_names:
                self.bot_fields["default_api_id"].set(current_selection)
                
        self.bot_fields["default_api_id"].bind('<Button-1>', update_bot_api_options)
        self.bot_fields["default_api_id"].bind('<Down>', update_bot_api_options)
        
        self.add_help_tooltip(api_frame, "default_api_id")
        
    def create_memo_fields(self):
        """创建备忘录字段"""
        for widget in self.memo_list_frame.winfo_children():
            widget.destroy()
            
        for i, memo in enumerate(self.memo_items):
            self.create_memo_item_widget(self.memo_list_frame, memo, i)
            
    def create_memo_item_widget(self, parent, memo, index):
        """创建单个备忘录项目组件"""
        card = ttk.Frame(parent, bootstyle="light")
        card.pack(fill=tk.X, padx=5, pady=2)
        
        # 标题行
        title_frame = ttk.Frame(card)
        title_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        ttk.Label(title_frame, text="标题:", width=8).pack(side=tk.LEFT)
        title_entry = ttk.Entry(title_frame, width=20)
        title_entry.pack(side=tk.LEFT, padx=5)
        title_entry.insert(0, memo.get("title", ""))
        
        # 删除按钮
        btn_delete = ttk.Button(title_frame, text="删除", command=lambda: self.delete_memo_item(index), bootstyle="danger")
        btn_delete.pack(side=tk.RIGHT)
        self.attach_hover(btn_delete, "danger")
        
        # 内容区域
        content_frame = ttk.Frame(card)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        ttk.Label(content_frame, text="内容:").pack(anchor="nw")
        
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 0))
        
        content_text = tk.Text(text_frame, height=4, wrap=tk.WORD, font=("微软雅黑", 9))
        text_scroll = ttk.Scrollbar(text_frame, command=content_text.yview)
        content_text.configure(yscrollcommand=text_scroll.set)
        content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        content_text.insert("1.0", memo.get("content", ""))
        
        # 存储组件引用
        self.memo_fields[f"memo_{index}"] = {
            "title": title_entry,
            "content": content_text
        }
        
    def add_memo_item(self):
        """添加新的备忘录项目"""
        new_memo = {
            "title": f"备忘录{len(self.memo_items) + 1}",
            "content": "请输入内容..."
        }
        self.memo_items.append(new_memo)
        self.log_message(f"添加新备忘录: {new_memo['title']}")
        self.create_memo_fields()
        
    def delete_memo_item(self, index):
        """删除备忘录项目"""
        if len(self.memo_items) > 1:
            deleted_memo = self.memo_items[index]
            del self.memo_items[index]
            self.log_message(f"删除备忘录: {deleted_memo.get('title', '未命名')}")
            self.create_memo_fields()
        else:
            self.log_message("删除失败: 至少需要保留一个备忘录项目")
            messagebox.showwarning("警告", "至少需要保留一个备忘录项目")

    def build_control_tab(self, parent):
        """控制页：按钮卡片 + 操作提示"""
        card = ttk.Frame(parent, bootstyle="light")
        card.pack(fill=tk.X, padx=10, pady=10)
        # header = ttk.Label(card, text="机器人控制", bootstyle="secondary",
        #                    font=("微软雅黑", 11, "bold"), padding=(10, 8))
        # header.pack(anchor="w")

        btn_frame = ttk.Frame(card)
        btn_frame.pack(padx=10, pady=(4, 10))

        self.toggle_bot_button = ttk.Button(btn_frame, text="启动机器人", command=self.start_bot, bootstyle="primary")
        btn_restart = ttk.Button(btn_frame, text="重启机器人", command=self.restart_bot, bootstyle="warning")
        btn_activate = ttk.Button(btn_frame, text="激活wxautox", command=self.activate_wxautox, bootstyle="success")

        self.toggle_bot_button.pack(side=tk.LEFT, padx=6, pady=6); self.attach_hover(self.toggle_bot_button, base_style="primary")
        btn_restart.pack(side=tk.LEFT, padx=6, pady=6); self.attach_hover(btn_restart, base_style="warning")
        btn_activate.pack(side=tk.LEFT, padx=6, pady=6); self.attach_hover(btn_activate, base_style="success")

        # 添加日志显示区域
        self.build_logs_section(card)

    def build_logs_section(self, parent):
        """在控制面板中构建日志显示区域"""
        # 日志区域标题
        logs_header = ttk.Frame(parent)
        logs_header.pack(fill=tk.X, padx=10, pady=(20, 5))

        ttk.Label(logs_header, text="实时日志", bootstyle="secondary",
                 font=("微软雅黑", 11, "bold")).pack(side=tk.LEFT)

        # 日志操作按钮
        logs_btn_frame = ttk.Frame(logs_header)
        logs_btn_frame.pack(side=tk.RIGHT)

        btn_clear_logs = ttk.Button(logs_btn_frame, text="清空日志", command=self.clear_logs, bootstyle="secondary")
        btn_clear_logs.pack(side=tk.LEFT, padx=(0, 5))
        self.attach_hover(btn_clear_logs, "secondary")

        btn_export_logs = ttk.Button(logs_btn_frame, text="导出日志", command=self.export_logs, bootstyle="info")
        btn_export_logs.pack(side=tk.LEFT)
        self.attach_hover(btn_export_logs, "info")

        # 异步处理器状态显示
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, padx=10, pady=2)

        ttk.Label(status_frame, text="异步处理器状态:", font=("微软雅黑", 9)).pack(side=tk.LEFT)
        self.async_status_var = tk.StringVar(value="未启动")
        self.async_status_label = ttk.Label(status_frame, textvariable=self.async_status_var, bootstyle="secondary", font=("微软雅黑", 9))
        self.async_status_label.pack(side=tk.LEFT, padx=(5, 0))

        # 日志显示区域
        logs_frame = ttk.Frame(parent)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建文本显示区域
        self.output_text = tk.Text(logs_frame, height=15, wrap=tk.WORD, state=tk.DISABLED,
                                  font=("Consolas", 9), bg="#f8f9fa", fg="#212529")
        scrollbar = ttk.Scrollbar(logs_frame, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 定期更新异步处理器状态
        self.update_async_status()

    def build_logs_tab(self, parent):
        """日志页：实时输出文本"""
    def export_logs(self):
        """导出日志到文件"""
        try:
            from tkinter import filedialog
            import os

            # 获取当前日志内容
            log_content = self.output_text.get("1.0", tk.END)

            if not log_content.strip():
                messagebox.showinfo("提示", "当前没有日志内容可导出")
                return

            # 选择保存位置
            filename = filedialog.asksaveasfilename(
                title="导出日志文件",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialname=f"wxbot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"# dolphin_wxbot 日志导出\n")
                    f.write(f"# 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# ==========================================\n\n")
                    f.write(log_content)

                self.log_message(f"日志已导出到: {filename}")
                messagebox.showinfo("成功", f"日志已成功导出到:\n{filename}")

        except Exception as e:
            error_msg = f"导出日志失败: {str(e)}"
            self.log_message(f"错误: {error_msg}")
            messagebox.showerror("错误", error_msg)

    def detect_wx_library_and_log(self):
        """检测当前使用的wxauto库类型并记录到日志"""
        try:
            # 尝试导入wxauto
            import wxauto

            # 检测是否为wxautox (Plus版本)
            is_wxautox = False
            activation_status = "未知"

            try:
                # 检测Plus版本特有的方法
                from wxauto import WeChat
                wx_temp = WeChat()

                # 检测Plus版本特有方法
                plus_methods = ['GetAllRecentGroups', 'GetFriendDetails', 'Moments', 'IsOnline']
                detected_plus_methods = []

                for method in plus_methods:
                    if hasattr(wx_temp, method):
                        detected_plus_methods.append(method)

                if detected_plus_methods:
                    is_wxautox = True

                    # 尝试调用一个Plus方法来检测激活状态
                    try:
                        # 使用相对安全的方法检测激活状态
                        if hasattr(wx_temp, 'GetAllRecentGroups'):
                            result = wx_temp.GetAllRecentGroups()
                            if result and not isinstance(result, bool):
                                activation_status = "已激活"
                            else:
                                activation_status = "未激活或无权限"
                        else:
                            activation_status = "无法检测"
                    except Exception as e:
                        if "激活" in str(e) or "license" in str(e).lower():
                            activation_status = "未激活"
                        else:
                            activation_status = "检测异常"

            except Exception as e:
                self.log_message(f"检测Plus功能时出错: {str(e)}")

            # 获取版本信息
            version_info = "未知版本"
            try:
                if hasattr(wxauto, '__version__'):
                    version_info = wxauto.__version__
                elif hasattr(wxauto, 'version'):
                    version_info = wxauto.version
            except:
                pass

            # 输出检测结果到日志
            if is_wxautox:
                self.log_message(f"✅ 检测到 wxautox (Plus版本) - 版本: {version_info}")
                self.log_message(f"🔑 激活状态: {activation_status}")
                self.log_message(f"🚀 可用Plus功能: {', '.join(detected_plus_methods)}")
            else:
                self.log_message(f"📦 检测到 wxauto (开源版本) - 版本: {version_info}")
                self.log_message(f"ℹ️  如需更多功能，可升级到wxautox Plus版本")

        except ImportError:
            self.log_message("❌ 未检测到wxauto库，请先安装: pip install wxauto")
        except Exception as e:
            self.log_message(f"⚠️  wxauto库检测异常: {str(e)}")

    def activate_wxautox(self):
        """激活wxautox Plus版本"""
        try:
            # 弹出输入框获取激活码
            modal = ModernModal(self.root, "激活wxautox", "请输入您的wxautox激活码:", "text")
            activation_code = modal.show()

            if not activation_code or not activation_code.strip():
                self.log_message("❌ 激活取消：未输入激活码")
                return

            activation_code = activation_code.strip()
            self.log_message(f"🔑 开始激活wxautox，激活码: {activation_code[:8]}...")

            # 尝试激活
            try:
                import subprocess
                import sys

                # 构建激活命令
                cmd = [sys.executable, "-m", "wxautox", "-a", activation_code]

                self.log_message("⏳ 正在执行激活命令...")

                # 执行激活命令
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=30)

                # 处理激活结果
                if result.returncode == 0:
                    self.log_message("✅ wxautox激活成功！")
                    self.log_message(f"📋 激活输出: {result.stdout}")

                    # 重新检测库状态
                    self.root.after(1000, self.detect_wx_library_and_log)

                    messagebox.showinfo("激活成功", "wxautox已成功激活！\n请查看日志了解详细信息。")
                else:
                    error_msg = result.stderr or result.stdout or "未知错误"
                    self.log_message(f"❌ wxautox激活失败: {error_msg}")
                    messagebox.showerror("激活失败", f"激活失败，错误信息：\n{error_msg}")

            except subprocess.TimeoutExpired:
                self.log_message("⏰ 激活超时：激活命令执行超过30秒")
                messagebox.showerror("激活超时", "激活命令执行超时，请检查网络连接或稍后重试。")

            except FileNotFoundError:
                self.log_message("❌ 激活失败：未找到wxautox命令")
                messagebox.showerror("激活失败", "未找到wxautox命令，请确认已安装wxautox：\npip install wxautox")

            except Exception as e:
                self.log_message(f"❌ 激活异常: {str(e)}")
                messagebox.showerror("激活异常", f"激活过程中发生异常：\n{str(e)}")

        except Exception as e:
            error_msg = f"激活功能异常: {str(e)}"
            self.log_message(f"❌ {error_msg}")
            messagebox.showerror("错误", error_msg)
        
    def clear_logs(self):
        """清空日志显示"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.log_message("日志已清空")
    
    def update_async_status(self):
        """更新异步处理器状态显示"""
        try:
            import wxbot_preview
            if hasattr(wxbot_preview, 'async_message_handler'):
                status = wxbot_preview.async_message_handler.async_handler.get_status()
                if status['is_running']:
                    status_text = f"异步处理器: 运行中 | 队列:{status['queue_size']} | 处理中:{status['processing_count']} | 日志:{status['log_lines']}/{status['max_log_lines']}"
                    self.async_status_label.config(bootstyle="success")
                else:
                    status_text = "异步处理器: 已停止"
                    self.async_status_label.config(bootstyle="danger")
                self.async_status_var.set(status_text)
        except (ImportError, AttributeError):
            self.async_status_var.set("异步处理器: 不可用")
            self.async_status_label.config(bootstyle="secondary")
        
        # 每3秒更新一次状态
        self.root.after(3000, self.update_async_status)


    def attach_hover(self, widget, base_style: str = "secondary"):
        """按钮悬停效果：在 outline 与实心样式间切换
        使用传入的 base_style（如 primary/success/info/warning/danger/secondary）。"""
        base = base_style
        outline = base + "-outline"
        def on_enter(_):
            try:
                widget.config(bootstyle=outline)
            except Exception:
                pass
        def on_leave(_):
            try:
                widget.config(bootstyle=base)
            except Exception:
                pass
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def on_mousewheel(self, event):
        """
        处理鼠标滚轮事件，使配置项区域能够上下滚动
        Windows/macOS 下 event.delta 的值一般为 120 的倍数
        """
        # 由于每个标签页都有自己的滚动事件，这个方法保留但不再使用
        pass
    
    def create_field(self, parent, key, value):
        """
        根据配置项字段名创建对应的输入组件
        处理逻辑：
            - 对于“监听用户列表”、“监听群组列表”：创建可编辑列表控件
            - 对于“prompt”：创建多行文本输入框
            - 对于“群机器人开关”：创建开关控件
            - 对于包含“api”或“备忘录”的字段：创建加密（隐藏输入）文本框
            - 其他字段：创建普通文本输入框
        """
        field_frame = ttk.Frame(parent)
        field_frame.pack(fill=tk.X, pady=5)
        label = ttk.Label(field_frame, text=f"{key}:", width=20)
        label.pack(side=tk.LEFT)
        
        if key in ["监听用户列表", "监听群组列表"]:
            widget = self.create_list_field(field_frame, key, value)
        elif key == "prompt":
            widget = self.create_multiline_field(field_frame, value)
        elif key == "群机器人开关":
            widget = self.create_switch_field(field_frame, key, value)
        elif "api" in key.lower() or "备忘录" in key:
            widget = self.create_secret_field(field_frame, key, value)
        else:
            widget = self.create_text_field(field_frame, key, value)
        
        self.add_help_tooltip(field_frame, key)
        return widget
    
    def add_help_tooltip(self, parent, key):
        """在输入组件旁添加问号图标，鼠标悬停时显示该配置项的说明"""
        tooltip_text = self.tooltips.get(key, "暂无说明")
        help_icon = ttk.Label(parent, text="？", cursor="question_arrow")
        help_icon.pack(side=tk.LEFT, padx=5)
        ModernTooltip(help_icon, tooltip_text)
    
    def create_text_field(self, parent, key, value):
        """创建普通文本输入框"""
        entry = ttk.Entry(parent, width=40)
        entry.insert(0, str(value))
        entry.pack(side=tk.LEFT, expand=True)
        return entry
    
    def create_secret_field(self, parent, key, value):
        """
        创建加密字段输入框：
        使用星号隐藏输入内容，并提供眼睛按钮切换显示模式
        """
        frame = ttk.Frame(parent)
        entry = ttk.Entry(frame, width=35, show="*")
        entry.insert(0, value)
        entry.pack(side=tk.LEFT, expand=True)
        ttk.Button(frame, text="👁", width=2,
                   command=lambda: self.toggle_visibility(entry),
                   bootstyle="link").pack(side=tk.LEFT)
        frame.pack(side=tk.LEFT, expand=True)
        return entry
    
    def toggle_visibility(self, entry):
        """切换加密字段的显示状态：显示或隐藏实际内容"""
        current_show = entry.cget("show")
        entry.config(show="" if current_show == "*" else "*")
    
    def create_switch_field(self, parent, key, value):
        """
        创建开关控件：
        将字符串或布尔值转换为布尔变量，并根据状态显示“启用”或“禁用”
        """
        bool_value = value if isinstance(value, bool) else value.lower() == "true"
        var = tk.BooleanVar(value=bool_value)
        switch = ttk.Checkbutton(
            parent,
            text="启用" if var.get() else "禁用",
            variable=var,
            bootstyle="round-toggle",
            command=lambda: switch.config(text="启用" if var.get() else "禁用")
        )
        switch.pack(side=tk.LEFT)
        return var
    
    def create_list_field(self, parent, key, value):
        """
        创建可编辑列表控件，用于“监听用户列表”和“监听群组列表”
        """
        frame = ttk.Frame(parent)
        listbox = tk.Listbox(frame, width=30, height=4)
        scrollbar = ttk.Scrollbar(frame, orient="vertical")
        for item in value:
            listbox.insert(tk.END, item)
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        
        btn_frame = ttk.Frame(frame)
        ttk.Button(btn_frame, text="＋ 添加", command=lambda: self.add_list_item(listbox),
                   bootstyle="outline-success").pack(fill=tk.X)
        ttk.Button(btn_frame, text="－ 删除", command=lambda: self.remove_list_item(listbox),
                   bootstyle="outline-danger").pack(fill=tk.X, pady=5)
        
        listbox.pack(side=tk.LEFT)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        btn_frame.pack(side=tk.LEFT, padx=5)
        frame.pack(side=tk.LEFT, expand=True)
        return listbox
    
    def add_list_item(self, listbox):
        """弹出对话框添加新项目到列表中"""
        modal = ModernModal(self.root, "添加项目", "请输入新项目：")
        new_item = modal.show()
        if new_item:
            listbox.insert(tk.END, new_item)
    
    def remove_list_item(self, listbox):
        """删除列表中选中的项"""
        try:
            index = listbox.curselection()[0]
            listbox.delete(index)
        except IndexError:
            pass
    
    def create_multiline_field(self, parent, value):
        """创建多行文本输入框，适用于较长文本，如系统提示词"""
        frame = ttk.Frame(parent)
        text = tk.Text(frame, width=50, height=5, wrap=tk.WORD)
        scroll = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.insert("1.0", value)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        return text
    
    def load_config(self):
        """
        加载配置文件：
            1. 如果配置文件不存在，则创建默认配置；
            2. 读取 JSON 数据，并根据各配置项生成对应的UI组件。
        """
        try:
            if not os.path.exists(CONFIG_FILE):
                # 创建新版配置文件结构
                base_config = {
                    # 机器人设置
                    "机器人名字": "dolphin_wxbot",
                    "prompt": "你是一个智能助手，请友好地回答用户问题。",
                    "管理员": "admin",
                    "default_api_id": "api_1",
                    
                    # API配置列表
                    "api_configs": [
                        {
                            "id": "api_1",
                            "name": "默认API配置",
                            "platform": "openai",
                            "api_key": "your-api-key",
                            "base_url": "https://api.openai.com/v1",
                            "enabled": True,
                            "is_default": True
                        }
                    ],
                    
                    # 监听规则
                    "listen_rules": {
                        "global_bot_enabled": True,
                        "default_api_id": "api_1",
                        "user_rules": [],
                        "group_rules": []
                    },
                    
                    # 备忘录数据
                    "memo_data": [
                        {"title": "备忘录1", "content": "请输入重要信息..."},
                        {"title": "备忘录2", "content": "请输入其他信息..."}
                    ]
                }
                
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(base_config, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("提示", f"已创建默认配置文件：\n{os.path.abspath(CONFIG_FILE)}\n请根据需求修改配置")
                
            # 读取配置文件
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            
            # 加载各个模块的配置
            self.load_api_configs()
            self.load_bot_settings()
            self.load_listen_rules()
            self.load_memo_data()
            
        except json.JSONDecodeError:
            messagebox.showerror("配置文件错误", "配置文件格式不正确，请检查JSON语法")
        except Exception as e:
            messagebox.showerror("加载错误", f"加载配置失败: {str(e)}\n{traceback.format_exc()}")
    
    def load_api_configs(self):
        """加载API配置"""
        self.api_configs = self.config.get('api_configs', [])
        if not self.api_configs:
            # 兼容旧版配置
            self.api_configs = [{
                "id": "api_1",
                "name": "默认API配置",
                "platform": "openai",
                "api_key": self.config.get('api_key', ''),
                "base_url": self.config.get('base_url', ''),
                "enabled": True,
                "is_default": True
            }]
        self.refresh_api_list()
    
    def load_bot_settings(self):
        """加载机器人设置"""
        if hasattr(self, 'bot_fields'):
            if "机器人名字" in self.bot_fields:
                self.bot_fields["机器人名字"].delete(0, tk.END)
                self.bot_fields["机器人名字"].insert(0, self.config.get("机器人名字", ""))
            
            if "管理员" in self.bot_fields:
                self.bot_fields["管理员"].delete(0, tk.END)
                self.bot_fields["管理员"].insert(0, self.config.get("管理员", ""))
            
            if "prompt" in self.bot_fields:
                self.bot_fields["prompt"].delete("1.0", tk.END)
                self.bot_fields["prompt"].insert("1.0", self.config.get("prompt", ""))
            
            if "default_api_id" in self.bot_fields:
                # 更新API选择框
                api_names = [f"{api.get('name', api.get('id', ''))} ({api.get('id', '')})" 
                           for api in self.api_configs]
                self.bot_fields["default_api_id"]["values"] = api_names
                default_api_id = self.config.get("default_api_id", "")
                for i, api in enumerate(self.api_configs):
                    if api.get('id') == default_api_id:
                        self.bot_fields["default_api_id"].current(i)
                        break
    
    def load_listen_rules(self):
        """加载监听规则"""
        listen_rules = self.config.get('listen_rules', {})

        if hasattr(self, 'global_bot_switch'):
            self.global_bot_switch.set(listen_rules.get('global_bot_enabled', True))

        if hasattr(self, 'default_api_var'):
            self.default_api_var.set(listen_rules.get('default_api_id', ''))

        # 加载消息类型过滤配置
        message_filter = listen_rules.get('message_types_filter', {})

        if hasattr(self, 'message_filter_enabled'):
            self.message_filter_enabled.set(message_filter.get('enabled', True))

        if hasattr(self, 'message_type_vars'):
            allowed_types = message_filter.get('allowed_types', ["text", "link", "location", "image", "file", "voice", "video", "emotion"])
            for type_key, var in self.message_type_vars.items():
                var.set(type_key in allowed_types)

            # 更新UI状态
            self.on_message_filter_toggle()

        self.user_rules = listen_rules.get('user_rules', [])
        self.group_rules = listen_rules.get('group_rules', [])

        if hasattr(self, 'users_list_frame'):
            self.refresh_user_rules()
        if hasattr(self, 'groups_list_frame'):
            self.refresh_group_rules()
    
    def load_memo_data(self):
        """加载备忘录数据"""
        self.memo_items = self.config.get('memo_data', [
            {"title": "备忘录1", "content": "请输入重要信息..."},
            {"title": "备忘录2", "content": "请输入其他信息..."}
        ])
        
        if hasattr(self, 'memo_list_frame'):
            self.create_memo_fields()
    
    def save_config(self):
        """
        保存当前配置：
            遍历各UI组件，获取用户输入的最新值，
            保存为 JSON 格式写回配置文件，并刷新界面。
        """
        try:
            new_config = {}
            for key, widget in self.fields.items():
                if key in ["监听用户列表", "监听群组列表"]:
                    new_config[key] = list(widget.get(0, tk.END))
                elif key == "群机器人开关":
                    new_config[key] = "True" if widget.get() else "False"
                elif isinstance(widget, tk.Text):
                    new_config[key] = widget.get("1.0", tk.END).strip()
                else:
                    new_config[key] = widget.get()
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(new_config, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("成功", "配置已保存，建议重启机器人以生效")
            self.load_config()
        except Exception as e:
            messagebox.showerror("保存错误", f"保存配置失败: {str(e)}")
    
    def start_bot(self):
        """
        启动机器人：
            1. 如果已有机器人线程在运行，则提示已运行；
            2. 启动新线程运行 wxbot_service.wxbot_service_main()，
               并将线程的标准输出重定向到队列中。
        """
        try:
            if self.bot_thread and self.bot_thread.is_alive():
                self.status_var.set("状态：机器人已在运行")
                return
            # 启动前先清空输出区域
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.config(state=tk.DISABLED)
            
            def run_bot():
                try:
                    # 重定向标准输出和错误输出到队列
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    sys.stdout = QueueWriter(self.output_queue)
                    sys.stderr = QueueWriter(self.output_queue)
                    # 如需COM初始化，可导入 pythoncom（仅在需要时）
                    try:
                        import pythoncom
                        pythoncom.CoInitialize()
                    except ImportError:
                        pass
                    wxbot_preview.start_bot()
                except Exception as e:
                    print("机器人运行时出错：", e)
                finally:
                    try:
                        import pythoncom
                        pythoncom.CoUninitialize()
                    except ImportError:
                        pass
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
            
            self.bot_thread = threading.Thread(target=run_bot, daemon=True)
            self.bot_thread.start()
            # 修改状态
            self.status_var.set("状态：机器人启动成功")
            self.toggle_bot_button.config(text="停止机器人", command=self.stop_bot, bootstyle="danger")
            self.log_message("机器人服务已启动")
        except Exception as e:
            error_msg = f"启动失败：{str(e)}\n{traceback.format_exc()}"
            self.status_var.set("状态：启动失败")
            messagebox.showerror("启动错误", error_msg)
    
    def stop_bot(self):
        """
        关闭机器人：
            如果机器人线程正在运行，则使用 _async_raise 抛出 KeyboardInterrupt 异常停止线程，
            并更新状态显示。
        """
        try:
            if self.bot_thread and self.bot_thread.is_alive():
                # _async_raise(self.bot_thread.ident, KeyboardInterrupt)
                # self.bot_thread.join(timeout=10)
                wxbot_preview.stop_bot() # 调用 wxbot_preview 模块的停止函数
                self.status_var.set("状态：机器人已关闭")
                self.toggle_bot_button.config(text="启动机器人", command=self.start_bot, bootstyle="primary")
                self.bot_thread = None
                self.log_message("机器人服务已停止")
            else:
                self.status_var.set("状态：没有运行中的机器人")
        except Exception as e:
            error_msg = f"关闭失败：{str(e)}\n{traceback.format_exc()}"
            self.status_var.set("状态：关闭失败")
            messagebox.showerror("关闭错误", error_msg)
    
    def restart_bot(self):
        """先关闭机器人，再启动机器人"""
        self.stop_bot()
        self.start_bot()
    
    def update_output(self):
        """
        定时检查输出队列和异步处理器日志，将机器人线程的输出显示在文本框中
        每100毫秒检查一次
        """
        try:
            # 检查机器人线程输出队列
            while not self.output_queue.empty():
                text = self.output_queue.get_nowait()
                self.output_text.config(state=tk.NORMAL)
                self.output_text.insert(tk.END, text)
                self.output_text.see(tk.END)
                self.output_text.config(state=tk.DISABLED)
            
            # 检查异步处理器日志（如果可用）
            try:
                import wxbot_preview
                if hasattr(wxbot_preview, 'async_message_handler'):
                    # 获取新的日志条目
                    logs = wxbot_preview.async_message_handler.async_handler.get_logs(10)  # 获取最近10条
                    if logs and hasattr(self, '_last_async_log_count'):
                        new_logs = logs[self._last_async_log_count:]
                        if new_logs:
                            self.output_text.config(state=tk.NORMAL)
                            for log in new_logs:
                                self.output_text.insert(tk.END, log + "\n")
                            self.output_text.see(tk.END)
                            self.output_text.config(state=tk.DISABLED)
                    
                    self._last_async_log_count = len(logs)
            except (ImportError, AttributeError):
                pass
                
        except queue.Empty:
            pass
        self.root.after(100, self.update_output)

def main():
    """程序入口函数：创建窗口并启动主事件循环"""
    root = ttk.Window()
    app = ConfigEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
