'''
siver_wxbot配置修改器
作者：https://siver.top
'''

# 导入必要的库
import json  # 用于处理JSON格式的配置文件
import os    # 处理文件路径和存在性检查
import tkinter as tk  # GUI基础库
from tkinter import messagebox, ttk  # 弹窗和主题控件
import ttkbootstrap as ttk  # 美化版tkinter组件
from tkinter import simpledialog  # 简单输入对话框
import traceback  # 异常堆栈跟踪

CONFIG_FILE = "config.json"  # 配置文件名常量

class Tooltip:
    """自定义悬浮提示类"""
    def __init__(self, widget, text):
        # 初始化工具提示绑定到指定组件
        self.widget = widget  # 需要绑定提示的GUI组件
        self.text = text      # 提示文本内容
        self.tooltip_window = None  # 提示窗口引用
        # 绑定鼠标事件
        self.widget.bind("<Enter>", self.show_tooltip)  # 鼠标进入时显示
        self.widget.bind("<Leave>", self.hide_tooltip)  # 鼠标离开时隐藏

    def show_tooltip(self, event=None):
        """显示提示信息"""
        # 计算提示窗口位置（相对屏幕坐标）
        x = self.widget.winfo_rootx() + 25  # X坐标偏移25像素
        y = self.widget.winfo_rooty() + 25  # Y坐标偏移25像素

        # 创建顶层无边框窗口
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # 移除窗口装饰
        self.tooltip_window.wm_geometry(f"+{x}+{y}")   # 设置窗口位置

        # 创建带样式的提示标签
        label = ttk.Label(
            self.tooltip_window, 
            text=self.text,
            background="#ffffe0",  # 浅黄色背景
            relief="solid",        # 实线边框
            borderwidth=1,         # 边框宽度
            padding=5              # 内边距
        )
        label.pack()

    def hide_tooltip(self, event=None):
        """隐藏提示信息"""
        if self.tooltip_window:
            self.tooltip_window.destroy()  # 销毁提示窗口
            self.tooltip_window = None     # 清除引用

