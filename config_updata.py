'''
siver_wxbot配置修改器
作者：https://siver.top
'''


import json
import os
import tkinter as tk
from tkinter import messagebox, ttk
import ttkbootstrap as ttk
from tkinter import simpledialog
import traceback

CONFIG_FILE = "config.json"

class Tooltip:
    """自定义悬浮提示类"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        """显示提示信息"""
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(
            self.tooltip_window, 
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            padding=5
        )
        label.pack()

    def hide_tooltip(self, event=None):
        """隐藏提示信息"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class ConfigEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("siver_wxbot 配置管理器")
        self.root.geometry("800x800")
        
        # 提示信息配置
        self.tooltips = {
            "listen_list": "需要监听的用户列表（每行一个用户ID）,有备注填备注，无备注填wx昵称，管理员无需填在这",
            "api_key": "在此处填写从开放平台获取的API密钥",
            "base_url": "填写开放平台的接口网址/链接",
            "AtMe": "机器人在群中被@的名字，建议复制粘贴过来，微信@有特殊符号",
            "cmd": "机器人账号wx对管理员账号wx的备注名",
            "bot_name": "机器人wx被问你是谁的时候回复的名字",
            "model1": "你在开发平台要调用的模型名称，可以填四个",
            "model2": "你在开发平台要调用的模型名称，可以填四个",
            "model3": "你在开发平台要调用的模型名称，可以填四个",
            "model4": "你在开发平台要调用的模型名称，可以填四个",
            "group": "机器人监听的群组名称",
            "group_switch": "启用/禁用群机器人功能",
            "备忘录1": "随意填写，备忘用",
            "备忘录2": "随意填写，备忘用"
        }
        
        # 初始化样式
        self.style = ttk.Style(theme="minty")
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        # 主容器
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 可滚动配置面板
        self.canvas = tk.Canvas(main_frame)
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 操作按钮面板
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame, 
            text="保存配置",
            command=self.save_config,
            bootstyle="success"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="重新加载",
            command=self.load_config,
            bootstyle="info"
        ).pack(side=tk.LEFT, padx=5)

    def create_field(self, parent, key, value):
        """创建配置项输入组件"""
        field_frame = ttk.Frame(parent)
        field_frame.pack(fill=tk.X, pady=5)

        # 字段标签
        label = ttk.Label(field_frame, text=f"{key}:", width=20)
        label.pack(side=tk.LEFT)

        # 动态创建输入组件
        if key == "listen_list":
            widget = self.create_list_field(field_frame, key, value)
        elif key == "group_switch":
            widget = self.create_switch_field(field_frame, key, value)
        elif "api" in key.lower() or "备忘录" in key.lower():
            widget = self.create_secret_field(field_frame, key, value)
        else:
            widget = self.create_text_field(field_frame, key, value)

        # 添加帮助提示
        self.add_help_tooltip(field_frame, key)
        return widget

    def add_help_tooltip(self, parent, key):
        """添加问号提示"""
        tooltip_text = self.tooltips.get(key, "暂无详细说明")
        help_icon = ttk.Label(parent, text="？？", cursor="question_arrow")
        help_icon.pack(side=tk.LEFT, padx=5)
        Tooltip(help_icon, tooltip_text)

    def create_text_field(self, parent, key, value):
        """创建普通文本输入框"""
        entry = ttk.Entry(parent, width=40)
        entry.insert(0, str(value))
        entry.pack(side=tk.LEFT, expand=True)
        return entry

    def create_secret_field(self, parent, key, value):
        """创建加密字段输入框"""
        frame = ttk.Frame(parent)
        
        # 输入框
        entry = ttk.Entry(frame, width=35, show="*")
        entry.insert(0, value)
        entry.pack(side=tk.LEFT, expand=True)
        
        # 显示切换按钮
        ttk.Button(
            frame,
            text="👁",
            width=2,
            command=lambda: self.toggle_visibility(entry),
            bootstyle="link"
        ).pack(side=tk.LEFT)
        
        frame.pack(side=tk.LEFT, expand=True)
        return entry

    def toggle_visibility(self, entry):
        """切换密码可见性"""
        current_show = entry.cget("show")
        entry.config(show="" if current_show == "*" else "*")

    def create_switch_field(self, parent, key, value):
        """创建开关组件"""
        # var = tk.BooleanVar(value=value)
        # 处理字符串类型配置值
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
        """创建可编辑列表"""
        frame = ttk.Frame(parent)
        
        # 列表框
        listbox = tk.Listbox(frame, width=30, height=4)
        scrollbar = ttk.Scrollbar(frame, orient="vertical")
        
        for item in value:
            listbox.insert(tk.END, item)
            
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        
        # 操作按钮
        btn_frame = ttk.Frame(frame)
        ttk.Button(
            btn_frame,
            text="＋ 添加",
            command=lambda: self.add_list_item(listbox),
            bootstyle="outline-success"
        ).pack(fill=tk.X)
        
        ttk.Button(
            btn_frame,
            text="－ 删除",
            command=lambda: self.remove_list_item(listbox),
            bootstyle="outline-danger"
        ).pack(fill=tk.X, pady=5)

        # 布局组件
        listbox.pack(side=tk.LEFT)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        btn_frame.pack(side=tk.LEFT, padx=5)
        frame.pack(side=tk.LEFT, expand=True)
        return listbox

    def add_list_item(self, listbox):
        """添加列表项"""
        new_item = simpledialog.askstring("添加项目", "请输入新项目:")
        if new_item:
            listbox.insert(tk.END, new_item)

    def remove_list_item(self, listbox):
        """删除列表项"""
        try:
            index = listbox.curselection()[0]
            listbox.delete(index)
        except IndexError:
            pass

    def load_config(self):
        """加载配置文件"""
        try:
            # 清除旧组件
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            # 增加文件存在性检查提示
            if not os.path.exists(CONFIG_FILE):
                # 创建默认配置前添加提示
                response = messagebox.askyesno(
                    "配置文件不存在",
                    "未找到配置文件，是否创建默认配置？",
                    icon="question"
                )
                if not response:
                    self.root.destroy()
                    return

                base_config = {
                    "鼠标放在？？上查看提示": "鼠标放在？？上查看提示",
                    "listen_list": [],
                    "api_key": "your-api",
                    "base_url": "https://api.siliconflow.cn/v1",
                    "AtMe": "@Siver. ",
                    "cmd": "(管理员备注)",
                    "bot_name": "DeepSeek.",
                    "model1": "Pro/deepseek-ai/DeepSeek-R1",
                    "model2": "Pro/deepseek-ai/DeepSeek-V3",
                    "model3": "deepseek-r1-250120",
                    "model4": "deepseek-v3-241226",
                    "group": "wxbot_test",
                    "group_switch": "False",
                    "备忘录1": "硅基流动: Pro/deepseek-ai/DeepSeek-R1 / Pro/deepseek-ai/DeepSeek-R1",
                    "备忘录2": "火山引擎: deepseek-r1-250120 / deepseek-v3-241226"
                }
                with open(CONFIG_FILE, "w") as f:
                    json.dump(base_config, f, indent=4)
                
                # 新增提示
                messagebox.showinfo(
                    "提示", 
                    f"已创建默认配置文件：\n{os.path.abspath(CONFIG_FILE)}\n请根据需求修改配置"
                )

            # 修改异常提示内容
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self.config = json.load(f)

            # 动态创建配置项
            self.fields = {}
            for key, value in self.config.items():
                self.fields[key] = self.create_field(self.scrollable_frame, key, value)

        except json.JSONDecodeError:
            messagebox.showerror(
                "配置文件错误",
                "配置文件格式不正确，请检查JSON语法\n建议使用文本编辑器检查格式"
            )
        except Exception as e:
            # 强化错误提示
            messagebox.showerror(
                "初始化错误",
                f"配置加载失败: {str(e)}\n\n可能原因：\n1. 文件权限不足\n2. 文件被其他程序占用\n3. 磁盘空间不足",
                detail=traceback.format_exc()
            )

    def save_config(self):
        """保存配置文件"""
        try:
            new_config = {}
            for key, widget in self.fields.items():
                # 处理不同类型组件的数据获取
                if key == "listen_list":
                    new_config[key] = list(widget.get(0, tk.END))
                elif key == "group_switch":
                    # new_config[key] = widget.get()
                    new_config[key] = "True" if widget.get() else "False"
                elif isinstance(widget, ttk.Checkbutton):
                    new_config[key] = widget.instate(["selected"])
                else:
                    new_config[key] = widget.get()

            # 写入配置文件
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(new_config, f, ensure_ascii=False, indent=4)

            messagebox.showinfo("操作成功", "配置已成功保存！")
            self.load_config()  # 刷新界面

        except Exception as e:
            messagebox.showerror("保存错误", f"配置保存失败: {str(e)}")

def main():
    root = ttk.Window()
    app = ConfigEditor(root)
    root.mainloop()

main()
