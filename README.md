# dolphin_wxbot 微信机器人

`dolphin_wxbot` 是一个功能强大的微信聊天机器人，配备了现代化的图形用户界面（GUI）用于配置和管理。它支持连接多种主流 AI 平台，实现了灵活的消息处理和自动化管理功能。

## ✨ 主要功能

- **现代化配置界面**: 使用 `main.py` 启动图形化配置管理器，轻松管理所有设置。
- **多 AI 平台支持**: 可通过配置连接到 OpenAI、Coze、Dify、FastGPT、RAGFlow 等多种 AI 服务。
- **异步消息处理**: 采用异步架构，能够高效处理多用户和多群组的并发消息，避免阻塞。
- **精细化监听规则**:
    - **用户和群组**: 可以指定监听特定的用户和群组。
    - **消息类型过滤**: 可配置只处理特定类型的消息（如文本、链接、图片等）。
    - **@机器人**: 在群聊中，可设置是否需要`@`机器人才会触发回复。
- **实时日志系统**: 在GUI中实时查看机器人的运行日志，方便调试和监控。
- **管理员指令**: 管理员可以直接在微信聊天中通过指令动态修改配置和控制机器人。

## 🚀 快速开始

### 1. 环境准备

- Python 3.8 或更高版本
- 已安装并登录 Windows 版本的微信客户端

### 2. 安装依赖

克隆本项目到本地，然后通过 `pip` 安装所需的依赖库：

```bash
git clone <your-repository-url>
cd siver_wxbot
pip install -r requirements.txt
```

### 3. 配置机器人

项目首次运行时，会自动生成一个 `config.json` 配置文件。请根据以下说明修改配置：

1.  **运行配置管理器**:
    ```bash
    python main.py
    ```
2.  **配置 API**:
    - 在 "API配置" 标签页中，添加您要使用的 AI 平台信息。
    - **`platform`**: 平台类型，如 `openai`, `dify`, `ragflow` 等。
    - **`api_key`**: 您从 AI 平台获取的密钥。
    - **`base_url`**: AI 平台的接口地址。
    - **`is_default`**: 设为 `true` 的 API 将作为默认 API 使用。

3.  **配置监听规则**:
    - 在 "监听规则" 标签页中，设置机器人的行为。
    - **全局设置**: 控制群机器人的总开关，并设置默认 API。
    - **用户规则**: 添加或删除需要机器人回复的个人用户。
    - **群组规则**: 添加或删除需要机器人回复的群聊，并可设置是否需要 `@` 机器人才响应。

### 4. 启动机器人

在配置管理器的 "控制面板" 标签页中，点击 "启动机器人" 按钮。观察 "实时日志" 窗口，确保机器人成功启动并开始监听消息。

## ⚙️ 配置文件 `config.json` 详解

```json
{
    "api_configs": [
        {
            "id": "api_1",
            "name": "ragflow",
            "platform": "ragflow",
            "api_key": "your-ragflow-api-key",
            "base_url": "http://your-ragflow-instance/api/v1/...",
            "enabled": true,
            "is_default": true
        },
        {
            "id": "api_2",
            "name": "dify_lily",
            "platform": "dify",
            "api_key": "your-dify-api-key",
            "base_url": "http://your-dify-instance/v1",
            "enabled": true,
            "is_default": false
        }
    ],
    "listen_rules": {
        "global_bot_enabled": true,
        "default_api_id": "api_1",
        "message_types_filter": {
            "enabled": true,
            "allowed_types": ["text", "link", "location", "voice"]
        },
        "user_rules": [
            {
                "name": "用户昵称或备注",
                "api_id": "api_1",
                "enabled": true
            }
        ],
        "group_rules": [
            {
                "name": "群聊名称",
                "api_id": "api_2",
                "enabled": true,
                "at_required": false,
                "admins": []
            }
        ]
    },
    "机器人名字": "小助手",
    "管理员": "您的微信昵称或备注"
}
```

- **`api_configs`**: 数组，包含一个或多个 AI 平台的配置。
- **`listen_rules`**: 对象，定义了机器人的监听和响应规则。
- **`机器人名字`**: 机器人的名称，在被问及身份时使用。
- **`管理员`**: 管理员的微信昵称或备注，用于接收和发送控制指令。

## 🔧 管理员指令

管理员可以直接向机器人发送以下指令来动态管理它（无需重启）：

-   `/当前用户`: 查看当前监听的用户列表。
-   `/添加用户[用户名]`: 添加一个用户到监听列表。
-   `/删除用户[用户名]`: 从监听列表中删除一个用户。
-   `/当前群`: 查看当前监听的群组列表。
-   `/添加群[群名]`: 添加一个群组到监听列表。
-   `/删除群[群名]`: 从监听列表中删除一个群组。
-   `/开启群机器人`: 全局开启群聊回复功能。
-   `/关闭群机器人`: 全局关闭群聊回复功能。
-   `/当前模型`: 查看当前默认使用的 AI 模型。
-   `/切换模型[1-4]`: 切换到配置中对应的模型。
-   `/当前AI设定`: 查看当前的系统提示词 (Prompt)。
-   `/更改AI设定为[内容]`: 修改系统提示词。
-   `/更新配置`: 重新加载 `config.json` 文件。
-   `/当前版本`: 显示机器人的当前版本信息。

## 📂 项目结构

-   **`main.py`**: 图形化配置管理器（GUI）的入口文件。
-   **`wxbot_preview.py`**: 机器人的核心逻辑，包括消息处理、指令解析和与微信的交互。
-   **`async_message_handler.py`**: 异步消息处理模块，负责将消息放入队列并并发调用 AI API。
-   **`message_processor.py`**: 消息内容提取和预处理模块。
-   **`config.json`**: 核心配置文件。
-   **`requirements.txt`**: 项目依赖库列表。
-   **`API/`**: 存放不同 AI 平台连接器的目录（当前逻辑主要集中在 `async_message_handler.py` 中）。
