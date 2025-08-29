# 微信机器人链接处理功能

## 功能概述

当监听的微信收到链接类型消息时，系统会自动提取链接的标题与URL，并将这些信息发送给API接口进行处理，而不影响现有的文本消息处理流程。

## 实现原理

### 1. 消息类型识别
- 在 `message_handle_callback()` 函数中，系统会检查消息类型
- 如果 `msg.type == 'link'`，则调用专门的链接处理函数 `process_link_message()`
- 其他类型消息继续使用原有的 `process_message()` 函数

### 2. 链接信息提取
- 从消息对象中提取链接URL（优先使用 `message.url` 属性）
- 如果没有直接的URL属性，则从消息内容中使用正则表达式提取
- 使用 `link_processor` 模块访问链接并提取网页标题

### 3. API消息构建
- 将提取的标题和URL格式化为特定格式：
```
用户分享了一个链接：
标题: [网页标题]
URL: [链接地址]
```

### 4. 异步处理
- 创建临时消息对象，包含格式化后的链接信息
- 发送到异步消息处理队列，与文本消息使用相同的API调用机制

## 文件结构

```
dolphin_wxbot/
├── link_processor.py          # 链接处理核心模块
├── wxbot_preview.py          # 主要修改：添加链接消息处理
├── async_message_handler.py  # 异步处理（保持原有逻辑）
├── test_link_processor.py    # 链接处理功能测试
├── test_message_types.py     # 消息类型处理测试
└── requirements.txt          # 新增依赖包
```

## 核心代码修改

### 1. wxbot_preview.py
```python
def message_handle_callback(msg, chat):
    if isinstance(msg, FriendMessage):
        # 检查消息类型，如果是链接类型则特殊处理
        if hasattr(msg, 'type') and msg.type == 'link':
            process_link_message(chat, msg)  # 链接专用处理
        else:
            process_message(chat, msg)       # 原有文本处理
```

### 2. 新增 process_link_message() 函数
- 专门处理链接类型消息
- 提取链接URL和标题
- 构建API消息格式
- 发送到异步处理队列

## 新增依赖

在 `requirements.txt` 中添加了以下依赖包：
- `requests` - 用于HTTP请求获取网页内容
- `beautifulsoup4` - 用于解析HTML提取标题
- `lxml` - BeautifulSoup的解析器

## 功能特点

### ✅ 优点
1. **专门处理**：链接消息有独立的处理流程
2. **不影响现有功能**：文本消息处理保持不变
3. **智能提取**：自动获取网页标题，提供更丰富的上下文
4. **异步处理**：使用现有的异步队列，不阻塞主线程
5. **错误处理**：网络异常时有降级处理机制

### 🔄 处理流程
```
链接消息 → 类型识别 → 链接提取 → 标题获取 → 格式化 → API处理 → 回复用户
文本消息 → 类型识别 → 直接处理 → API处理 → 回复用户
```

## 使用示例

### 链接消息处理
当用户发送链接时：
```
输入：https://www.python.org
处理：提取标题 "Welcome to Python.org"
发送给API：
用户分享了一个链接：
标题: Welcome to Python.org
URL: https://www.python.org
```

### 文本消息处理（不变）
当用户发送文本时：
```
输入：你好，今天天气怎么样？
处理：直接使用原始文本
发送给API：你好，今天天气怎么样？
```

## 测试方法

运行测试脚本验证功能：
```bash
# 测试链接处理功能
python test_link_processor.py

# 测试消息类型路由
python test_message_types.py
```

## 配置说明

无需额外配置，功能会自动启用。链接处理使用与文本消息相同的API配置和监听规则。

## 注意事项

1. 需要网络连接才能提取链接标题
2. 某些网站可能有反爬虫机制，导致标题提取失败
3. 提取标题有超时机制（默认10秒），避免长时间等待
4. 如果标题提取失败，会使用 "无法获取标题" 作为默认值
