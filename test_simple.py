#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试脚本 - 验证API连接和基本功能
"""

import json
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """测试配置文件加载"""
    print("测试配置文件加载...")
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✅ 配置文件加载成功")
        
        # 检查API配置
        api_configs = config.get('api_configs', [])
        print(f"找到 {len(api_configs)} 个API配置")
        
        for api in api_configs:
            status = "启用" if api.get('enabled') else "禁用"
            print(f"  - {api.get('name')}: {api.get('platform')} ({status})")
        
        return config
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return None

def test_api_import():
    """测试API模块导入"""
    print("\n测试API模块导入...")
    try:
        from API import RAGflowAPIConnector, DifyAPIConnector
        print("✅ API模块导入成功")
        return True
    except Exception as e:
        print(f"❌ API模块导入失败: {e}")
        return False

def test_ragflow_api(config):
    """测试RAGFlow API连接"""
    print("\n测试RAGFlow API连接...")
    try:
        from API import RAGflowAPIConnector
        
        # 找到RAGFlow配置
        ragflow_config = None
        for api in config.get('api_configs', []):
            if api.get('platform') == 'ragflow' and api.get('enabled'):
                ragflow_config = api
                break
        
        if not ragflow_config:
            print("❌ 未找到启用的RAGFlow配置")
            return False
        
        print(f"使用配置: {ragflow_config['name']}")
        
        # 创建连接器
        connector = RAGflowAPIConnector(
            api_key=ragflow_config['api_key'],
            base_url=ragflow_config['base_url'],
            name="test_connector"
        )
        
        # 测试API调用
        messages = [{"role": "user", "content": "你好，这是一个测试"}]
        response, _ = connector.chat(messages, stream=False)
        
        print(f"✅ RAGFlow API调用成功")
        print(f"响应: {response[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ RAGFlow API测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_async_handler_import():
    """测试异步处理器导入"""
    print("\n测试异步处理器导入...")
    try:
        from async_message_handler import AsyncMessageHandler
        print("✅ 异步处理器导入成功")
        return True
    except Exception as e:
        print(f"❌ 异步处理器导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("dolphin_wxbot 功能测试")
    print("=" * 50)
    
    # 测试配置加载
    config = test_config()
    if not config:
        return
    
    # 测试API模块导入
    if not test_api_import():
        return
    
    # 测试异步处理器导入
    if not test_async_handler_import():
        return
    
    # 测试RAGFlow API
    test_ragflow_api(config)
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
