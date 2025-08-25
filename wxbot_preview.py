#!/usr/bin/env python3
# Siver微信机器人 siver_wxbot
# 作者：dolphi

ver = "V2.0.0"         # 当前版本
ver_log = "日志：全新版本2.0，支持最新wxauto V2"    # 日志
import time
import json
import re
import traceback
import email_send
from openai import OpenAI
from datetime import datetime, timedelta
from wxauto import WeChat
from wxauto.msgs import *
import async_message_handler

# -------------------------------
# 配置相关
# -------------------------------

# 配置文件路径
CONFIG_FILE = 'config.json'

# 全局配置字典及相关变量（将在 refresh_config 中更新）
config = {}
listen_list = []    # 监听的用户列表
api_key = ""        # API 密钥
base_url = ""       # API 基础 URL
AtMe = ""           # 机器人@的标识
bot_name = ""       # 机器人名字
cmd = ""            # 命令接收账号（管理员）
group = []          # 群聊ID
group_switch = None # 群机器人开关
group_welcome = False
group_welcome_msg = "欢迎新朋友！请先查看群公告！本消息由wxautox发送!"
model1 = ""         # 模型1标识
model2 = ""         # 模型2标识
model3 = ""         # 模型3标识
model4 = ""         # 模型4标识
prompt = ""         # AI提示词
# 当前使用的模型和 API 客户端
DS_NOW_MOD = ""
client = None

def is_err(id, err="无"):
    '''错误中断并发送邮件 
    id：邮件主题
    err:错误信息'''
    print(traceback.format_exc())
    print(err)
    email_send.send_email(subject=id, content='错误信息：\n'+traceback.format_exc()+"\nerr信息：\n"+str(err))
    while True:
        print("程序已保护现场，检查后请重启程序")
        time.sleep(100)
def now_time(time="%Y/%m/%d %H:%M:%S "):
    # 获取当前时间
    now = datetime.now()
    # 格式化时间为 YYYY/MM/DD HH:mm:ss
    formatted_time = now.strftime(time)
    return formatted_time

def check_wechat_window():
    """检测微信是否运行"""
    return wx.IsOnline()

def load_config():
    """
    从配置文件加载配置，并赋值给全局变量 config
    """
    global config
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
            config = json.load(file)
            print("配置文件加载成功")
    except Exception as e:
        print("打开配置文件失败，请检查配置文件！", e)
        while True:
            time.sleep(100)


def update_global_config():
    """
    将 config 中的配置项更新到全局变量中，并初始化 API 客户端
    支持新版 listen_rules 配置结构，同时兼容旧版配置
    """
    global listen_list, api_key, base_url, AtMe, cmd, group, model1, model2, model3, model4, prompt, DS_NOW_MOD, client, group_switch, bot_name
    
    # 获取新版监听规则配置
    listen_rules = config.get('listen_rules', {})
    
    # 从新版配置构建监听列表（启用的用户）
    user_rules = listen_rules.get('user_rules', [])
    listen_list = [rule['name'] for rule in user_rules if rule.get('enabled', True)]
    
    # 从新版配置构建群组列表（启用的群组）
    group_rules = listen_rules.get('group_rules', [])
    group = [rule['name'] for rule in group_rules if rule.get('enabled', True)]
    
    # 全局群机器人开关
    group_switch = "True" if listen_rules.get('global_bot_enabled', True) else "False"
    
    # 如果新版配置为空，回退到旧版配置
    if not listen_list:
        listen_list = config.get('监听用户列表', [])
    if not group:
        group = config.get('监听群组列表', [])
    if 'global_bot_enabled' not in listen_rules:
        group_switch = config.get('群机器人开关', 'True')
    
    # 获取默认API配置
    api_configs = config.get('api_configs', [])
    default_api_id = config.get('default_api_id', '') or listen_rules.get('default_api_id', '')
    
    # 查找默认API配置
    default_api_config = None
    if default_api_id:
        for api_config in api_configs:
            if api_config.get('id') == default_api_id and api_config.get('enabled', True):
                default_api_config = api_config
                break
    
    # 如果没找到默认配置，使用第一个启用的配置
    if not default_api_config and api_configs:
        for api_config in api_configs:
            if api_config.get('enabled', True):
                default_api_config = api_config
                break
    
    # 设置API相关变量（优先使用新版配置，回退到旧版）
    if default_api_config:
        api_key = default_api_config.get('api_key', "")
        base_url = default_api_config.get('base_url', "")
        DS_NOW_MOD = default_api_config.get('model', "")
        prompt = config.get('prompt', "")  # 系统提示词仍从全局配置获取
    else:
        # 回退到旧版配置
        api_key = config.get('api_key', "")
        base_url = config.get('base_url', "")
        DS_NOW_MOD = config.get('model1', "")
        prompt = config.get('prompt', "")
    
    # 保持旧版模型变量的兼容性
    model1 = config.get('model1', "")
    model2 = config.get('model2', "")
    model3 = config.get('model3', "")
    model4 = config.get('model4', "")
    
    # 其他配置
    cmd = config.get('管理员', "")
    bot_name = config.get("机器人名字", '')
    
    # 初始化 OpenAI 客户端
    if api_key and base_url:
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        print("警告: 未找到有效的API配置，客户端初始化可能失败")
        client = None
    
    print(now_time()+"全局配置更新完成")
    print(f"监听用户: {listen_list}")
    print(f"监听群组: {group}")
    print(f"群机器人开关: {group_switch}")
    print(f"默认API: {default_api_config.get('name', '未配置') if default_api_config else '未配置'}")


