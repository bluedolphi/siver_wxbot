# wxautox框架 - 用户收到信息类型与数据结构文档

## 概述

wxautox是一个基于Windows微信客户端的自动化框架，支持监听和处理各种类型的微信消息。本文档详细描述了框架中用户可以收到的各种消息类型及其对应的数据结构。

## 主要消息类型

### 1. FriendMessage (好友消息)

**描述**: 来自好友或群友的消息，是最常见的消息类型。

**数据结构**:
```python
class FriendMessage:
    type: str           # 消息类型标识
    attr: str           # 消息属性，通常为 'friend'
    sender: str         # 发送者昵称/备注名
    sender_remark: str  # 发送者备注名
    content: str        # 消息内容
    info: dict          # 原始消息信息
    timestamp: datetime # 消息时间戳
```

**消息内容类型**:
- **文本消息**: 普通文字内容
- **链接消息**: 显示为 `[链接]`，需要解析为"标题+URL"格式传给API处理
- **图片消息**: 显示为 `[图片]`
- **文件消息**: 显示为 `[文件]`
- **语音消息**: 显示为 `[语音]`
- **视频消息**: 显示为 `[视频]`
- **表情消息**: 显示为 `[表情]`
- **位置消息**: 显示为 `[位置]`

**处理示例**:
```python
def message_handle_callback(msg, chat):
    if isinstance(msg, FriendMessage):
        print(f"收到好友消息: {msg.sender} - {msg.content}")
        process_message(chat, msg)
```

### 2. SystemMessage (系统消息)

**描述**: 微信系统生成的消息，如群成员变动、系统通知等。

**数据结构**:
```python
class SystemMessage:
    type: str           # 消息类型标识
    attr: str           # 消息属性，通常为 'system'
    content: str        # 系统消息内容
    info: dict          # 原始消息信息
    timestamp: datetime # 消息时间戳
```

**常见系统消息类型**:
- **群成员加入**: `"xxx"加入群聊` 或 `"xxx"加入了群聊`
- **群成员退出**: `"xxx"退出了群聊`
- **群名称修改**: `群名称已修改为"xxx"`
- **群公告更新**: `群公告已更新`
- **撤回消息**: `"xxx"撤回了一条消息`

**处理示例**:
```python
def message_handle_callback(msg, chat):
    if isinstance(msg, SystemMessage):
        if "加入群聊" in msg.content:
            send_group_welcome_msg(chat, msg)
```

## 消息属性详解

### 消息属性 (attr)

- **friend**: 好友消息
- **system**: 系统消息
- **self**: 自己发送的消息
- **other**: 其他类型消息

### 消息发送者信息

在群聊中，消息对象包含以下发送者信息：
- `sender`: 发送者在群中的昵称
- `sender_remark`: 发送者的备注名（如果有）

## 聊天窗口对象 (Chat)

**数据结构**:
```python
class Chat:
    who: str            # 聊天对象名称（好友备注名或群名）
    
    # 方法
    def SendMsg(msg: str, at: str = None):
        """发送消息
        Args:
            msg: 消息内容
            at: @的用户名（仅群聊有效）
        """
        pass
```

## 消息处理流程

### 1. 消息监听设置

```python
# 添加监听用户
wx.AddListenChat(nickname="用户名", callback=message_handle_callback)

# 添加监听群组
wx.AddListenChat(nickname="群名", callback=message_handle_callback)
```

### 2. 消息回调处理

```python
def message_handle_callback(msg, chat):
    """消息处理回调函数
    Args:
        msg: 消息对象 (FriendMessage 或 SystemMessage)
        chat: 聊天窗口对象
    """
    # 记录消息日志
    text = f'类型：{msg.type} 属性：{msg.attr} 窗口：{chat.who} 发送人：{msg.sender_remark} - 消息：{msg.content}'
    print(text)
    
    # 根据消息类型处理
    if isinstance(msg, FriendMessage):
        process_friend_message(chat, msg)
    elif isinstance(msg, SystemMessage):
        process_system_message(chat, msg)
```

### 3. 消息内容处理

```python
def process_message(chat, message):
    """处理好友消息"""
    # 检查是否需要@机器人
    if chat.who in group_list:
        if AtMe in message.content:
            content = re.sub(AtMe, "", message.content).strip()
            # 处理群聊@消息
            handle_group_message(chat, content)
    else:
        # 处理私聊消息
        handle_private_message(chat, message.content)
```

