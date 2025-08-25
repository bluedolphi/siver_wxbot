#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAGFlow API 连接器测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from API import RAGFlowAPIConnector, APIConnectorFactory

def test_ragflow_direct():
    """直接测试 RAGFlow 连接器"""
    print("=== 直接测试 RAGFlow 连接器 ===")
    
    # 测试参数
    api_key = "ragflow-NkZTYwZjZhNzkwYjExZjA4ZmM0ODJhMj"
    base_url = "http://ragflow.56lai.cc/api/v1/chats_openai/b4d06cf2790a11f0a74482a266f296aa/chat/completions"
    
    # 创建连接器
    connector = RAGFlowAPIConnector(
        api_key=api_key,
        base_url=base_url,
        name="RAGFlow测试"
    )
    
    print(f"API Key: {api_key}")
    print(f"Base URL: {base_url}")
    print(f"提取的 chat_id: {connector.chat_id}")
    print()
    
    # 测试聊天功能（非流式）
    print("--- 测试非流式聊天 ---")
    messages = [{"role": "user", "content": "Say this is a test!"}]
    
    try:
        response, request_time = connector.chat(messages, stream=False)
        print(f"响应内容: {response}")
        print(f"请求耗时: {request_time:.2f}秒")
    except Exception as e:
        print(f"非流式测试失败: {e}")
    
    print()
    
    # 测试搜索功能
    print("--- 测试搜索功能 ---")
    try:
        response, request_time = connector.search("你好，请介绍一下自己")
        print(f"搜索响应: {response}")
        print(f"请求耗时: {request_time:.2f}秒")
    except Exception as e:
        print(f"搜索测试失败: {e}")

def test_ragflow_factory():
    """通过工厂测试 RAGFlow 连接器"""
    print("\n=== 通过工厂测试 RAGFlow 连接器 ===")
    
    # 测试参数
    api_key = "ragflow-NkZTYwZjZhNzkwYjExZjA4ZmM0ODJhMj"
    base_url = "http://ragflow.56lai.cc/api/v1/chats_openai/b4d06cf2790a11f0a74482a266f296aa/chat/completions"
    
    # 通过工厂创建连接器
    connector = APIConnectorFactory.create_connector(
        platform="ragflow",
        api_key=api_key,
        base_url=base_url,
        name="RAGFlow工厂测试"
    )
    
    print(f"连接器类型: {type(connector).__name__}")
    print(f"连接器名称: {connector.name}")
    
    # 测试聊天功能
    messages = [{"role": "user", "content": "请用中文回答：什么是人工智能？"}]
    
    try:
        response, request_time = connector.chat(messages)
        print(f"工厂测试响应: {response}")
        print(f"请求耗时: {request_time:.2f}秒")
    except Exception as e:
        print(f"工厂测试失败: {e}")

def test_ragflow_stream():
    """测试 RAGFlow 流式响应"""
    print("\n=== 测试 RAGFlow 流式响应 ===")
    
    # 测试参数
    api_key = "ragflow-NkZTYwZjZhNzkwYjExZjA4ZmM0ODJhMj"
    base_url = "http://ragflow.56lai.cc/api/v1/chats_openai/b4d06cf2790a11f0a74482a266f296aa/chat/completions"
    
    connector = RAGFlowAPIConnector(
        api_key=api_key,
        base_url=base_url,
        name="RAGFlow流式测试"
    )
    
    messages = [{"role": "user", "content": "请详细介绍一下机器学习的基本概念"}]
    
    try:
        response, request_time = connector.chat(messages, stream=True)
        print(f"流式响应内容: {response}")
        print(f"请求耗时: {request_time:.2f}秒")
    except Exception as e:
        print(f"流式测试失败: {e}")

if __name__ == "__main__":
    print("开始测试 RAGFlow API 连接器...")
    print("=" * 50)
    
    # 运行所有测试
    test_ragflow_direct()
    test_ragflow_factory()
    test_ragflow_stream()
    
    print("\n" + "=" * 50)
    print("测试完成！")
