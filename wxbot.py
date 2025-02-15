
# 作者：https://siver.top
ver = 1.2
print("wxbot\n版本:wxbot_"+ver+"\n作者:https://siver.top")


import time
from wxauto import WeChat
import re
import traceback
from openai import OpenAI
import json
# 读取 config.json 文件
try:
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
        print("打开配置文件完成")
except:
    print("打开配置文件失败！！！请检查配置文件")
    while True:
        time.sleep(100)

def up_config(): # 在运行时更新配置
    global config
    try:
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
            print("打开配置文件完成")
    except:
        print("打开配置文件失败！！！请检查配置文件")
        while True:
            time.sleep(100)
    global listen_list, api_key, base_url, AtMe, cmd, group, model1, model2
    # 将数据加载回到变量中
    listen_list = config['listen_list']
    api_key = config['api_key']
    base_url = config['base_url']
    AtMe = config['AtMe']
    cmd = config['cmd']
    group = config['group']
    model1 = config['model1']
    model2 = config['model2']
    # 更新模型与API URL
    global DS_NOW_MOD, client
    DS_NOW_MOD = model1
    client = OpenAI(api_key=api_key, base_url=base_url)
    print("更新配置完成")


def add_user_list(name):
    config['listen_list'].append(name)
    # 写回 config.json 文件
    with open('.\config.json', 'w', encoding='utf-8') as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    
    up_config()
    print("添加后的 Listen List:", config['listen_list'])
def del_user_list(name):
    # 从 listen_list 中删除指定数据
    item_to_remove = name
    if item_to_remove in config['listen_list']:
        config['listen_list'].remove(item_to_remove)

    # 写回 config.json 文件
    with open('config.json', 'w', encoding='utf-8') as file:
        json.dump(config, file, ensure_ascii=False, indent=4)

    up_config()
    print("删除后的 Listen List:", config['listen_list'])
def set_group(group):
    # 从
    config['group'] = group

    # 写回 config.json 文件
    with open('.\config.json', 'w', encoding='utf-8') as file:
        json.dump(config, file, ensure_ascii=False, indent=4)

    up_config()
    print("更改群组为", config['group'])
def set_group_switch(switch):
    # 从
    config['group_switch'] = switch

    # 写回 config.json 文件
    with open('.\config.json', 'w', encoding='utf-8') as file:
        json.dump(config, file, ensure_ascii=False, indent=4)

    up_config()
    print("开启群开关", config['group_switch'])
# 将数据加载到变量中
listen_list = config['listen_list']
api_key = config['api_key']
base_url = config['base_url']
AtMe = config['AtMe']
cmd = config['cmd']
group = config['group']
model1 = config['model1']
model2 = config['model2']
# DS API 调用
DS_R1 = "deepseek-reasoner"
DS_V3 = "deepseek-chat"
siliconflow_DS_R1 = "deepseek-ai/DeepSeek-R1"
siliconflow_DS_V3 = "deepseek-ai/DeepSeek-V3"

DS_NOW_MOD = model1

# client = OpenAI(api_key="sk-d67f6ddb26e94cb1b2aec9c743ef9b56", base_url="https://api.deepseek.com") # DS官方
# client = OpenAI(api_key="sk-gipbdqrktcrohvezcpdofegiefxegwycjdrwctfiacktlojl", base_url="https://api.siliconflow.cn/v1") # 硅基流动
client = OpenAI(api_key=api_key, base_url=base_url)
def DeekSeepChat(Msg, model, stream): # Msg->用户消息  model->模型选择  stream->是否流式输出(Ture/False)
    response = client.chat.completions.create(
        # model="deepseek-chat", # V3模型
        # model='deepseek-reasoner', # R1模型
        model=model, # R1模型
        messages=[
            {"role": "system", "content": "You are a helpful assistant"}, # 
            {"role": "user", "content": Msg},
        ],
        stream=stream
    )
    if stream:
        # 定义一个变量来累积所有的 chunk_message
        full_response = ""
        # 逐步接收并处理响应
        for chunk in response:
            chunk_message = chunk.choices[0].delta.content
            print(chunk_message, end='', flush=True)
            if chunk_message != None:
                full_response += chunk_message  # 将每个 chunk_message 累积到 full_response 中
        print("\n")
        return full_response.strip()
    else:
        out = response.choices[0].message.content
        print(out)
        return out
# DeekSeepChat("你好", DS_NOW_MOD, True) # 测试

# AtMe = '@Siver. ' # @我
wx = WeChat()
def wxauto_init():
    global wx
    wx = WeChat()
    for i in listen_list:
        wx.AddListenChat(who=i)  # 添加监听对象
    if config['group_switch'] == "True":
        wx.AddListenChat(who=config['group'])  # 添加监听对象
        print('群组设置监听完成')
    print('设置监听完成')
wxauto_init()

# 持续监听消息，有消息则对接大模型进行回复
wait = 1  # 设置1秒查看一次是否有新消息