class ConfigEditor:
    def __init__(self, root):
        # 主窗口初始化
        self.root = root
        self.root.title("siver_wxbot 配置管理器V1.1")  # 设置窗口标题
        self.root.geometry("800x800")             # 初始窗口尺寸800x800像素
        
        # 字段说明提示字典
        self.tooltips = {
            "listen_list": "需要监听的用户列表（每行一个用户ID）...",  # 列表字段说明
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
            "备忘录2": "随意填写，备忘用",
            "prompt": "系统提示词，用于定义机器人的基本行为和回复规则",  # 新增提示
        }
        
        # GUI样式初始化
        self.style = ttk.Style(theme="minty")  # 使用ttkbootstrap的minty主题
        self.setup_ui()    # 调用界面构建方法
        self.load_config() # 加载配置文件数据

    def setup_ui(self):
        """构建主界面布局"""
        # 主容器框架
        main_frame = ttk.Frame(self.root)  # 创建主容器
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)  # 填充整个窗口并留边距
        
        # 滚动区域组件
        self.canvas = tk.Canvas(main_frame)  # 创建画布用于滚动
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)  # 垂直滚动条
        self.scrollable_frame = ttk.Frame(self.canvas)  # 可滚动内容容器
        
        # 配置滚动区域自适应
        self.scrollable_frame.bind(
            "<Configure>",  # 当框架尺寸变化时触发
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")  # 更新画布滚动区域
            )
        )
        
        # 画布布局设置
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")  # 将框架嵌入画布
        self.canvas.configure(yscrollcommand=self.scrollbar.set)  # 连接滚动条与画布
        
        # 组件布局
        self.canvas.pack(side="left", fill="both", expand=True)  # 画布靠左填充
        self.scrollbar.pack(side="right", fill="y")  # 滚动条靠右垂直填充

        # 操作按钮面板
        btn_frame = ttk.Frame(self.root)  # 创建按钮容器
        btn_frame.pack(pady=10)  # 下方留白10像素
        
        # 保存按钮
        ttk.Button(
            btn_frame, 
            text="保存配置",
            command=self.save_config,  # 绑定保存方法
            bootstyle="success"  # 使用成功样式（绿色）
        ).pack(side=tk.LEFT, padx=5)  # 靠左排列，间距5像素
        
        # 重载按钮
        ttk.Button(
            btn_frame,
            text="重新加载",
            command=self.load_config,  # 绑定重载方法
            bootstyle="info"  # 使用信息样式（蓝色）
        ).pack(side=tk.LEFT, padx=5)

    def create_field(self, parent, key, value):
        """创建配置项输入组件"""
        field_frame = ttk.Frame(parent)  # 单项容器
        field_frame.pack(fill=tk.X, pady=5)  # 横向填充，纵向间距5像素

        # 字段标签
        label = ttk.Label(field_frame, text=f"{key}:", width=20)  # 固定宽度标签
        label.pack(side=tk.LEFT)  # 靠左排列

        # 动态创建输入组件
        if key == "listen_list":
            widget = self.create_list_field(field_frame, key, value)  # 列表类型字段
        elif key == "prompt":  # 新增多行输入处理
            widget = self.create_multiline_field(field_frame, value)
        elif key == "group_switch":
            widget = self.create_switch_field(field_frame, key, value)  # 开关类型字段
        elif "api" in key.lower() or "备忘录" in key.lower():
            widget = self.create_secret_field(field_frame, key, value)  # 加密字段
        else:
            widget = self.create_text_field(field_frame, key, value)  # 普通文本字段

        # 添加帮助提示图标
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
        frame = ttk.Frame(parent)  # 创建容器框架
        
        # 输入框
        entry = ttk.Entry(frame, width=35, show="*")  # 使用星号隐藏输入
        entry.insert(0, value)  # 初始化输入内容
        entry.pack(side=tk.LEFT, expand=True)  # 靠左布局并扩展
        
        # 显示切换按钮
        ttk.Button(
            frame,
            text="👁",  # 眼睛图标
            width=2,
            command=lambda: self.toggle_visibility(entry),  # 绑定点击事件
            bootstyle="link"  # 无边框按钮样式
        ).pack(side=tk.LEFT)  # 按钮靠左排列
        
        frame.pack(side=tk.LEFT, expand=True)  # 整体框架布局
        return entry  # 返回输入框引用

    def toggle_visibility(self, entry):
        """切换密码可见性"""
        current_show = entry.cget("show")  # 获取当前显示模式
        entry.config(show="" if current_show == "*" else "*")  # 切换星号显示

    def create_switch_field(self, parent, key, value):
        """创建开关组件"""
        # 处理字符串类型配置值
        bool_value = value if isinstance(value, bool) else value.lower() == "true"
        var = tk.BooleanVar(value=bool_value)  # 创建布尔变量
        switch = ttk.Checkbutton(
            parent,
            text="启用" if var.get() else "禁用",  # 动态按钮文本
            variable=var,  # 绑定变量
            bootstyle="round-toggle",  # 圆形切换样式
            command=lambda: switch.config(text="启用" if var.get() else "禁用")  # 状态变更回调
        )
        switch.pack(side=tk.LEFT)  # 靠左布局
        return var  # 返回变量引用

    def create_list_field(self, parent, key, value):
        """创建可编辑列表"""
        frame = ttk.Frame(parent)  # 列表容器框架
        
        # 列表框
        listbox = tk.Listbox(frame, width=30, height=4)  # 固定尺寸列表框
        scrollbar = ttk.Scrollbar(frame, orient="vertical")  # 垂直滚动条
        
        for item in value:  # 遍历初始值
            listbox.insert(tk.END, item)  # 逐项插入
            
        listbox.config(yscrollcommand=scrollbar.set)  # 绑定滚动条
        scrollbar.config(command=listbox.yview)  # 设置滚动回调
        
        # 操作按钮
        btn_frame = ttk.Frame(frame)  # 按钮容器
        ttk.Button(
            btn_frame,
            text="＋ 添加",
            command=lambda: self.add_list_item(listbox),  # 绑定添加方法
            bootstyle="outline-success"  # 绿色轮廓按钮
        ).pack(fill=tk.X)  # 横向填充
        
        ttk.Button(
            btn_frame,
            text="－ 删除",
            command=lambda: self.remove_list_item(listbox),  # 绑定删除方法
            bootstyle="outline-danger"  # 红色轮廓按钮
        ).pack(fill=tk.X, pady=5)  # 带垂直间距

        # 布局组件
        listbox.pack(side=tk.LEFT)  # 列表框靠左
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)  # 滚动条填充垂直方向
        btn_frame.pack(side=tk.LEFT, padx=5)  # 按钮容器带水平间距
        frame.pack(side=tk.LEFT, expand=True)  # 整体框架布局
        return listbox  # 返回列表框引用

    def add_list_item(self, listbox):
        """添加列表项"""
        new_item = simpledialog.askstring("添加项目", "请输入新项目:")  # 弹出输入对话框
        if new_item:  # 验证输入内容
            listbox.insert(tk.END, new_item)  # 插入到列表末尾

    def remove_list_item(self, listbox):
        """删除列表项"""
        try:
            index = listbox.curselection()[0]  # 获取选中项的索引
            listbox.delete(index)  # 删除指定项
        except IndexError:  # 处理未选中项的情况
            pass  # 静默失败

    def create_multiline_field(self, parent, value):
        """创建多行文本输入框"""
        frame = ttk.Frame(parent)
        
        # 带滚动条的文本框
        text = tk.Text(frame, width=50, height=5, wrap=tk.WORD)
        scroll = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.insert("1.0", value)
        
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        return text

    def load_config(self):
        """加载配置文件"""
        try:
            # 清除旧组件
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()  # 遍历删除可滚动区域所有子组件

            # 增加文件存在性检查提示
            if not os.path.exists(CONFIG_FILE):
                # 创建默认配置前添加提示
                response = messagebox.askyesno(
                    "配置文件不存在",
                    "未找到配置文件，是否创建默认配置？",
                    icon="question"  # 显示问号图标
                )
                if not response:  # 用户选择否
                    self.root.destroy()  # 关闭窗口
                    return

                # 创建默认配置字典
                base_config = {
                    "鼠标放在？？上查看提示": "鼠标放在？？上查看提示",  # 引导性提示
                    "listen_list": [],  # 空监听列表
                    "api_key": "your-api",  # 默认API密钥占位符
                    "base_url": "https://api.siliconflow.cn/v1",  # 默认接口地址
                    "model1": "Pro/deepseek-ai/DeepSeek-R1",
                    "model2": "Pro/deepseek-ai/DeepSeek-V3",
                    "model3": "deepseek-r1-250120",
                    "model4": "deepseek-v3-241226",
                    "prompt": "你是一个乐于助人的AI",  # 新增提示
                    "AtMe": "@Siver. ",
                    "cmd": "(管理员备注)",
                    "bot_name": "DeepSeek.",
                    "group": "wxbot_test",
                    "group_switch": "False",
                    "备忘录1": "硅基流动: Pro/deepseek-ai/DeepSeek-R1 / Pro/deepseek-ai/DeepSeek-R1",
                    "备忘录2": "火山引擎: deepseek-r1-250120 / deepseek-v3-241226",
                    
                }
                with open(CONFIG_FILE, "w") as f:
                    json.dump(base_config, f, indent=4)  # 美化格式写入
                
                # 新增创建成功提示
                messagebox.showinfo(
                    "提示", 
                    f"已创建默认配置文件：\n{os.path.abspath(CONFIG_FILE)}\n请根据需求修改配置"
                )

            # 读取并解析配置文件
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self.config = json.load(f)  # 加载为字典对象

            # 动态创建配置项
            self.fields = {}  # 存储组件引用的字典
            for key, value in self.config.items():
                # 为每个配置项创建对应GUI组件
                self.fields[key] = self.create_field(self.scrollable_frame, key, value)

        except json.JSONDecodeError:  # JSON解析异常处理
            messagebox.showerror(
                "配置文件错误",
                "配置文件格式不正确，请检查JSON语法\n建议使用文本编辑器检查格式"
            )
        except Exception as e:  # 其他异常捕获
            # 显示详细错误信息
            messagebox.showerror(
                "初始化错误",
                f"配置加载失败: {str(e)}\n\n可能原因：\n1. 文件权限不足\n2. 文件被其他程序占用\n3. 磁盘空间不足",
                detail=traceback.format_exc()  # 显示完整堆栈跟踪
            )

    def save_config(self):
        """保存配置文件"""
        try:
            new_config = {}  # 新配置字典
            for key, widget in self.fields.items():
                # 根据组件类型获取值
                if key == "listen_list":
                    new_config[key] = list(widget.get(0, tk.END))  # 获取列表框全部内容
                elif key == "group_switch":
                    new_config[key] = "True" if widget.get() else "False"  # 转换布尔值为字符串
                elif isinstance(widget, ttk.Checkbutton):
                    new_config[key] = widget.instate(["selected"])  # 检查按钮状态
                elif isinstance(widget, tk.Text):  # 处理多行文本
                    new_config[key] = widget.get("1.0", tk.END).strip()
                else:
                    new_config[key] = widget.get()  # 获取输入框内容

            # 写入配置文件
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(new_config, f, ensure_ascii=False, indent=4)  # 保留中文原格式

            messagebox.showinfo("操作成功", "配置已成功保存！")
            self.load_config()  # 重新加载刷新界面

        except Exception as e:  # 保存异常处理
            messagebox.showerror("保存错误", f"配置保存失败: {str(e)}")

def main():
    """程序入口函数"""
    root = ttk.Window()  # 创建主窗口
    app = ConfigEditor(root)  # 初始化配置编辑器实例
    root.mainloop()  # 启动GUI事件循环
    

main()  # 执行主函数