def refresh_config():
    """
    刷新配置：重新加载配置文件并更新全局变量
    """
    load_config()
    update_global_config()


def save_config():
    """
    将当前的配置写回到配置文件
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as file:  # 写入配置文件
            json.dump(config, file, ensure_ascii=False, indent=4)  # 保留中文原格式 
    except Exception as e:  # 异常处理
        print("保存配置文件失败:", e)  # 显示错误信息   


def add_user(name):
    """
    添加用户至监听列表，并更新配置
    """
    if name not in config.get('监听用户列表', []):  # 检查用户是否已存在
        config['监听用户列表'].append(name)  # 添加用户到监听列表
        save_config()  # 保存配置
        refresh_config()  # 刷新配置
        print("添加后的  监听用户列表:", config['监听用户列表'])  # 显示添加后的列表
    else:
        print(f"用户 {name} 已在监听列表中")  # 显示用户已存在  


def remove_user(name):
    """
    从监听列表中删除指定用户，并更新配置
    """
    if name in listen_list:  # 检查用户是否存在
        config['监听用户列表'].remove(name)  # 从列表中删除用户
        save_config()  # 保存配置
        refresh_config()  # 刷新配置
        print("删除后的 监听用户列表:", config['监听用户列表'])  # 显示删除后的列表
    else:
        print(f"用户 {name} 不在监听列表中")


def set_group(new_group):
    """
    更改监听的群聊ID，并更新配置
    """
    config['监听群组列表'] = new_group  # 更新群聊ID
    save_config()  # 保存配置
    refresh_config()  # 刷新配置
    print("群组已更改为", config['监听群组列表'])  # 显示更新后的群聊ID

def add_group(name):
    """
    添加群组至监听列表，并更新配置
    """
    if name not in config.get('监听群组列表', []):  # 检查用户是否已存在
        config['监听群组列表'].append(name)  # 添加用户到监听列表
        save_config()  # 保存配置
        refresh_config()  # 刷新配置
        print("添加后的  监听群组列表:", config['监听群组列表'])  # 显示添加后的列表
    else:
        print(f"群组 {name} 已在监听列表中")  # 显示用户已存在  
def remove_group(name):
    """
    删除群组从监听列表，并更新配置
    """
    if name in config.get('监听群组列表', []):  # 检查用户是否存在
        config['监听群组列表'].remove(name)  # 从列表中删除用户
        save_config()  # 保存配置
        refresh_config()  # 刷新配置
        print("删除后的 监听群组列表:", config['监听群组列表'])  # 显示删除后的列表
    else:
        print(f"群组 {name} 不在监听列表中")

def set_group_switch(switch_value):
    """
    设置是否启用群机器人（"True" 或 "False"），并更新配置
    """
    config['群机器人开关'] = switch_value  # 更新群机器人开关状态
    save_config()  # 保存配置       
    refresh_config()  # 刷新配置
    print("群开关设置为", config['群机器人开关'])  # 显示更新后的开关状态
def set_config(id, new_content):
    """
    更改配置
    id:字段
    new_content:新的字段值
    """
    config[id] = new_content  # 更新
    save_config()  # 保存配置
    refresh_config()  # 刷新配置
    print(now_time()+id+"已更改为:", config[id])  # 显示更新后的

def split_long_text(text, chunk_size=2000):
    # 使用range生成切割起始位置序列：0, chunk_size, 2*chunk_size...
    # 通过列表推导式循环截取每个分段
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# -------------------------------
# DeepSeek API 调用
# -------------------------------

def deepseek_chat(message, model, stream, prompt):
    """
    调用 DeepSeek API 获取对话回复

    参数:
        message (str): 用户输入的消息
        model (str): 使用的模型标识
        stream (bool): 是否使用流式输出

    返回:
        str: AI 返回的回复
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message},
            ],
            stream=stream
        )
    except Exception as e:
        print("调用 DeepSeek API 出错:", e)
        raise

    # 流式输出处理
    if stream:
        reasoning_content = ""  # 思维链内容
        content = ""  # 回复内容    
        for chunk in response: 
            if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content: # 判断是否为思维链
                chunk_message = chunk.choices[0].delta.reasoning_content # 获取思维链
                print(chunk_message, end="", flush=True)  # 打印思维链
                if chunk_message:
                    reasoning_content += chunk_message  # 累加思维链
            else:
                chunk_message = chunk.choices[0].delta.content # 获取回复
                print(chunk_message, end="", flush=True)  # 打印回复
                if chunk_message: 
                    content += chunk_message  # 累加回复
                
        print("\n")
        return content.strip()  # 返回回复内容

        full_response = ""
        for chunk in response:
            chunk_message = chunk.choices[0].delta.content
            print(chunk_message, end='', flush=True)
            if chunk_message:
                # print(chunk_message, end='', flush=True)
                full_response += chunk_message
        print("\n")
        return full_response.strip()
    else:
        output = response.choices[0].message.content  # 获取回复内容
        print(output)  # 打印回复
        return output  # 返回回复内容


