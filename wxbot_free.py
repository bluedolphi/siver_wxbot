#!/usr/bin/env python3
# 作者：https://siver.top
# 版本：free
ver = "free"         # 当前版本
import time
import json
import re
import traceback
from wxauto import WeChat
from openai import OpenAI

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
cmd = ""            # 命令接收账号（管理员）
group = ""          # 群聊ID
model1 = ""         # 模型1标识
model2 = ""         # 模型2标识

# 当前使用的模型和 API 客户端
DS_NOW_MOD = ""
client = None

# DS API 模型常量（可根据需要更换）
DS_R1 = "deepseek-reasoner"
DS_V3 = "deepseek-chat"
siliconflow_DS_R1 = "deepseek-ai/DeepSeek-R1"
siliconflow_DS_V3 = "deepseek-ai/DeepSeek-V3"


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
    """
    global listen_list, api_key, base_url, AtMe, cmd, group, model1, model2, DS_NOW_MOD, client
    listen_list = config.get('listen_list', [])
    api_key = config.get('api_key', "")
    base_url = config.get('base_url', "")
    AtMe = config.get('AtMe', "")
    cmd = config.get('cmd', "")
    group = config.get('group', "")
    model1 = config.get('model1', "")
    model2 = config.get('model2', "")

    # 默认使用模型1
    DS_NOW_MOD = model1
    # 初始化 OpenAI 客户端
    client = OpenAI(api_key=api_key, base_url=base_url)
    print("全局配置更新完成")


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
        with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
            json.dump(config, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print("保存配置文件失败:", e)


def add_user(name):
    """
    添加用户至监听列表，并更新配置
    """
    if name not in config.get('listen_list', []):
        config['listen_list'].append(name)
        save_config()
        refresh_config()
        print("添加后的 Listen List:", config['listen_list'])
    else:
        print(f"用户 {name} 已在监听列表中")


def remove_user(name):
    """
    从监听列表中删除指定用户，并更新配置
    """
    if name in config.get('listen_list', []):
        config['listen_list'].remove(name)
        save_config()
        refresh_config()
        print("删除后的 Listen List:", config['listen_list'])
    else:
        print(f"用户 {name} 不在监听列表中")


def set_group(new_group):
    """
    更改监听的群聊ID，并更新配置
    """
    config['group'] = new_group
    save_config()
    refresh_config()
    print("群组已更改为", config['group'])


def set_group_switch(switch_value):
    """
    设置是否启用群机器人（"True" 或 "False"），并更新配置
    """
    config['group_switch'] = switch_value
    save_config()
    refresh_config()
    print("群开关设置为", config['group_switch'])


# -------------------------------
# DeepSeek API 调用
# -------------------------------

def deepseek_chat(message, model, stream):
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
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": message},
            ],
            stream=stream
        )
    except Exception as e:
        print("调用 DeepSeek API 出错:", e)
        raise

    # 流式输出处理
    if stream:
        reasoning_content = ""
        content = ""
        for chunk in response:
            if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content: # 判断是否为思维链
                chunk_message = chunk.choices[0].delta.reasoning_content # 获取思维链
                print(chunk_message, end="", flush=True)
                if chunk_message:
                    reasoning_content += chunk_message
            else:
                chunk_message = chunk.choices[0].delta.content # 获取回复
                print(chunk_message, end="", flush=True)
                if chunk_message:
                    content += chunk_message

        print("\n")
        return content.strip()

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
        output = response.choices[0].message.content
        print(output)
     
