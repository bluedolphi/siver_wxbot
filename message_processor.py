#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息处理器模块
用于处理不同类型的微信消息，提取实际可用内容
作者：dolphi
"""

import logging
from pathlib import Path
from typing import Union, Optional

class MessageProcessor:
    """消息处理器 - 处理各种类型的微信消息"""
    
    def __init__(self, enable_ocr: bool = False, download_path: str = None):
        """
        初始化消息处理器
        
        Args:
            enable_ocr: 是否启用图片OCR识别
            download_path: 文件下载路径
        """
        self.enable_ocr = enable_ocr
        self.download_path = download_path or "./downloads"
        
        # 确保下载目录存在
        Path(self.download_path).mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
    
    def extract_content(self, msg) -> str:
        """
        根据消息类型提取实际可用内容
        
        Args:
            msg: 微信消息对象
            
        Returns:
            提取的实际内容字符串
        """
        try:
            msg_type = getattr(msg, 'type', 'unknown')
            self.logger.info(f"处理消息类型: {msg_type}")
            
            if msg_type == 'text':
                # 文本消息直接返回内容
                return self._extract_text_content(msg)
            
            elif msg_type == 'voice':
                # 语音消息转换为文本
                return self._extract_voice_content(msg)
            
            elif msg_type == 'link':
                # 链接消息返回实际URL
                return self._extract_link_content(msg)
            
            elif msg_type == 'image':
                # 图片消息处理
                return self._extract_image_content(msg)
            
            elif msg_type == 'file':
                # 文件消息处理
                return self._extract_file_content(msg)
            
            elif msg_type == 'location':
                # 位置消息返回具体地址
                return self._extract_location_content(msg)
            
            elif msg_type == 'quote':
                # 引用消息返回引用内容+回复内容
                return self._extract_quote_content(msg)
            
            elif msg_type == 'merge':
                # 合并转发消息展开所有内容
                return self._extract_merge_content(msg)
            
            elif msg_type == 'personal_card':
                # 名片消息处理
                return self._extract_card_content(msg)
            
            elif msg_type == 'emotion':
                # 表情消息处理
                return self._extract_emotion_content(msg)
            
            else:
                # 其他类型消息返回原始内容
                return self._extract_other_content(msg)
                
        except Exception as e:
            self.logger.error(f"消息内容提取失败: {e}")
            return f"[消息处理失败: {str(e)}]"
    
    def _extract_text_content(self, msg) -> str:
        """提取文本消息内容"""
        return getattr(msg, 'content', '') or '[空文本消息]'
    
    def _extract_voice_content(self, msg) -> str:
        """提取语音消息内容"""
        try:
            # 尝试使用wxauto的语音转文字功能
            if hasattr(msg, 'to_text'):
                text_content = msg.to_text()
                self.logger.info(f"语音转文字成功: {text_content[:50]}...")
                return text_content
            else:
                # 如果没有转换功能，返回语音消息提示
                content = getattr(msg, 'content', '[语音消息]')
                self.logger.warning("消息对象不支持语音转文字功能")
                return f"[语音消息] {content} - 请手动播放查看内容"
        except Exception as e:
            self.logger.error(f"语音转文字失败: {e}")
            content = getattr(msg, 'content', '[语音消息]')
            return f"[语音消息] {content} - 转换失败: {str(e)}"
    
    def _extract_link_content(self, msg) -> str:
        """提取链接消息内容"""
        try:
            # 尝试获取真实URL (Plus版本功能)
            if hasattr(msg, 'get_url'):
                url = msg.get_url()
                self.logger.info(f"提取链接URL: {url}")
                return url
            else:
                # 降级处理：从info中提取链接信息或使用预处理内容
                content = getattr(msg, 'content', '[链接消息]')

                # 如果content已经是预处理过的链接信息，直接返回
                if "用户分享了一个链接" in content or "标题：" in content:
                    return content

                self.logger.info(f"链接消息内容: {content}")
                return f"[链接消息] {content}"
        except Exception as e:
            self.logger.error(f"链接提取失败: {e}")
            content = getattr(msg, 'content', '[链接消息]')
            return f"[链接消息] {content}"
    
    def _extract_image_content(self, msg) -> str:
        """提取图片消息内容"""
        try:
            # 下载图片
            if hasattr(msg, 'download'):
                img_path = msg.download(dir_path=self.download_path)
                self.logger.info(f"图片下载成功: {img_path}")
                
                # 如果启用OCR，尝试识别图片中的文字
                if self.enable_ocr:
                    try:
                        ocr_text = self._perform_ocr(img_path)
                        if ocr_text.strip():
                            return f"[图片内容] {ocr_text}"
                        else:
                            return f"[图片消息 - 无文字内容] 路径: {img_path}"
                    except Exception as ocr_e:
                        self.logger.error(f"OCR识别失败: {ocr_e}")
                        return f"[图片消息] 路径: {img_path}"
                else:
                    return f"[图片消息] 路径: {img_path}"
            else:
                return "[图片消息 - 无法下载]"
        except Exception as e:
            self.logger.error(f"图片处理失败: {e}")
            return f"[图片消息 - 处理失败: {str(e)}]"
    
    def _extract_file_content(self, msg) -> str:
        """提取文件消息内容"""
        try:
            filename = getattr(msg, 'content', '未知文件')
            
            if hasattr(msg, 'download'):
                file_path = msg.download(dir_path=self.download_path)
                self.logger.info(f"文件下载成功: {file_path}")
                return f"[文件] {filename} - 已下载到: {file_path}"
            else:
                return f"[文件] {filename} - 无法下载"
        except Exception as e:
            self.logger.error(f"文件处理失败: {e}")
            filename = getattr(msg, 'content', '未知文件')
            return f"[文件] {filename} - 处理失败: {str(e)}"
    
    def _extract_location_content(self, msg) -> str:
        """提取位置消息内容"""
        try:
            # 尝试获取地址信息
            address = getattr(msg, 'address', None)
            if address:
                return f"[位置] {address}"
            else:
                content = getattr(msg, 'content', '[位置信息]')

                # 如果content已经是预处理过的位置信息，直接返回
                if "用户分享了一个位置" in content or "名称：" in content:
                    return content

                return f"[位置] {content}"
        except Exception as e:
            self.logger.error(f"位置信息提取失败: {e}")
            content = getattr(msg, 'content', '[位置信息]')
            return f"[位置消息] {content}"
    
    def _extract_quote_content(self, msg) -> str:
        """提取引用消息内容"""
        try:
            quote_content = getattr(msg, 'quote_content', '')
            reply_content = getattr(msg, 'content', '')
            
            if quote_content and reply_content:
                return f"[引用回复] 引用: {quote_content} | 回复: {reply_content}"
            elif reply_content:
                return f"[引用回复] {reply_content}"
            else:
                return "[引用消息]"
        except Exception as e:
            self.logger.error(f"引用消息处理失败: {e}")
            return "[引用消息 - 处理失败]"
    
    def _extract_merge_content(self, msg) -> str:
        """提取合并转发消息内容"""
        try:
            # 尝试获取合并消息内容 (Plus版本功能)
            if hasattr(msg, 'get_messages'):
                messages = msg.get_messages()
                if messages:
                    content = "\n".join(messages[:5])  # 限制显示前5条
                    if len(messages) > 5:
                        content += f"\n... (共{len(messages)}条消息)"
                    return f"[合并转发] {content}"
            
            # 降级处理
            content = getattr(msg, 'content', '[合并转发消息]')
            return f"[合并转发] {content}"
        except Exception as e:
            self.logger.error(f"合并消息处理失败: {e}")
            return "[合并转发消息 - 处理失败]"
    
    def _extract_card_content(self, msg) -> str:
        """提取名片消息内容"""
        try:
            content = getattr(msg, 'content', '未知联系人')
            return f"[名片] {content}"
        except Exception as e:
            self.logger.error(f"名片消息处理失败: {e}")
            return "[名片消息 - 处理失败]"
    
    def _extract_emotion_content(self, msg) -> str:
        """提取表情消息内容"""
        try:
            content = getattr(msg, 'content', '[表情]')
            return f"[表情] {content}"
        except Exception as e:
            self.logger.error(f"表情消息处理失败: {e}")
            return "[表情消息 - 处理失败]"
    
    def _extract_other_content(self, msg) -> str:
        """提取其他类型消息内容"""
        try:
            msg_type = getattr(msg, 'type', 'unknown')
            content = getattr(msg, 'content', '')

            # 特殊处理一些常见的其他类型
            if msg_type == 'personal_card' or '[名片]' in content:
                return f"[名片消息] {content}"
            elif msg_type == 'emotion' or '[表情]' in content:
                return f"[表情消息] {content}"
            elif content:
                return f"[{msg_type}消息] {content}"
            else:
                return f"[{msg_type}消息]"
        except Exception as e:
            self.logger.error(f"其他消息处理失败: {e}")
            return "[未知消息类型]"
    
    def _perform_ocr(self, image_path: Union[str, Path]) -> str:
        """
        对图片进行OCR识别
        
        Args:
            image_path: 图片路径
            
        Returns:
            识别出的文字内容
        """
        try:
            # 这里可以集成各种OCR服务
            # 例如：百度OCR、腾讯OCR、PaddleOCR等
            
            # 示例：使用PaddleOCR (需要安装 paddlepaddle 和 paddleocr)
            try:
                from paddleocr import PaddleOCR
                ocr = PaddleOCR(use_angle_cls=True, lang='ch')
                result = ocr.ocr(str(image_path), cls=True)
                
                if result and result[0]:
                    text_lines = []
                    for line in result[0]:
                        if len(line) > 1 and line[1]:
                            text_lines.append(line[1][0])
                    return '\n'.join(text_lines)
                else:
                    return ""
            except ImportError:
                self.logger.warning("PaddleOCR未安装，跳过OCR识别")
                return ""
            
        except Exception as e:
            self.logger.error(f"OCR识别失败: {e}")
            return ""
