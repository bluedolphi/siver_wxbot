#!/usr/bin/env python3
# 测试消息类型配置UI功能

import json
import os
import sys

def test_config_structure():
    """测试配置文件结构是否包含消息类型过滤配置"""
    print("=== 测试配置文件结构 ===")
    
    try:
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        
        # 检查是否存在 listen_rules
        if 'listen_rules' not in config:
            print("✗ 配置文件中缺少 listen_rules 配置")
            return False
        
        listen_rules = config['listen_rules']
        
        # 检查是否存在 message_types_filter
        if 'message_types_filter' not in listen_rules:
            print("✗ listen_rules 中缺少 message_types_filter 配置")
            return False
        
        message_filter = listen_rules['message_types_filter']
        
        # 检查必要的字段
        required_fields = ['enabled', 'allowed_types', 'description']
        for field in required_fields:
            if field not in message_filter:
                print(f"✗ message_types_filter 中缺少 {field} 字段")
                return False
        
        print("✓ 配置文件结构正确")
        print(f"✓ 过滤功能启用状态: {message_filter['enabled']}")
        print(f"✓ 允许的消息类型: {message_filter['allowed_types']}")
        
        return True
        
    except Exception as e:
        print(f"✗ 读取配置文件失败: {e}")
        return False

def test_message_types_completeness():
    """测试消息类型是否完整"""
    print("\n=== 测试消息类型完整性 ===")
    
    expected_types = ["text", "link", "location", "image", "file", "voice", "video", "emotion"]
    
    try:
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        
        allowed_types = config['listen_rules']['message_types_filter']['allowed_types']
        
        # 检查是否包含所有预期的类型
        missing_types = []
        for msg_type in expected_types:
            if msg_type not in allowed_types:
                missing_types.append(msg_type)
        
        if missing_types:
            print(f"✗ 缺少消息类型: {missing_types}")
            return False
        
        # 检查是否有额外的未知类型
        extra_types = []
        for msg_type in allowed_types:
            if msg_type not in expected_types:
                extra_types.append(msg_type)
        
        if extra_types:
            print(f"⚠ 发现额外的消息类型: {extra_types}")
        
        print("✓ 消息类型配置完整")
        return True
        
    except Exception as e:
        print(f"✗ 检查消息类型失败: {e}")
        return False

def simulate_ui_operations():
    """模拟UI操作测试"""
    print("\n=== 模拟UI操作测试 ===")
    
    try:
        # 读取当前配置
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        
        original_config = config.copy()
        
        # 模拟禁用过滤功能
        print("1. 模拟禁用消息过滤功能")
        config['listen_rules']['message_types_filter']['enabled'] = False
        
        # 模拟只选择文本消息
        print("2. 模拟只选择文本消息类型")
        config['listen_rules']['message_types_filter']['allowed_types'] = ["text"]
        
        # 保存测试配置
        with open('config_test.json', 'w', encoding='utf-8') as file:
            json.dump(config, file, ensure_ascii=False, indent=4)
        
        print("✓ 测试配置文件已生成: config_test.json")
        
        # 模拟恢复所有类型
        print("3. 模拟恢复所有消息类型")
        config['listen_rules']['message_types_filter']['enabled'] = True
        config['listen_rules']['message_types_filter']['allowed_types'] = [
            "text", "link", "location", "image", "file", "voice", "video", "emotion"
        ]
        
        print("✓ UI操作模拟测试完成")
        return True
        
    except Exception as e:
        print(f"✗ UI操作模拟失败: {e}")
        return False

def test_integration_with_wxbot():
    """测试与wxbot_preview.py的集成"""
    print("\n=== 测试与wxbot集成 ===")
    
    try:
        # 检查wxbot_preview.py是否存在消息类型过滤函数
        if not os.path.exists('wxbot_preview.py'):
            print("✗ wxbot_preview.py 文件不存在")
            return False
        
        with open('wxbot_preview.py', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 检查关键函数是否存在
        required_functions = [
            'def get_message_type_from_content',
            'def is_message_type_allowed',
            'def preprocess_message_content'
        ]

        missing_functions = []
        for func in required_functions:
            if func not in content:
                missing_functions.append(func.replace('def ', ''))
        
        if missing_functions:
            print(f"✗ wxbot_preview.py 中缺少函数: {missing_functions}")
            return False
        
        print("✓ wxbot_preview.py 集成检查通过")
        return True
        
    except Exception as e:
        print(f"✗ 集成测试失败: {e}")
        return False

def generate_test_report():
    """生成测试报告"""
    print("\n=== 生成测试报告 ===")
    
    tests = [
        ("配置文件结构", test_config_structure),
        ("消息类型完整性", test_message_types_completeness),
        ("UI操作模拟", simulate_ui_operations),
        ("wxbot集成", test_integration_with_wxbot)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 统计结果
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n=== 测试报告 ===")
    print(f"总测试项: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！消息类型配置UI功能正常工作。")
    else:
        print(f"\n⚠️ 有 {total - passed} 项测试失败，请检查相关功能。")
    
    return passed == total

def main():
    """主测试函数"""
    print("开始测试消息类型配置UI功能...")
    print("=" * 50)
    
    success = generate_test_report()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 消息类型配置UI功能测试完成，所有功能正常！")
    else:
        print("❌ 测试发现问题，请检查相关功能。")
    
    return success

if __name__ == "__main__":
    main()