while True:
    msgs = wx.GetListenMessage()
    for c in msgs:
        msg = msgs.get(c)   # 获取消息内容
        for i in msg:
            if i.type == 'friend':
                # 打印原始消息
                print(i.sender+" 问："+i.content)
                # 若监听对象消息不在列表内，则退出
                for lis in listen_list:
                    flag = False
                    if c.who == lis or (c.who == config['group'] and config['group_switch'] == "True"):
                        flag = True
                        break
                if flag == False: break
                # ===================================================
                # 处理消息逻辑
                if i.content == '你是谁' or re.sub(AtMe, "", i.content) == '你是谁':
                    c.SendMsg('我是'+config['bot_name'])  # 向``发送微信客户端消息

                else:
                    if c.who == config['group']: # 群消息@回答
                        if AtMe in i.content:
                            NoAtMsg = re.sub(AtMe, "", i.content)
                            # 获取AI回答
                            try:
                                reply = DeekSeepChat(NoAtMsg, DS_NOW_MOD, True)
                            except:
                                print(traceback.format_exc())
                                reply = "API返回错误，请稍后再试"

                            c.SendMsg('@'+i.sender+' '+reply)  # 向``发送微信客户端消息
                    # cmd
                    elif c.who == cmd:
                        if "添加用户" in i.content:
                            NoAddMsg = re.sub("添加用户", "", i.content)
                            add_user_list(NoAddMsg)
                            wxauto_init()
                            c.SendMsg(i.content + '完成\n' + "  ".join(config['listen_list']))
                        elif "删除用户" in i.content:
                            NoDelMsg = re.sub("删除用户", "", i.content)
                            del_user_list(NoDelMsg)
                            wxauto_init()
                            c.SendMsg(i.content + '完成\n' + "  ".join(config['listen_list']))
                        elif "更改群为" in i.content:
                            NoSetMsg = re.sub("更改群为", "", i.content)
                            set_group(NoSetMsg)
                            wxauto_init()
                            c.SendMsg(i.content + '完成\n')
                        elif "开启群机器人" == i.content:
                            set_group_switch("True")
                            wxauto_init()
                            c.SendMsg(i.content + '完成\n')
                        elif "关闭群机器人" == i.content:
                            set_group_switch("False")
                            wxauto_init()
                            c.SendMsg(i.content + '完成\n')
                        elif "当前模型" == i.content:
                            c.SendMsg(i.content + DS_NOW_MOD)
                        elif "切换模型1" == i.content:
                            DS_NOW_MOD = model1
                            c.SendMsg(i.content + '完成\n')
                        elif "切换模型2" == i.content:
                            DS_NOW_MOD = model2
                            c.SendMsg(i.content + '完成\n')
                        elif "更新配置" == i.content:
                            up_config()
                            wxauto_init()
                            c.SendMsg(i.content + '完成\n')
                        elif "指令" == i.content:
                            msg = '指令列表（发送引号里内容)\n"添加用户***"（将用户***添加进监听列表）\n"删除用户***"\n"更改群为***"(更改监听的群，只能监听一个群)\n"开启群机器人"\n"关闭群机器人"\n"当前模型"(返回当前模型)\n"切换模型1"(切换回复模型为config里的model1)\n"切换模型2"(切换回复模型为config里的model2)\n"更新配置"(若在程序运行时手动修改过config.json 请发送一遍以将你修改的配置更新进程序)'
                            c.SendMsg(msg) # 返回可用指令
                        else: # 给管理员返回普通Ai消息
                            # ===================================================
                            c.SendMsg("已接收，请耐心等待回答")  # 向``发送微信客户端消息
                            # 获取AI回答
                            try:
                                reply = DeekSeepChat(i.content, DS_NOW_MOD, True)
                            except:
                                print(traceback.format_exc())
                                reply = "API返回错误，请稍后再试"
                            # 回复消息
                            c.SendMsg(reply)  # 向``发送微信客户端消息
                    else:
                        # ===================================================
                        c.SendMsg("已接收，请耐心等待回答")  # 向``发送微信客户端消息
                        # 获取AI回答
                        try:
                            reply = DeekSeepChat(i.content, DS_NOW_MOD, True)
                        except:
                            print(traceback.format_exc())
                            reply = "API返回错误，请稍后再试"
                        # 回复消息
                        c.SendMsg(reply)  # 向``发送微信客户端消息

    time.sleep(wait)



'''# 硅基流动 requests 库调用
import requests

siliconflow_DS_R1 = "deepseek-ai/DeepSeek-R1"
siliconflow_DS_V3 = "deepseek-ai/DeepSeek-V3"
def siliconflow_Chat(Msg, model):
    url = "https://api.siliconflow.cn/v1/chat/completions"
    API = "Bearer sk-gipbdqrktcrohvezcpdofegiefxegwycjdrwctfiacktlojl"
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": Msg}
        ],
        "temperature": 0.7,
        "max_tokens": 4096
    }

    headers = {
        "Authorization": API, # API填写
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.ok:
        out = response.json()['choices'][0]['message']['content']
        print(out)
        return out
    else:
        print("Error:", response.status_code)
        print(response.text)
        return "API返回错误，请稍后再试"
'''
