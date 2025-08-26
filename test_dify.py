#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Dify API 连接器
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from API import DifyAPIConnector

def test_dify_direct():
    """直接测试 Dify 连接器"""
    print("=== 直接测试 Dify 连接器 ===")
    
    # 从配置中获取的 Dify API 参数
    api_key = "app-ieEC20o5GR6l7KnuGszAcW2t"
    base_url = "http://dify.56lai.cc/v1"
    
    print(f"API Key: {api_key}")
    print(f"Base URL: {base_url}")
    
    # 创建连接器实例
    connector = DifyAPIConnector(
        api_key=api_key,
        base_url=base_url,
        name="Dify测试"
    )
    
    print(f"连接器名称: {connector.name}")
    print(f"实际请求URL: {connector.base_url}")
    print()
    
    # 测试搜索功能
    print("--- 测试搜索功能 ---")
    try:
        response, request_time = connector.search("你好，请介绍一下自己")
        print(f"搜索响应: {response}")
        print(f"请求耗时: {request_time:.2f}秒")
    except Exception as e:
        print(f"搜索测试失败: {e}")
    print()
    
    # 测试聊天功能
    print("--- 测试聊天功能 ---")
    try:
        messages = [
            {"role": "user", "content": "Say this is a test!"}
        ]
        response, request_time = connector.chat(messages)
        print(f"聊天响应: {response}")
        print(f"请求耗时: {request_time:.2f}秒")
    except Exception as e:
        print(f"聊天测试失败: {e}")
    print()
    
    # 测试多轮对话
    print("--- 测试多轮对话 ---")
    try:
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！我是AI助手，有什么可以帮助你的吗？"},
            {"role": "user", "content": "请详细介绍一下机器学习的基本概念"}
        ]
        response, request_time = connector.chat(messages)
        print(f"多轮对话响应: {response}")
        print(f"请求耗时: {request_time:.2f}秒")
    except Exception as e:
        print(f"多轮对话测试失败: {e}")
    print()

def test_dify_with_params():
    """测试 Dify 连接器的参数传递"""
    print("=== 测试 Dify 参数传递 ===")
    
    api_key = "app-ieEC20o5GR6l7KnuGszAcW2t"
    base_url = "http://dify.56lai.cc/v1"
    
    connector = DifyAPIConnector(
        api_key=api_key,
        base_url=base_url,
        name="Dify参数测试"
    )
    
    # 测试带自定义用户ID的请求
    print("--- 测试自定义用户ID ---")
    try:
        response, request_time = connector.search(
            "测试自定义用户ID", 
            user="test_user_123"
        )
        print(f"自定义用户ID响应: {response}")
        print(f"请求耗时: {request_time:.2f}秒")
    except Exception as e:
        print(f"自定义用户ID测试失败: {e}")
    print()
    
    # 测试带输入变量的请求
    print("--- 测试输入变量 ---")
    try:
        response, request_time = connector.search(
            "使用输入变量进行测试",
            inputs={"variable1": "value1", "variable2": "value2"}
        )
        print(f"输入变量响应: {response}")
        print(f"请求耗时: {request_time:.2f}秒")
    except Exception as e:
        print(f"输入变量测试失败: {e}")
    print()

if __name__ == "__main__":
    print("开始测试 Dify API 连接器...")
    print("=" * 50)
    
    test_dify_direct()
    test_dify_with_params()
    
    print("=" * 50)
    print("测试完成！")