## 特殊消息处理

### 1. 链接消息处理

链接消息是微信中常见的消息类型，需要特殊处理以提供更好的用户体验：

```python
def process_link_message(message):
    """处理链接消息，转换为标题+URL格式"""
    if message.content == "[链接]":
        # 从消息对象中提取链接信息
        link_info = extract_link_info(message)
        if link_info:
            # 转换为API可处理的文本格式
            processed_content = f"""用户分享了一个链接：
标题：{link_info['title']}
URL：{link_info['url']}
描述：{link_info.get('description', '无描述')}

请根据这个链接内容进行回复。"""
            return processed_content
        else:
            return "用户分享了一个链接，但无法获取详细信息"
    return message.content

def extract_link_info(message):
    """从消息对象中提取链接详细信息"""
    try:
        # wxautox框架中链接信息通常存储在message.info中
        if hasattr(message, 'info') and isinstance(message.info, dict):
            # 尝试多种可能的字段名
            link_fields = ['link_info', 'url_info', 'share_info', 'card_info']

            for field in link_fields:
                if field in message.info:
                    link_data = message.info[field]
                    return {
                        'title': link_data.get('title', link_data.get('name', '未知标题')),
                        'url': link_data.get('url', link_data.get('link', '')),
                        'description': link_data.get('desc', link_data.get('description', ''))
                    }

        # 如果无法从info中提取，尝试其他方法
        return extract_link_from_raw_data(message)

    except Exception as e:
        print(f"提取链接信息失败: {e}")
        return None

def extract_link_from_raw_data(message):
    """从原始消息数据中提取链接信息"""
    # 这里可以添加更多的提取逻辑
    # 根据实际的wxautox版本和微信客户端版本调整
    return None
```

**个人与群组监听的链接消息处理差异**：

```python
def handle_link_in_different_contexts(chat, message):
    """在不同上下文中处理链接消息"""

    # 获取处理后的链接内容
    processed_content = process_link_message(message)

    if chat.who in user_rules:
        # 个人聊天中的链接处理
        handle_personal_link(chat, processed_content, message)
    elif chat.who in group_rules:
        # 群组聊天中的链接处理
        handle_group_link(chat, processed_content, message)

def handle_personal_link(chat, content, original_message):
    """处理个人聊天中的链接"""
    # 个人聊天可以直接处理链接
    send_to_api(chat, content)

def handle_group_link(chat, content, original_message):
    """处理群组聊天中的链接"""
    # 群组中需要检查是否@了机器人
    group_rule = get_group_rule(chat.who)

    if group_rule and group_rule.get('at_required', True):
        # 需要@才处理链接
        if AtMe in original_message.content or is_mentioned(original_message):
            send_to_api(chat, content)
    else:
        # 不需要@就处理链接
        send_to_api(chat, content)
```

### 2. 群欢迎消息

```python
def send_group_welcome_msg(chat, message):
    """处理群欢迎新人"""
    if "加入群聊" in message.content:
        # 提取新成员名称
        new_friend = find_new_group_friend(message.content, 1)
        # 发送欢迎消息并@新成员
        chat.SendMsg(msg=group_welcome_msg, at=new_friend)
```

### 2. 长消息分段处理

```python
def split_long_text(text, chunk_size=2000):
    """分割长文本消息"""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# 发送分段消息
if len(reply) >= 2000:
    segments = split_long_text(reply)
    for segment in segments:
        chat.SendMsg(segment)
```

## 异步消息处理

框架支持异步消息处理，提高并发性能：

```python
# 异步处理消息
async def process_single_message(message_data):
    """异步处理单个消息"""
    message_id = message_data['id']
    chat = message_data['chat']
    message = message_data['message']
    api_config = message_data['api_config']
    
    # API调用
    reply = await call_api_async(message.content, api_config, message_id)
    
    # 发送回复
    await wx_send_queue.put({
        'chat': chat,
        'message': reply,
        'message_id': message_id
    })
```

## 配置相关数据结构

### API配置结构

```python
api_config = {
    'id': 'api_1',
    'name': 'API配置名称',
    'platform': 'openai',  # openai, coze, dify, fastgpt, n8n, ragflow
    'api_key': 'your_api_key',
    'base_url': 'https://api.example.com',
    'model': 'gpt-3.5-turbo',
    'enabled': True,
    'is_default': False
}
```

### 监听规则结构

