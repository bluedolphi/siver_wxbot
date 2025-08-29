#!/usr/bin/env python3
# 测试消息类型过滤功能

import json
import sys
import os

# 添加当前目录到路径，以便导入wxbot_preview模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_test_config():
    """加载测试配置"""
    global config
    try:
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
            print("✓ 配置文件加载成功")
            return True
    except Exception as e:
        print(f"✗ 配置文件加载失败: {e}")
        return False

def get_message_type_from_content(content):
    """根据消息内容判断消息类型（复制的函数用于测试）"""
    if content == "[链接]":
        return "link"
    elif content == "[位置]":
        return "location"
    elif content == "[图片]":
        return "image"
    elif content == "[文件]":
        return "file"
    elif content == "[语音]":
        return "voice"
    elif content == "[视频]":
        return "video"
    elif content == "[表情]":
        return "emotion"
    else:
        return "text"

def is_message_type_allowed(message_type):
    """检查消息类型是否在允许处理的列表中（复制的函数用于测试）"""
    try:
        # 获取消息类型过滤配置
        listen_rules = config.get('listen_rules', {})
        message_filter = listen_rules.get('message_types_filter', {})

        # 如果过滤功能未启用，允许所有类型
        if not message_filter.get('enabled', True):
            return True

        # 获取允许的消息类型列表
        allowed_types = message_filter.get('allowed_types', [])

        # 如果没有配置允许列表，默认允许所有类型
        if not allowed_types:
            return True

        # 检查当前消息类型是否在允许列表中
        return message_type in allowed_types

    except Exception as e:
        print(f"[WARNING] 检查消息类型过滤配置失败: {e}")
        # 出错时默认允许处理
        return True

def test_message_type_detection():
    """测试消息类型检测功能"""
    print("\n=== 测试消息类型检测 ===")

    test_cases = [
        ("[链接]", "link"),
        ("[位置]", "location"),
        ("[图片]", "image"),
        ("[文件]", "file"),
        ("[语音]", "voice"),
        ("[视频]", "video"),
        ("[表情]", "emotion"),
        ("普通文本消息", "text"),
        ("Hello World", "text")
    ]

    for content, expected_type in test_cases:
        actual_type = get_message_type_from_content(content)
        status = "✓" if actual_type == expected_type else "✗"
        print(f"{status} '{content}' -> {actual_type} (期望: {expected_type})")

def test_message_filter_logic():
    """测试消息过滤逻辑"""
    print("\n=== 测试消息过滤逻辑 ===")

    # 测试允许的类型
    allowed_types = ["text", "link", "location", "image", "file", "voice", "video", "emotion"]
    for msg_type in allowed_types:
        result = is_message_type_allowed(msg_type)
        status = "✓" if result else "✗"
        print(f"{status} 类型 '{msg_type}' 允许处理: {result}")

    # 测试不允许的类型（假设的类型）
    disallowed_types = ["unknown", "system", "recall"]
    for msg_type in disallowed_types:
        result = is_message_type_allowed(msg_type)
        status = "✓" if not result else "✗"
        print(f"{status} 类型 '{msg_type}' 不允许处理: {not result}")

def preprocess_message_content_test(message):
    """预处理消息内容的测试版本"""
    content = message.content

    # 判断消息类型
    message_type = get_message_type_from_content(content)

    # 检查是否允许处理此类型的消息
    if not is_message_type_allowed(message_type):
        print(f"[INFO] 消息类型 '{message_type}' 不在允许处理列表中，跳过处理")
        return None  # 返回None表示不处理此消息

    print(f"[INFO] 处理消息类型: {message_type}")

    if content == "[链接]":
        return f"用户分享了一个链接：\n标题：未知链接\nURL：无法获取URL\n\n请根据这个链接内容进行回复。"
    elif content == "[位置]":
        return "用户分享了一个位置，但无法获取其名称。"
    elif content == "[图片]":
        return "用户发送了一张图片，请询问图片相关信息或提供图片处理建议"
    elif content == "[文件]":
        return "用户发送了一个文件，请询问文件相关信息或提供文件处理建议"
    elif content == "[语音]":
        return "用户发送了一条语音消息，请询问语音内容或提供语音相关回复"
    elif content == "[视频]":
        return "用户发送了一个视频，请询问视频内容或提供视频相关回复"
    elif content == "[表情]":
        return "用户发送了一个表情，请给出适当的回应"

    # 默认返回原始文本内容
    return content

def test_preprocess_with_filter():
    """测试预处理函数的过滤功能"""
    print("\n=== 测试预处理函数过滤 ===")

    # 创建模拟消息对象
    class MockMessage:
        def __init__(self, content):
            self.content = content

    # 测试允许的消息类型
    test_messages = [
        "[链接]",
        "[图片]",
        "[语音]",
        "普通文本消息"
    ]

    for content in test_messages:
        message = MockMessage(content)
        result = preprocess_message_content_test(message)
        status = "✓" if result is not None else "✗"
        print(f"{status} 消息 '{content}' 处理结果: {'允许' if result is not None else '跳过'}")

def test_config_modification():
    """测试配置修改对过滤的影响"""
    print("\n=== 测试配置修改影响 ===")

    # 备份原始配置
    original_config = config.copy()

    try:
        # 测试禁用过滤功能
        print("1. 测试禁用过滤功能")
        config['listen_rules']['message_types_filter']['enabled'] = False

        result = is_message_type_allowed("unknown_type")
        status = "✓" if result else "✗"
        print(f"{status} 禁用过滤后，未知类型允许处理: {result}")

        # 测试启用过滤功能
        print("2. 测试启用过滤功能")
        config['listen_rules']['message_types_filter']['enabled'] = True
        result = is_message_type_allowed("unknown_type")
        status = "✓" if not result else "✗"
        print(f"{status} 启用过滤后，未知类型不允许处理: {not result}")

        # 测试修改允许类型列表
        print("3. 测试修改允许类型列表")
        config['listen_rules']['message_types_filter']['allowed_types'] = ["text"]
        result_text = is_message_type_allowed("text")
        result_image = is_message_type_allowed("image")

        status1 = "✓" if result_text else "✗"
        status2 = "✓" if not result_image else "✗"
        print(f"{status1} 仅允许text类型，text允许: {result_text}")
        print(f"{status2} 仅允许text类型，image不允许: {not result_image}")

    finally:
        # 恢复原始配置
        config.clear()
        config.update(original_config)

def main():
    """主测试函数"""
    print("开始测试消息类型过滤功能...")
    
    # 加载配置
    if not load_test_config():
        return
    
    # 运行各项测试
    test_message_type_detection()
    test_message_filter_logic()
    test_preprocess_with_filter()
    test_config_modification()
    
    print("\n=== 测试完成 ===")
    print("如果所有测试项都显示 ✓，说明消息类型过滤功能正常工作")

if __name__ == "__main__":
    main()