# -------------------------------
# 微信机器人逻辑
# -------------------------------

# 微信客户端对象，全局变量
wx = None


def safe_add_listen(nickname: str, retries: int = 3, delay: float = 1.5) -> bool:
    """
    安全添加监听：对 wx.AddListenChat 进行重试，避免微信UI未就绪导致的 LookupError。
    """
    for attempt in range(1, retries + 1):
        try:
            wx.AddListenChat(nickname=nickname, callback=message_handle_callback)
            print(f"添加监听成功: {nickname}")
            return True
        except LookupError as e:
            # 常见报错: Find Control Timeout: IDS_FAV_SEARCH_RESULT ListControl
            print(
                f"AddListenChat 失败({attempt}/{retries}): {e}\n"
                "提示: 请确保微信 Windows 客户端已登录，主界面处于前台且会话列表可见；"
                "不要最小化微信窗口。稍后将自动重试..."
            )
            try:
                # 尝试重新启动监听，以触发UI刷新
                wx.StartListening()
            except Exception:
                pass
            time.sleep(delay)
        except Exception as e:
            print(f"AddListenChat 异常({attempt}/{retries}): {e}，稍后重试...")
            time.sleep(delay)
    print(f"添加监听失败（已重试 {retries} 次）: {nickname}")
    return False