```python
listen_rules = {
    'global_bot_enabled': True,
    'default_api_id': 'api_1',
    'user_rules': [
        {
            'name': '用户名',
            'api_id': 'api_1',
            'enabled': True
        }
    ],
    'group_rules': [
        {
            'name': '群名',
            'api_id': 'api_1',
            'enabled': True,
            'at_required': True,
            'admins': []
        }
    ]
}
```

## 日志格式

框架会记录详细的消息处理日志：

```
[2025-08-27 10:02:30] [friend other]获取到新消息：蓝京 - [链接]
[2025-08-27 10:03:10] [self text]获取到新消息：蓝京 - API调用结果
```

日志格式说明：
- `[时间戳]`: 消息时间
- `[消息属性 消息类型]`: 消息分类
- `获取到新消息`: 操作类型
- `发送者 - 消息内容`: 具体信息

## 错误处理

框架提供完善的错误处理机制：

```python
try:
    # 消息处理逻辑
    reply = process_with_api(message.content)
    chat.SendMsg(reply)
except Exception as e:
    # 错误日志记录
    print(f"消息处理失败: {e}")
    # 发送错误提示
    chat.SendMsg("处理消息时出现错误，请稍后再试")
```

## 消息类型枚举

### 消息类型标识符

根据wxautox框架的实现，消息类型包括：

```python
MESSAGE_TYPES = {
    'text': '文本消息',
    'image': '图片消息',
    'file': '文件消息',
    'voice': '语音消息',
    'video': '视频消息',
    'emoji': '表情消息',
    'location': '位置消息',
    'link': '链接消息',
    'system': '系统消息',
    'recall': '撤回消息',
    'card': '名片消息',
    'transfer': '转账消息',
    'redpacket': '红包消息'
}
```

### 消息属性枚举

```python
MESSAGE_ATTRS = {
    'friend': '好友消息',
    'system': '系统消息',
    'self': '自己发送的消息',
    'other': '其他类型消息'
}
```

## 高级消息处理功能

### 1. 消息过滤和路由

```python
def message_router(msg, chat):
    """消息路由器 - 根据消息类型和来源进行路由"""

    # 根据聊天窗口类型路由
    if chat.who in user_rules:
        return handle_user_message(msg, chat)
    elif chat.who in group_rules:
        return handle_group_message(msg, chat)
    elif chat.who == admin_user:
        return handle_admin_command(msg, chat)

    # 默认处理
    return handle_default_message(msg, chat)
```

### 2. 消息队列管理

```python
class MessageQueue:
    """消息队列管理器"""

    def __init__(self, max_size=1000):
        self.queue = asyncio.Queue(maxsize=max_size)
        self.processing = {}

    async def add_message(self, msg_data):
        """添加消息到队列"""
        await self.queue.put(msg_data)

    async def process_messages(self):
        """处理队列中的消息"""
        while True:
            msg_data = await self.queue.get()
            await self.handle_single_message(msg_data)
```

### 3. 消息状态跟踪

```python
MESSAGE_STATUS = {
    'queued': '已排队',
    'processing': '处理中',
    'completed': '已完成',
    'error': '处理失败',
    'timeout': '处理超时'
}

class MessageTracker:
    """消息状态跟踪器"""

    def __init__(self):
        self.messages = {}

    def track_message(self, msg_id, status):
        """跟踪消息状态"""
        self.messages[msg_id] = {
            'status': status,
            'timestamp': time.time(),
            'attempts': 0
        }
```

## API集成数据结构

### 支持的API平台

```python
SUPPORTED_PLATFORMS = {
    'openai': {
        'name': 'OpenAI兼容API',
        'required_fields': ['api_key', 'base_url', 'model'],
        'optional_fields': ['temperature', 'max_tokens']
    },
    'coze': {
        'name': 'Coze API',
        'required_fields': ['api_key', 'base_url'],
        'optional_fields': ['bot_id', 'user_id']
    },
    'dify': {
        'name': 'Dify API',
        'required_fields': ['api_key', 'base_url'],
        'optional_fields': ['conversation_id', 'user']
    },
    'ragflow': {
        'name': 'RAGFlow API',
        'required_fields': ['api_key', 'base_url'],
        'optional_fields': ['conversation_id', 'stream']
    },
    'fastgpt': {
        'name': 'FastGPT API',
        'required_fields': ['api_key', 'base_url'],
        'optional_fields': ['chatId', 'stream']
    },
    'n8n': {
        'name': 'n8n Webhook',
        'required_fields': ['base_url'],
        'optional_fields': ['headers', 'method']
    }
}
```

