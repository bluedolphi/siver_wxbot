# wxauto 完整使用说明文档

## 目录
1. [什么是 wxauto](#什么是-wxauto)
2. [环境配置和安装](#环境配置和安装)
3. [快速开始](#快速开始)
4. [核心类概念](#核心类概念)
5. [核心类方法文档](#核心类方法文档)
6. [使用示例](#使用示例)
7. [常见问题](#常见问题)
8. [Plus版本](#plus版本)

## 什么是 wxauto

wxauto 是一个基于 UIAutomation 的开源 Python 微信自动化库，最初在2020年开发，经过2023年的重新开发，针对新版微信增加了更多功能。即使 Python 初学者也可以简单上手自动化微信操作。

### 主要功能

- **消息发送**：支持发送文字、图片、文件、@群好友、引用消息等功能
- **聊天记录**：可获取好友的聊天记录内容
- **监听消息**：实时获取指定监听好友（群）的新消息
- **其他定制功能**：根据需求定制自动化流程，满足各种特殊需求

### 安全性

不封号。该项目基于Windows官方API开发，不涉及任何侵入、破解、抓包微信客户端应用，完全以人操作微信的行为执行操作。

## 环境配置和安装

### 环境要求

| 环境 | 版本要求 |
|------|----------|
| Python | 3.9-3.12 |
| OS | Windows10+, Windows Server2016+ |
| 微信 | 3.9.8+（不支持4.0） |

### 安装方式

#### 开源版
```bash
pip install wxauto
```

#### ✨Plus版
```bash
pip install wxautox

# 或指定python版本安装：
py -3.12 -m pip install wxautox
```

**激活Plus版本：**
```bash
wxautox -a 激活码
```

### 测试运行

```python
from wxauto import WeChat   # 开源版
# from wxautox import WeChat   # ✨Plus版

# 初始化微信实例
wx = WeChat()

# 发送消息
wx.SendMsg("你好", who="文件传输助手")

# 获取当前聊天窗口消息
msgs = wx.GetAllMessage()

for msg in msgs:
    print('==' * 30)
    print(f"{msg.sender}: {msg.content}")
```

## 快速开始

### 获取微信实例
```python
from wxauto import WeChat

# 初始化微信实例
wx = WeChat()
```

### 发送消息
```python
# 发送消息
wx.SendMsg("你好", who="文件传输助手")
```

### 获取当前聊天窗口消息
```python
# 获取当前聊天窗口消息
msgs = wx.GetAllMessage()

for msg in msgs:
    print('==' * 30)
    print(f"{msg.sender}: {msg.content}")
```

## 核心类概念

### Chat类
Chat 类代表一个微信聊天窗口实例，提供了与聊天相关的操作方法，用于对微信聊天窗口进行各种操作。

### WeChat类
WeChat 类是本项目的主要入口点，它继承自 Chat 类，代表微信主窗口实例，用于对微信主窗口进行各种操作。

**初始化参数：**
- `nickname` (str): 微信昵称，用于定位特定的微信窗口
- `debug` (bool): 是否开启调试模式

```python
wx = WeChat(nickname="张三")
```

### Message类
Message类代表微信聊天中的消息，分为两个概念：
- **消息内容类型（type）**：文本消息、图片消息、文件消息、语音消息、卡片消息等
- **消息来源类型（attr）**：系统消息、时间消息、自己发送的消息、对方发来的消息

### 消息类型表

| type↓ attr→ | 自己的消息 | 对方的消息 |
|-------------|------------|------------|
| 文本消息 | SelfTextMessage | FriendTextMessage |
| 引用消息 | SelfQuoteMessage | FriendQuoteMessage |
| 语音消息 | SelfVoiceMessage | FriendVoiceMessage |
| 图片消息 | SelfImageMessage | FriendImageMessage |
| 视频消息 | SelfVideoMessage | FriendVideoMessage |
| 文件消息 | SelfFileMessage | FriendFileMessage |

### WxResponse类
该类用于该项目多个方法的返回值：

```python
# 判断是否成功
if result:
    data = result['data']  # 成功，获取返回数据
else:
    print(result['message'])  # 失败，打印错误信息
```

### WxParam类
用于配置项目参数：

```python
from wxautox import WxParam

WxParam.LISTENER_EXCUTOR_WORKERS = 8  # 设置监听线程数
```

## 核心类方法文档

### WeChat类主要方法

#### 发送消息 SendMsg
```python
wx.SendMsg(msg="你好", who="张三", clear=True, at="李四", exact=False)
```

**参数：**
- `msg` (str): 消息内容
- `who` (str): 发送对象
- `clear` (bool): 发送后是否清空编辑框
- `at` (Union[str, List[str]]): @对象
- `exact` (bool): 是否精确匹配

#### 发送文件 SendFiles
```python
wx.SendFiles(filepath="C:/文件.txt", who="张三", exact=False)
```

#### ✨发送打字机模式文本 SendTypingText
```python
wx.SendTypingText(msg="你好", who="张三", clear=True, exact=False)

# 换行及@功能
wx.SendTypingText('各位下午好\n{@张三}负责xxx\n{@李四}负责xxxx', who='工作群')
```

#### 获取当前聊天窗口的所有消息 GetAllMessage
```python
messages = wx.GetAllMessage()
```

#### 添加监听聊天窗口 AddListenChat
```python
def on_message(msg, chat):
    print(f"收到来自 {chat} 的消息: {msg.content}")

wx.AddListenChat(nickname="张三", callback=on_message)
```

#### 获取下一个新消息 GetNextNewMessage
```python
messages = wx.GetNextNewMessage(filter_mute=False)
```

#### ✨获取好友列表 GetFriendDetails
```python
friends = wx.GetFriendDetails(n=10)
```

#### ✨添加新好友 AddNewFriend
```python
wx.AddNewFriend(keywords="张三", addmsg="我是小明", remark="老张", tags=["同学"])
```

### Message类主要方法

#### 回复消息 reply
```python
msg.reply("收到")
```

#### 转发消息 forward
```python
msg.forward("张三")
```

#### 下载文件/图片/视频 download
```python
file_path = msg.download()
```

#### ✨拍一拍 tickle
```python
msg.tickle()
```

#### ✨删除消息 delete
```python
msg.delete()
```

### ✨朋友圈类

#### 进入朋友圈
```python
moments = wx.Moments(timeout=3)
```

#### 获取朋友圈内容
```python
moments_list = moments.GetMoments()
```

#### 点赞朋友圈
```python
moment.Like()  # 点赞
moment.Like(False)  # 取消赞
```

#### 评论朋友圈
```python
moment.Comment('评论内容')
```

#### 保存朋友圈图片
```python
images = moment.SaveImages()
```

## 使用示例

### 1. 基本使用
```python
from wxauto import WeChat

# 初始化微信实例
wx = WeChat()

# 发送消息
wx.SendMsg("你好", who="张三")

# 获取当前聊天窗口消息
msgs = wx.GetAllMessage()
for msg in msgs:
    print(f"消息内容: {msg.content}, 消息类型: {msg.type}")
```

### 2. 监听消息
```python
from wxauto import WeChat
from wxauto.msgs import FriendMessage
import time

wx = WeChat()

# 消息处理函数
def on_message(msg, chat):
    # 将消息记录到本地文件
    with open('msgs.txt', 'a', encoding='utf-8') as f:
        f.write(msg.content + '\n')

    # 自动下载图片和视频
    if msg.type in ('image', 'video'):
        print(msg.download())

    # 自动回复收到
    if isinstance(msg, FriendMessage):
        msg.quote('收到')

# 添加监听
wx.AddListenChat(nickname="张三", callback=on_message)

# 保持程序运行
wx.KeepRunning()
```

### 3. ✨处理好友申请
```python
from wxautox import WeChat

wx = WeChat()

# 获取新的好友申请
newfriends = wx.GetNewFriends(acceptable=True)

# 处理好友申请
tags = ['同学', '技术群']
for friend in newfriends:
    remark = f'备注_{friend.name}'
    friend.accept(remark=remark, tags=tags)
```

### 4. ✨合并转发消息
```python
from wxautox import WeChat
from wxautox.msgs import HumanMessage

wx = WeChat()

# 打开指定聊天窗口
wx.ChatWith("工作群")

# 获取消息列表
msgs = wx.GetAllMessage()

# 多选最后五条消息
n = 0
for msg in msgs[::-1]:
    if n >= 5:
        break
    if isinstance(msg, HumanMessage):
        n += 1
        msg.multi_select()

# 执行合并转发
targets = ['张三', '李四']
wx.MergeForward(targets)
```

## 常见问题

### 不同获取消息的方法有什么区别？

| 方法 | 说明 |
|------|------|
| GetAllMessage | 获取当前聊天页面中已加载的消息 |
| GetNextNewMessage | 获取微信主窗口中，其中一个未设置消息免打扰窗口的新消息 |
| AddListenChat | 获取监听模式下聊天窗口的新消息 |

**监听模式优点：**
- 准确读取
- 速度快

**监听模式缺点：**
- 数量限制，最多设置40个监听对象

**全局模式优点：**
- 没有数量限制，无差别获取所有窗口新消息

**全局模式缺点：**
- 必须进行UI操作，速度可能相较监听模式慢些

### 会封号吗？
不会封号。该项目基于Windows官方API开发，不涉及任何侵入、破解、抓包微信客户端应用。

但以下行为可能有风控风险：
- 曾用hook类或webhook类微信工具
- 频繁且大量的发送消息、添加好友等
- 高频率发送机器人特征明显的消息
- 扫码手机与电脑客户端不在同一个城市
- 低权重账号做太多动作

### 支持Linux/Mac吗？
不支持，基于Windows官方API开发，只支持Windows系统。

### 是否支持微信多开？
wxauto项目不支持一切违反官方用户协议的操作，不建议、不支持、不提供微信多开的方法或行为。

## Plus版本

### 功能对比

| 类别 | 功能 | 开源版 | ✨Plus版 |
|------|------|--------|----------|
| 消息类 | 发送自定义表情包 | ❌ | ✅ |
| 消息类 | @所有人 | ❌ | ✅ |
| 消息类 | 合并转发 | ❌ | ✅ |
| 好友管理 | 获取好友列表 | ❌ | ✅ |
| 好友管理 | 发送好友请求 | ❌ | ✅ |
| 好友管理 | 接受好友请求 | ❌ | ✅ |
| 群管理 | 邀请入群 | ❌ | ✅ |
| 群管理 | 修改群名 | ❌ | ✅ |
| 朋友圈 | 获取朋友圈内容 | ❌ | ✅ |
| 朋友圈 | 点赞朋友圈 | ❌ | ✅ |
| 其他 | 后台模式 | ❌ | ✅ |

### Plus版本特性

**后台模式：**
- 不依赖鼠标移动
- 绝大部分场景无需将微信调到前台窗口即可进行操作
- 不抢占鼠标
- 执行速度快
- 窗口不必在桌面顶部也能操作

### 获取Plus版本
- 添加作者好友，备注"plus"
- 加入交流群获取更多支持

---

**注意：** 文档中标题前缀为✨标志的，为Plus版本特有方法，开源版无法调用。

**更新说明：** Plus版本订阅期为1年，订阅期内更新免费，订阅过期后不提供更新服务，已获取的版本仍可继续使用。

## 消息类型处理和API转换

在实际应用中，不同类型的消息需要提取不同的实际内容：

### 统一消息处理器

```python
class MessageProcessor:
    @staticmethod
    def extract_content(msg):
        """根据消息类型提取实际可用内容"""
        if msg.type == 'text':
            # 文本消息直接返回内容
            return msg.content

        elif msg.type == 'voice':
            # 语音消息转换为文本
            try:
                return msg.to_text()  # wxauto提供的语音转文字功能
            except Exception as e:
                return f"[语音转换失败: {str(e)}]"

        elif msg.type == 'link':
            # 链接消息返回实际URL
            try:
                return msg.get_url()  # Plus版本功能，返回真实链接
            except:
                return msg.content  # 降级返回显示内容

        elif msg.type == 'image':
            # 图片消息可以OCR识别文字或返回图片路径
            try:
                img_path = msg.download()
                # 如果需要OCR识别图片中的文字
                # return perform_ocr(img_path)
                return f"[图片已下载: {img_path}]"
            except:
                return "[图片消息]"

        elif msg.type == 'file':
            # 文件消息下载文件并返回路径
            try:
                file_path = msg.download()
                return f"文件: {msg.content}, 路径: {file_path}"
            except:
                return f"文件: {msg.content}"

        elif msg.type == 'location':
            # 位置消息返回具体地址
            return getattr(msg, 'address', msg.content)

        elif msg.type == 'quote':
            # 引用消息返回引用内容+回复内容
            return f"引用内容: {msg.quote_content}\n回复内容: {msg.content}"

        elif msg.type == 'merge':
            # 合并转发消息展开所有内容
            try:
                messages = msg.get_messages()  # Plus版本功能
                return "\n".join(messages)
            except:
                return msg.content

        else:
            # 其他类型消息返回原始内容
            return msg.content or f"[{msg.type}类型消息]"

### API接口处理示例

```python
def process_message_for_api(msg, chat):
    """处理消息并发送给API"""
    processor = MessageProcessor()

    # 提取实际内容
    extracted_content = processor.extract_content(msg)

    # 构建API数据
    api_payload = {
        'message': extracted_content,  # 实际可处理的内容
        'type': msg.type,
        'sender': msg.sender,
        'timestamp': getattr(msg, 'time', ''),
        'chat_info': chat.ChatInfo() if hasattr(chat, 'ChatInfo') else {}
    }

    # 调用API
    try:
        response = your_api_client.process_message(api_payload)

        # 根据API响应回复
        if response.get('reply'):
            chat.SendMsg(response['reply'])

    except Exception as e:
        print(f"API调用失败: {e}")

# 实际使用
wx = WeChat()
wx.AddListenChat(nickname="客服群", callback=process_message_for_api)
wx.KeepRunning()
```

### 关键处理策略

1. **语音消息** → 使用 `msg.to_text()` 转换为文本内容
2. **链接消息** → 使用 `msg.get_url()` 提取真实URL地址
3. **图片消息** → 下载图片，可选OCR识别文字内容
4. **文件消息** → 下载文件，返回文件路径和名称
5. **位置消息** → 提取 `address` 属性获取地址信息
6. **引用消息** → 组合 `quote_content` 和 `content`
7. **合并消息** → 使用 `get_messages()` 展开所有消息内容

这样处理后，API接收到的都是实际可用的文本或URL内容，而不是消息类型标识。
```