def init_wx_listeners():
    """
    初始化微信监听器，根据新版 listen_rules 配置添加监听用户和群聊
    """
    global wx, AtMe
    if not wx:
        print("本次未获取客户端，正在初始化微信客户端...")
        wx = WeChat()

    AtMe = "@"+wx.nickname # 绑定AtMe
    print('启动wxautox监听器...')
    wx.StartListening() # 启动监听器
    
    # 添加管理员监听（带重试）
    if cmd:
        if safe_add_listen(cmd):
            print(f"添加管理员监听完成: {cmd}")
    
    # 获取新版监听规则配置
    listen_rules = config.get('listen_rules', {})
    
    # 添加用户监听（仅启用的用户）
    user_rules = listen_rules.get('user_rules', [])
    enabled_users = [rule['name'] for rule in user_rules if rule.get('enabled', True)]
    
    # 如果新版配置为空，回退到旧版配置
    if not enabled_users:
        enabled_users = listen_list
    
    for user in enabled_users:
        if user and user != cmd:  # 避免重复添加管理员
            if safe_add_listen(user):
                print(f"添加用户监听: {user}")
    
    # 添加群组监听（检查全局开关和各群组启用状态）
    global_bot_enabled = listen_rules.get('global_bot_enabled', True)
    if global_bot_enabled:
        group_rules = listen_rules.get('group_rules', [])
        enabled_groups = [rule['name'] for rule in group_rules if rule.get('enabled', True)]
        
        # 如果新版配置为空，回退到旧版配置
        if not enabled_groups and group_switch == "True":
            enabled_groups = group
        
        for group_name in enabled_groups:
            if group_name:
                if safe_add_listen(group_name):
                    print(f"添加群组监听: {group_name}")
        
        if enabled_groups:
            print(f"群组监听设置完成，共 {len(enabled_groups)} 个群组")
    else:
        print("全局群机器人开关已关闭，跳过群组监听")
    
    print(f"监听器初始化完成 - 用户: {len(enabled_users)}, 群组: {len([rule for rule in listen_rules.get('group_rules', []) if rule.get('enabled', True)]) if global_bot_enabled else 0}")
def message_handle_callback(msg, chat):
    """消息处理回调"""
    text = datetime.now().strftime("%Y/%m/%d %H:%M:%S ") + f'类型：{msg.type} 属性：{msg.attr} 窗口：{chat.who} 发送人：{msg.sender_remark} - 消息：{msg.content}'
    print(text)
    if isinstance(msg, FriendMessage): # 好友群友的消息
        process_message(chat, msg)
    elif isinstance(msg, SystemMessage): # 系统的消息
        if group_welcome: # 群新人欢迎语开关
            send_group_welcome_msg(chat, msg) # 获取子窗口对象与消息对象送入处理

def get_api_config_for_chat(chat_who):
    """
    根据聊天对象获取对应的API配置
    
    Args:
        chat_who: 聊天窗口标识（用户名或群名）
        
    Returns:
        dict: API配置字典，如果没找到返回默认配置
    """
    try:
        # 从配置文件中获取API配置和监听规则
        api_configs = config.get('api_configs', [])
        listen_rules = config.get('listen_rules', {})
        default_api_id = config.get('default_api_id', '') or listen_rules.get('default_api_id', '')
        
        # 首先检查用户规则
        user_rules = listen_rules.get('user_rules', [])
        for user_rule in user_rules:
            if user_rule.get('name') == chat_who and user_rule.get('enabled', True):
                user_api_id = user_rule.get('api_id')
                if user_api_id:
                    # 查找对应的API配置
                    for api_config in api_configs:
                        if api_config.get('id') == user_api_id and api_config.get('enabled', True):
                            return api_config
        
        # 检查群组规则
        group_rules = listen_rules.get('group_rules', [])
        for group_rule in group_rules:
            if group_rule.get('name') == chat_who and group_rule.get('enabled', True):
                group_api_id = group_rule.get('api_id')
                if group_api_id:
                    # 查找对应的API配置
                    for api_config in api_configs:
                        if api_config.get('id') == group_api_id and api_config.get('enabled', True):
                            return api_config
        
        # 如果没有找到专用配置，使用默认配置
        if default_api_id:
            for api_config in api_configs:
                if api_config.get('id') == default_api_id and api_config.get('enabled', True):
                    return api_config
        
        # 如果还没找到，返回第一个启用的API配置
        for api_config in api_configs:
            if api_config.get('enabled', True):
                return api_config
                
        # 如果没有任何API配置，返回兼容旧版本的默认配置
        return {
            'id': 'default',
            'name': '默认配置',
            'platform': 'openai',
            'api_key': api_key,
            'base_url': base_url,
            'model': DS_NOW_MOD,
            'prompt': config.get('prompt', prompt),  # 使用配置文件中的prompt
            'enabled': True
        }
        
    except Exception as e:
        print(f"获取API配置失败: {e}")
        # 返回兼容配置
        return {
            'id': 'fallback',
            'name': '备用配置',
            'platform': 'openai',
            'api_key': api_key,
            'base_url': base_url,
            'model': DS_NOW_MOD,
            'prompt': config.get('prompt', prompt),  # 使用配置文件中的prompt
            'enabled': True
        }

