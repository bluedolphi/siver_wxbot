#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步消息处理器测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import json
from async_message_handler import async_handler

# 模拟聊天对象和消息对象
class MockChat:
    def __init__(self, who):
        self.who = who
        
    def SendMsg(self, msg, at=None):
        if at:
            print(f"[模拟发送到 {self.who}] @{at}: {msg}")
        else:
            print(f"[模拟发送到 {self.who}] {msg}")

class MockMessage:
    def __init__(self, content, sender=None):
        self.content = content
        self.sender = sender
        self.attr = 'friend'

def test_async_handler():
    """测试异步消息处理器"""
    print("=== 异步消息处理器测试 ===")
    
    # 启动处理器
    print("启动异步处理器...")
    async_handler.start()
    time.sleep(2)  # 等待启动完成
    
    # 获取状态
    status = async_handler.get_status()
    print(f"处理器状态: {status}")
    
    # 测试配置
    test_config = {
        'id': 'test_api',
        'name': 'Test RAGFlow',
        'platform': 'ragflow',
        'api_key': 'ragflow-NkZTYwZjZhNzkwYjExZjA4ZmM0ODJhMj',
        'base_url': 'http://ragflow.56lai.cc/api/v1/chats_openai/b4d06cf2790a11f0a74482a266f296aa/chat/completions',
        'prompt': 'You are a helpful assistant.',
        'enabled': True
    }
    
    # 创建模拟对象
    chat = MockChat("测试用户")
    message = MockMessage("你好，请介绍一下自己", sender="test_user")
    
    print("\n发送测试消息...")
    
    # 使用同步接口添加消息
    import async_message_handler
    async_message_handler.sync_add_message(chat, message, test_config)
    
    # 等待处理完成
    print("等待消息处理...")
    for i in range(30):  # 等待最多30秒
        time.sleep(1)
        status = async_handler.get_status()
        print(f"第{i+1}秒 - 队列:{status['queue_size']}, 处理中:{status['processing_count']}")
        
        if status['queue_size'] == 0 and status['processing_count'] == 0:
            print("消息处理完成!")
            break
    else:
        print("等待超时，可能处理失败")
    
    # 显示日志
    print("\n=== 处理日志 ===")
    logs = async_handler.get_logs()
    for log in logs[-10:]:  # 显示最后10条日志
        print(log)
    
    # 停止处理器
    print("\n停止异步处理器...")
    async_handler.stop()
    
    print("测试完成!")

if __name__ == "__main__":
    test_async_handler()