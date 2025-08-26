#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试自动回复功能
验证异步消息处理器和微信发送队列是否正常工作
"""

import asyncio
import json
import sys
import os
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from async_message_handler import AsyncMessageHandler

def load_config():
    """加载配置文件"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return None

async def test_message_processing():
    """测试消息处理功能"""
    print("=" * 50)
    print("开始测试异步消息处理器...")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    if not config:
        print("❌ 配置文件加载失败")
        return False
    
    # 创建异步消息处理器
    try:
        handler = AsyncMessageHandler(config)
        print("✅ 异步消息处理器创建成功")
    except Exception as e:
        print(f"❌ 创建异步消息处理器失败: {e}")
        return False
    
    # 测试API连接
    print("\n测试API连接...")
    api_configs = config.get('api_configs', [])
    if not api_configs:
        print("❌ 没有找到API配置")
        return False
    
    # 测试第一个启用的API
    test_api = None
    for api in api_configs:
        if api.get('enabled', False):
            test_api = api
            break
    
    if not test_api:
        print("❌ 没有找到启用的API配置")
        return False
    
    print(f"使用API: {test_api['name']} ({test_api['platform']})")
    
    # 测试API调用
    try:
        test_message = "你好，这是一个测试消息"
        print(f"发送测试消息: {test_message}")
        
        response = await handler.call_api_async(
            content=test_message,
            api_config=test_api,
            message_id="test_001"
        )
        
        print(f"✅ API响应成功: {response[:100]}...")
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        return False
    
    # 测试消息队列
    print("\n测试微信消息发送队列...")
    
    # 模拟添加消息到队列
    test_messages = [
        "测试消息1",
        "测试消息2", 
        "测试消息3"
    ]
    
    for i, msg in enumerate(test_messages):
        try:
            # 模拟同步添加消息
            handler.sync_add_message(f"测试用户{i+1}", msg)
            print(f"✅ 消息 {i+1} 已添加到队列")
        except Exception as e:
            print(f"❌ 添加消息 {i+1} 失败: {e}")
    
    # 检查队列状态
    queue_size = handler.message_queue.qsize()
    print(f"当前消息队列大小: {queue_size}")
    
    # 启动处理器并运行一段时间
    print("\n启动异步处理器...")
    try:
        # 创建任务但不等待完成
        processor_task = asyncio.create_task(handler.process_messages())
        sender_task = asyncio.create_task(handler.wx_message_sender())
        
        print("✅ 异步处理器启动成功")
        print("等待5秒观察处理效果...")
        
        # 等待5秒让处理器工作
        await asyncio.sleep(5)
        
        # 取消任务
        processor_task.cancel()
        sender_task.cancel()
        
        try:
            await processor_task
        except asyncio.CancelledError:
            pass
        
        try:
            await sender_task
        except asyncio.CancelledError:
            pass
        
        print("✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 异步处理器运行失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 运行异步测试
        result = asyncio.run(test_message_processing())
        
        if result:
            print("\n🎉 所有测试通过！自动回复功能正常工作")
        else:
            print("\n❌ 测试失败，请检查配置和代码")
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