def wx_send_ai(chat, message):
    """
    异步AI消息处理（新版本）
    使用异步消息队列处理，支持并发和详细日志
    """
    try:
        # 获取对应的API配置
        api_config = get_api_config_for_chat(chat.who)
        
        # 记录消息接收日志
        print(f"{now_time()}[异步处理] 收到消息 - 窗口: {chat.who}, 内容: {message.content[:100]}")
        print(f"{now_time()}[异步处理] 使用API配置: {api_config.get('name', 'Unknown')} ({api_config.get('id', 'Unknown')})")
        
        # 发送到异步处理队列
        async_message_handler.sync_add_message(chat, message, api_config)
        
        # 可选：立即回复处理状态（避免用户等待焦虑）
        # chat.SendMsg("收到消息，正在为您处理...")
        
    except Exception as e:
        print(f"{now_time()}[错误] 异步处理失败: {e}")
        print(traceback.format_exc())
        # 降级到同步处理
        wx_send_ai_sync(chat, message)

def wx_send_ai_sync(chat, message):
    """
    同步AI消息处理（备用）
    保留原有的同步处理逻辑作为备用
    """
    # 默认：回复 AI 生成的消息
    # chat.SendMsg("已接收，请耐心等待回答")
    try:
        reply = deepseek_chat(message.content, DS_NOW_MOD, stream=True, prompt=prompt)
    except Exception:
        print(traceback.format_exc())
        reply = "API返回错误，请稍后再试"
            
    if len(reply) >= 2000:
        segments = split_long_text(reply)
        # 处理分段后的内容
        for index, segment in enumerate(segments, 1):
            # print(f"第 {index} 段内容（{len(segment)} 字符）: {segment}")
            reply_ = segment
            chat.SendMsg(reply_)
    else:
        chat.SendMsg(reply)
def find_new_group_friend(msg, flag):
    '''
    寻找新的群好友
    msg：系统消息
    flag：若是邀请的消息则填3，扫描二维码的消息则填1
    '''
    text = msg
    try:
        first_quote_content = text.split('"')[flag]
    except:
        first_quote_content = text.split('"')[1]
    # print("新人:", first_quote_content)  # 输出: Gary10
    return first_quote_content
def send_group_welcome_msg(chat, message):
    '''
    监听群组欢迎新人
    '''
    print(now_time()+f"{chat.who} 系统消息:", message.content)
    if "加入群聊" in message.content:
        new_friend = find_new_group_friend(message.content, 1) # 扫码加入
        print(f"{chat.who} 新群友:", new_friend)
        time.sleep(2) # 等待2秒微信刷新
        chat.SendMsg(msg=group_welcome_msg, at=new_friend)
    elif "加入了群聊" in message.content:
        new_friend = find_new_group_friend(message.content, 3) # 个人邀请
        print(f"{chat.who} 新群友:", new_friend)
        time.sleep(2) # 等待2秒微信刷新
        chat.SendMsg(msg=group_welcome_msg, at=new_friend)
    return