### API响应数据结构

```python
class APIResponse:
    """API响应统一数据结构"""

    def __init__(self):
        self.success: bool = False
        self.content: str = ""
        self.error_message: str = ""
        self.response_time: float = 0.0
        self.token_usage: dict = {}
        self.metadata: dict = {}
```

## 命令系统

### 管理员命令列表

```python
ADMIN_COMMANDS = {
    '/当前用户': '显示当前监听用户列表',
    '/添加用户[用户名]': '添加用户到监听列表',
    '/删除用户[用户名]': '从监听列表删除用户',
    '/当前群': '显示当前监听群组列表',
    '/添加群[群名]': '添加群组到监听列表',
    '/删除群[群名]': '从监听列表删除群组',
    '/开启群机器人': '启用群机器人功能',
    '/关闭群机器人': '禁用群机器人功能',
    '/群机器人状态': '查看群机器人状态',
    '/当前模型': '显示当前使用的AI模型',
    '/切换模型[1-4]': '切换到指定的AI模型',
    '/当前AI设定': '显示当前AI提示词设定',
    '/更改AI设定为[内容]': '修改AI提示词',
    '/更新配置': '重新加载配置文件',
    '/当前版本': '显示程序版本信息',
    '/指令': '显示所有可用命令'
}
```

### 命令处理示例

```python
def handle_admin_command(msg, chat):
    """处理管理员命令"""
    command = msg.content.strip()

    if command == '/当前用户':
        response = f"当前监听用户：\n{', '.join(listen_list)}"
        chat.SendMsg(response)

    elif command.startswith('/添加用户'):
        user_name = command.replace('/添加用户', '').strip()
        add_user(user_name)
        chat.SendMsg(f"用户 {user_name} 已添加到监听列表")
```

## 性能监控和统计

### 消息处理统计

```python
class MessageStats:
    """消息处理统计"""

    def __init__(self):
        self.total_messages = 0
        self.processed_messages = 0
        self.failed_messages = 0
        self.average_response_time = 0.0
        self.message_types_count = {}
        self.api_usage_count = {}

    def record_message(self, msg_type, processing_time, success=True):
        """记录消息处理统计"""
        self.total_messages += 1
        if success:
            self.processed_messages += 1
        else:
            self.failed_messages += 1

        # 更新平均响应时间
        self.average_response_time = (
            (self.average_response_time * (self.total_messages - 1) + processing_time)
            / self.total_messages
        )

        # 统计消息类型
        self.message_types_count[msg_type] = self.message_types_count.get(msg_type, 0) + 1
```

## 安全和权限控制

### 用户权限级别

```python
USER_PERMISSIONS = {
    'admin': {
        'level': 0,
        'permissions': ['all_commands', 'config_modify', 'user_management']
    },
    'moderator': {
        'level': 1,
        'permissions': ['basic_commands', 'group_management']
    },
    'user': {
        'level': 2,
        'permissions': ['chat_only']
    },
    'guest': {
        'level': 3,
        'permissions': ['limited_chat']
    }
}
```

### 消息内容过滤

```python
class ContentFilter:
    """消息内容过滤器"""

    def __init__(self):
        self.blocked_words = []
        self.blocked_patterns = []

    def filter_message(self, content):
        """过滤消息内容"""
        # 检查敏感词
        for word in self.blocked_words:
            if word in content:
                return False, f"包含敏感词: {word}"

        # 检查正则模式
        for pattern in self.blocked_patterns:
            if re.search(pattern, content):
                return False, f"匹配敏感模式: {pattern}"

        return True, "内容安全"
```

## 总结

wxautox框架提供了完整的微信消息处理解决方案，主要特性包括：

1. **丰富的消息类型支持**: FriendMessage、SystemMessage等多种消息类型
2. **灵活的API集成**: 支持OpenAI、Coze、Dify、RAGFlow等多个AI平台
3. **异步消息处理**: 高性能的并发消息处理能力
4. **完善的配置系统**: 用户规则、群组规则、API配置等
5. **强大的命令系统**: 管理员命令和用户交互
6. **性能监控**: 消息处理统计和性能分析
7. **安全控制**: 权限管理和内容过滤

通过这些功能和数据结构，开发者可以构建功能强大、性能优异的微信机器人应用。