def process_message(chat, message):
    """
    处理收到的单条消息，并根据不同情况调用 DeepSeek API 或执行命令

    参数:
        chat: 消息所属的会话对象（包含 who 等信息）
        message: 消息对象（包含 type, sender, content 等信息）
    """
    global DS_NOW_MOD, group_welcome, group_welcome_msg
    # 只处理好友消息
    if message.attr != 'friend':
        return

    print(now_time()+f"\n{chat.who} 窗口 {message.sender} 说：{message.content}")
    # print(message.info) # 原始消息


    # 检查是否为需要监听的对象（使用新版 listen_rules）
    listen_rules = config.get('listen_rules', {})
    
    # 检查用户规则
    user_rules = listen_rules.get('user_rules', [])
    user_enabled = any(rule['name'] == chat.who and rule.get('enabled', True) for rule in user_rules)
    
    # 检查群组规则
    group_rules = listen_rules.get('group_rules', [])
    group_enabled = any(rule['name'] == chat.who and rule.get('enabled', True) for rule in group_rules)
    global_bot_enabled = listen_rules.get('global_bot_enabled', True)
    
    # 如果新版配置为空，回退到旧版配置
    if not user_rules:
        user_enabled = chat.who in listen_list
    if not group_rules:
        group_enabled = chat.who in group and group_switch == "True"
    
    is_monitored = user_enabled or (group_enabled and global_bot_enabled) or (chat.who == cmd)
    if not is_monitored:
        return

    # 如果用户询问“你是谁”，直接回复机器人名称
    if message.content == '你是谁' or re.sub(AtMe, "", message.content).strip() == '你是谁':
        chat.SendMsg('我是' + bot_name)
        return 


    # 群聊中：根据群组规则的 at_required 设置决定是否需要 @
    if group_enabled and global_bot_enabled:
        # 查找当前群组的 at_required 设置
        at_required = True  # 默认需要 @
        for rule in group_rules:
            if rule['name'] == chat.who:
                at_required = rule.get('at_required', True)
                break
        
        # 如果新版配置为空，回退到旧版逻辑（总是需要 @）
        if not group_rules and chat.who in group:
            at_required = True
        
        # 根据 at_required 设置决定是否处理消息
        should_reply = False
        content_to_process = message.content
        
        if at_required:
            # 需要 @ 才回复
            if AtMe in message.content:
                should_reply = True
                content_to_process = re.sub(AtMe, "", message.content).strip()
        else:
            # 不需要 @，直接回复
            should_reply = True
            content_to_process = message.content
        
        if should_reply:
            print(now_time()+f"群组 {chat.who} 消息（@要求: {at_required}）：{content_to_process}")
            # 创建临时消息对象用于异步处理
            temp_message = type('obj', (object,), {'content': content_to_process, 'sender': message.sender, 'attr': message.attr})
            # 使用异步处理群组消息
            wx_send_ai(chat, temp_message)
            return
        return

    # 命令处理：当消息来自指定命令账号时，执行相应的管理操作
    if chat.who == cmd:
        if "/添加用户" in message.content:
            try:
                user_to_add = re.sub("/添加用户", "", message.content).strip()
                add_user(user_to_add)
                init_wx_listeners()
                chat.SendMsg(message.content + ' 完成\n' + ", ".join(listen_list))
            except:
                user_to_add = re.sub("/添加用户", "", message.content).strip()
                remove_user(user_to_add)
                init_wx_listeners()
                chat.SendMsg(message.content + ' 失败\n请检查添加的用户是否为好友或者备注是否正确或者备注名 昵称中是否含有非法中文字符\n当前用户：\n'+", ".join(listen_list))
        elif "/删除用户" in message.content:
            user_to_remove = re.sub("/删除用户", "", message.content).strip()
            # if is_wxautox: # 如果是wxautox则删除监听窗口
            wx.RemoveListenChat(user_to_remove) # 删除监听窗口
            remove_user(user_to_remove)
            # init_wx_listeners()
            chat.SendMsg(message.content + ' 完成\n' + ", ".join(listen_list))
        elif "/当前用户" == message.content:
            chat.SendMsg(message.content + '\n' + ", ".join(listen_list))
        elif "/当前群" == message.content:
            chat.SendMsg(message.content + '\n'+ ", ".join(group))
        elif "/群机器人状态" == message.content:
            if group_switch == 'False':
                chat.SendMsg(message.content + '为关闭')
            else:
                chat.SendMsg(message.content + '为开启')
        elif "/添加群" in message.content:
            try:
                new_group = re.sub("/添加群", "", message.content).strip()
                # if is_wxautox: # 如果是wxautox则删除群组监听窗口
                # wx.RemoveListenChat(config.get('group')) # 删除群组监听窗口
                add_group(new_group)
                init_wx_listeners()
                chat.SendMsg(message.content + ' 完成\n' + ", ".join(group))
            except Exception:
                print(traceback.format_exc())
                remove_group(new_group)
                set_group_switch("False")
                init_wx_listeners()
                chat.SendMsg(message.content + ' 失败\n请重新配置群名称或者检查机器人号是否在群内\n当前群:\n' + ", ".join(group) + '\n当前群机器人状态:'+group_switch)
        elif "/删除群" in message.content:
            group_to_remove = re.sub("/删除群", "", message.content).strip()
            wx.RemoveListenChat(group_to_remove) # 删除监听窗口
            remove_group(group_to_remove) # 在配置中删除
            chat.SendMsg(message.content + ' 完成\n' + ", ".join(group))
        elif message.content == "/开启群机器人":
            try:
                set_group_switch("True")
                init_wx_listeners()
                chat.SendMsg(message.content + ' 完成\n' +'当前群：\n'+", ".join(group))
            except Exception as e:
                print(traceback.format_exc())
                set_group_switch("False")
                init_wx_listeners()
                chat.SendMsg(message.content + ' 失败\n请重新配置群名称或者检查机器人号是否在群或者群名中是否含有非法中文字符\n当前群:'+ ", ".join(group) +'\n当前群机器人状态:'+group_switch)
        elif message.content == "/关闭群机器人":
            set_group_switch("False")
            # if is_wxautox: # 如果是wxautox则删除群组监听窗口
            for user in group:
                wx.RemoveListenChat(user) # 删除群组监听窗口
            # init_wx_listeners()
            chat.SendMsg(message.content + ' 完成\n' +'当前群：\n' + ", ".join(group))
        elif message.content == "/开启群机器人欢迎语":
            group_welcome = True
            chat.SendMsg(message.content + ' 完成\n' +'当前群：\n' + ", ".join(group))
        elif message.content == "/关闭群机器人欢迎语":
            group_welcome = False
            chat.SendMsg(message.content + ' 完成\n' +'当前群：\n' + ", ".join(group))
        elif message.content == "/群机器人欢迎语状态":
            if group_welcome:
                chat.SendMsg("/群机器人欢迎语状态 为开启\n" +'当前群：\n' + ", ".join(group))
            else:
                chat.SendMsg("/群机器人欢迎语状态 为关闭\n" +'当前群：\n' + ", ".join(group))
        elif message.content == "/当前群机器人欢迎语":
            chat.SendMsg(message.content + '\n' +group_welcome_msg)
        elif "/更改群机器人欢迎语为" in message.content:
            new_welcome = re.sub("/更改群机器人欢迎语为", "", message.content).strip()
            group_welcome_msg = new_welcome
            chat.SendMsg('群机器人欢迎语已更新\n' + group_welcome_msg)
        elif message.content == "/当前模型":
            chat.SendMsg(message.content + " " + DS_NOW_MOD)
        elif message.content == "/切换模型1": # 1
            # global DS_NOW_MOD
            DS_NOW_MOD = model1
            chat.SendMsg(message.content + ' 完成\n当前模型:' + DS_NOW_MOD)
        elif message.content == "/切换模型2": # 2
            # global DS_NOW_MOD
            DS_NOW_MOD = model2
            chat.SendMsg(message.content + ' 完成\n当前模型:' + DS_NOW_MOD)
        elif message.content == "/切换模型3": # 3
            # global DS_NOW_MOD
            DS_NOW_MOD = model3
            chat.SendMsg(message.content + ' 完成\n当前模型:' + DS_NOW_MOD)
        elif message.content == "/切换模型4": # 4
            # global DS_NOW_MOD
            DS_NOW_MOD = model4
            chat.SendMsg(message.content + ' 完成\n当前模型:' + DS_NOW_MOD)
        elif message.content == "/当前AI设定":
            chat.SendMsg('当前AI设定：\n' + config['prompt'])
        elif "/更改AI设定为" in message.content or "/更改ai设定为" in message.content:
            if "AI设定" in message.content:
                new_prompt = re.sub("/更改AI设定为", "", message.content).strip()
            else:
                new_prompt = re.sub("/更改ai设定为", "", message.content).strip()
            config['prompt'] = new_prompt
            save_config()
            refresh_config()
            chat.SendMsg('AI设定已更新\n' + config['prompt'])
        elif message.content == "/更新配置":
            refresh_config()
            init_wx_listeners()
            chat.SendMsg(message.content + ' 完成\n')
        elif message.content == "/当前版本":
            global ver
            chat.SendMsg(message.content + 'wxbot_' + ver + '\n' + ver_log + '\n作者:dolphi')
        elif message.content == "/指令" or message.content == "指令":
            commands = (
                '指令列表[发送中括号里内容]：\n'
                '[/当前用户] (返回当前监听用户列表)\n'
                '[/添加用户***] （将用户***添加进监听列表）\n'
                '[/删除用户***]\n'
                '[/当前群]\n'
                '[/添加群***] \n'
                '[/删除群***] \n'
                '[/开启群机器人]\n'
                '[/关闭群机器人]\n'
                '[/群机器人状态]\n'
                '[/开启群机器人欢迎语]\n'
                '[/关闭群机器人欢迎语]\n'
                '[/群机器人欢迎语状态]\n'
                '[/当前群机器人欢迎语]\n'
                '[/更改群机器人欢迎语为***]\n'
                '[/当前模型] （返回当前模型）\n'
                '[/切换模型1] （切换回复模型为配置中的 model1）\n'
                '[/切换模型2]\n'
                '[/切换模型3]\n'
                '[/切换模型4]\n'
                '[/当前AI设定] （返回当前AI设定）\n'
                '[/更改AI设定为***] （更改AI设定，***为AI设定）\n'
                '[/更新配置] （若在程序运行时修改过配置，请发送此指令以更新配置）\n'
                '[/当前版本] (返回当前版本)\n'
                '作者:dolphi  若有非法传播请告知'
            )
            chat.SendMsg(commands)
        else:
            # 默认：回复 AI 生成的消息
            wx_send_ai(chat, message)
        return

    # 普通好友消息：先提示已接收，再调用 AI 接口获取回复
    wx_send_ai(chat, message)

run_flag = True  # 运行标记，用于控制程序退出
def main():
    # 输出版本信息
    global ver, run_flag
    print(f"wxbot\n版本: wxbot_{ver}\n作者: dolphi")
    
    # 加载配置并更新全局变量
    refresh_config()
    
    # 启动异步消息处理器
    print(now_time() + "启动异步消息处理器...")
    async_message_handler.async_handler.start()

    try:
        # 初始化微信监听器
        init_wx_listeners()
    except Exception as e:
        print(traceback.format_exc())
        print("初始化微信监听器失败，请检查微信是否启动登录正确")
        run_flag = False

    
    wait_time = 1  # 每1秒检查一次新消息
    check_interval = 10  # 每10次循环检查一次进程状态
    check_counter = 0
    print(now_time()+'siver_wxbot初始化完成，开始监听消息(作者:dolphi)')
    
    # 发送启动通知给管理员（如果配置了）
    if cmd and wx:
        try:
            wx.SendMsg('siver_wxbot初始化完成', who=cmd)
        except:
            print("发送启动通知给管理员失败")
    
    # 主循环：保持运行
    while run_flag:
        time.sleep(wait_time)  # 等待1秒
        check_counter += 1
        
        # 定期输出异步处理器状态
        if check_counter % check_interval == 0:
            status = async_message_handler.async_handler.get_status()
            if status['queue_size'] > 0 or status['processing_count'] > 0:
                print(f"{now_time()}异步处理器状态: 队列:{status['queue_size']}, 处理中:{status['processing_count']}")
    
    print(now_time()+'siver_wxbot已停止运行')

def start_bot():
    """启动机器人"""
    main()  # 执行主函数
def stop_bot():
    """停止机器人"""
    global run_flag, wx
    print(now_time() + "正在停止机器人...")
    
    # 停止异步消息处理器（优先处理队列中的消息）
    try:
        print(now_time() + "停止异步消息处理器...")
        async_message_handler.async_handler.stop()
    except Exception as e:
        print(f"停止异步消息处理器时出现异常: {e}")
    
    # 停止wxauto监听器（若已初始化）
    try:
        print(now_time() + "停止微信监听器...")
        if wx:
            wx.StopListening()
    except Exception as e:
        print(f"停止监听器时出现异常: {e}")
    
    # 标记主循环退出
    run_flag = False
    print(now_time()+"siver_wxbot已停止运行")

if __name__ == "__main__":
    main()  # 执行主函数

