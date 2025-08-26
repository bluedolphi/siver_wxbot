#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步消息处理模块
用于处理WeChat机器人的消息队列、并发控制和异步API调用
作者：dolphi
"""

import asyncio
import threading
import queue
import time
import json
from datetime import datetime
from collections import deque
from typing import Dict, List, Optional, Tuple
import traceback
import logging

class AsyncMessageHandler:
    """异步消息处理器"""
    
    def __init__(self, config=None, max_concurrent=5, max_log_lines=200):
        """
        初始化异步消息处理器
        
        Args:
            config: 配置字典
            max_concurrent: 最大并发处理数量
            max_log_lines: 最大日志行数
        """
        self.config = config or {}
        self.max_concurrent = max_concurrent
        self.max_log_lines = max_log_lines
        
        # 消息队列
        self.message_queue = asyncio.Queue()
        self.processing_messages = {}  # 正在处理的消息 {message_id: task}
        
        # 微信RPA发送队列 - 解决并发控制权冲突
        self.wx_send_queue = asyncio.Queue()
        self.wx_send_lock = asyncio.Lock()  # 微信发送操作锁
        self.wx_sender_task = None  # 专用的微信发送任务
        
        # 日志系统
        self.process_logs = deque(maxlen=max_log_lines)  # 自动限制行数
        self.log_lock = threading.Lock()
        
        # 事件循环
        self.loop = None
        self.handler_task = None
        
        # 状态标记
        self.is_running = False
        
        # API客户端（从wxbot_preview导入）
        self.client = None
        self.wx = None
        
    def log_process(self, level: str, message: str, message_id: str = None):
        """
        记录处理日志
        
        Args:
            level: 日志级别 (INFO, WARNING, ERROR)
            message: 日志信息
            message_id: 消息ID（可选）
        """
        with self.log_lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}][{level}]"
            if message_id:
                log_entry += f"[{message_id}]"
            log_entry += f" {message}"
            
            self.process_logs.append(log_entry)
            print(log_entry)  # 同时输出到控制台
    
    def get_logs(self, lines: int = None) -> List[str]:
        """
        获取处理日志
        
        Args:
            lines: 获取的行数，None表示获取全部
            
        Returns:
            日志列表
        """
        with self.log_lock:
            if lines is None:
                return list(self.process_logs)
            else:
                return list(self.process_logs)[-lines:]
    
    def clear_logs(self):
        """清空日志"""
        with self.log_lock:
            self.process_logs.clear()
    
    async def add_message(self, chat, message, api_config: Dict = None, priority: int = 0):
        """
        添加消息到处理队列
        
        Args:
            chat: 聊天对象
            message: 消息对象
            api_config: API配置字典
            priority: 优先级（数字越小优先级越高）
        """
        message_id = f"{chat.who}_{int(time.time()*1000)}"
        
        message_data = {
            'id': message_id,
            'chat': chat,
            'message': message,
            'api_config': api_config,
            'priority': priority,
            'timestamp': time.time(),
            'status': 'queued'
        }
        
        await self.message_queue.put((priority, message_id, message_data))
        self.log_process("INFO", f"消息已加入队列: {message.content[:50]}", message_id)
    
    async def process_single_message(self, message_data: Dict):
        """
        处理单个消息
        
        Args:
            message_data: 消息数据字典
        """
        message_id = message_data['id']
        chat = message_data['chat']
        message = message_data['message']
        api_config = message_data['api_config']
        
        try:
            # 更新处理状态
            message_data['status'] = 'processing'
            self.log_process("INFO", f"开始处理消息: {message.content[:50]}", message_id)
            
            # 立即回复处理中状态（可选）
            if hasattr(chat, 'SendMsg'):
                # chat.SendMsg("收到消息，正在处理中...")
                pass
            
            # 调用API处理消息
            start_time = time.time()
            reply = await self.call_api_async(message.content, api_config, message_id)
            process_time = time.time() - start_time
            
            self.log_process("INFO", f"API调用完成，耗时: {process_time:.2f}秒", message_id)
            
            # 处理长消息分段并加入发送队列
            if len(reply) >= 2000:
                segments = self.split_long_text(reply)
                self.log_process("INFO", f"长消息分为 {len(segments)} 段发送", message_id)
                for index, segment in enumerate(segments, 1):
                    # 加入微信发送队列而不是直接发送
                    send_data = {
                        'chat': chat,
                        'message': segment,
                        'at_user': message.sender if hasattr(message, 'sender') and message.sender else None,
                        'message_id': message_id,
                        'segment_info': f"{index}/{len(segments)}"
                    }
                    await self.wx_send_queue.put(send_data)
            else:
                # 单条消息也加入发送队列
                send_data = {
                    'chat': chat,
                    'message': reply,
                    'at_user': message.sender if hasattr(message, 'sender') and message.sender else None,
                    'message_id': message_id,
                    'segment_info': None
                }
                await self.wx_send_queue.put(send_data)
                self.log_process("INFO", f"消息已加入发送队列，长度: {len(reply)} 字符", message_id)
            
            message_data['status'] = 'completed'
            self.log_process("INFO", f"消息处理完成: {message.content[:50]}", message_id)
            
        except Exception as e:
            message_data['status'] = 'error'
            error_msg = f"消息处理失败: {str(e)}"
            self.log_process("ERROR", error_msg, message_id)
            
            # 发送错误提示给用户（也通过队列发送）
            if hasattr(chat, 'SendMsg'):
                error_send_data = {
                    'chat': chat,
                    'message': "抱歉，处理您的消息时出现错误，请稍后再试。",
                    'at_user': None,
                    'message_id': message_id,
                    'segment_info': None
                }
                await self.wx_send_queue.put(error_send_data)
        
        finally:
            # 清理处理中的消息记录
            if message_id in self.processing_messages:
                del self.processing_messages[message_id]
    
    async def call_api_async(self, content: str, api_config: Dict, message_id: str) -> str:
        """
        异步调用API
        
        Args:
            content: 消息内容
            api_config: API配置
            message_id: 消息ID
            
        Returns:
            API回复内容
        """
        try:
            platform = api_config.get('platform', 'openai').lower()
            api_key = api_config.get('api_key', '')
            base_url = api_config.get('base_url', '')
            model = api_config.get('model', 'gpt-3.5-turbo')
            prompt = api_config.get('prompt', 'You are a helpful assistant.')
            
            self.log_process("INFO", f"开始API调用，平台: {platform}, 模型: {model if platform != 'ragflow' else 'N/A'}, 提示词长度: {len(prompt)}字符", message_id)
            
            # 根据平台选择不同的调用方式
            if platform == 'ragflow':
                response_text = await self._call_ragflow_api(api_key, base_url, content, message_id)
            elif platform == 'coze':
                response_text = await self._call_coze_api(api_key, base_url, content, message_id)
            elif platform == 'dify':
                response_text = await self._call_dify_api(api_key, base_url, content, message_id)
            else:
                # 默认使用OpenAI兼容API
                response_text = await self._call_openai_api(api_key, base_url, model, prompt, content, message_id)
            
            self.log_process("INFO", f"API调用成功，回复长度: {len(response_text)} 字符", message_id)
            return response_text
            
        except Exception as e:
            self.log_process("ERROR", f"API调用失败: {str(e)}", message_id)
            return "API调用出错，请稍后再试。"
    
    async def _call_openai_api(self, api_key: str, base_url: str, model: str, prompt: str, content: str, message_id: str) -> str:
        """调用OpenAI兼容的API"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 创建异步任务来处理OpenAI API调用
            loop = asyncio.get_event_loop()
            
            def sync_api_call():
                return client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": content},
                    ],
                    stream=False
                )
            
            response = await loop.run_in_executor(None, sync_api_call)
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI API调用失败: {str(e)}")
    
    async def _call_ragflow_api(self, api_key: str, base_url: str, content: str, message_id: str) -> str:
        """调用RAGFlow API"""
        try:
            from API import RAGflowAPIConnector
            
            # 创建RAGFlow连接器
            connector = RAGflowAPIConnector(
                api_key=api_key,
                base_url=base_url,
                name=f"async_handler_{message_id}"
            )
            
            # 构建消息
            messages = [{"role": "user", "content": content}]
            
            # 创建异步任务
            loop = asyncio.get_event_loop()
            
            def sync_ragflow_call():
                response, _ = connector.chat(messages, stream=False)
                return response
            
            response_text = await loop.run_in_executor(None, sync_ragflow_call)
            return response_text
            
        except Exception as e:
            raise Exception(f"RAGFlow API调用失败: {str(e)}")
    
    async def _call_coze_api(self, api_key: str, base_url: str, content: str, message_id: str) -> str:
        """调用Coze API"""
        try:
            from API import CozeAPIConnector
            
            connector = CozeAPIConnector(
                api_key=api_key,
                base_url=base_url,
                name=f"async_handler_{message_id}"
            )
            
            messages = [{"role": "user", "content": content}]
            
            loop = asyncio.get_event_loop()
            
            def sync_coze_call():
                response, _ = connector.chat(messages, stream=False)
                return response
            
            response_text = await loop.run_in_executor(None, sync_coze_call)
            return response_text
            
        except Exception as e:
            raise Exception(f"Coze API调用失败: {str(e)}")
    
    async def _call_dify_api(self, api_key: str, base_url: str, content: str, message_id: str) -> str:
        """调用Dify API"""
        try:
            from API import DifyAPIConnector
            
            connector = DifyAPIConnector(
                api_key=api_key,
                base_url=base_url,
                name=f"async_handler_{message_id}"
            )
            
            messages = [{"role": "user", "content": content}]
            
            loop = asyncio.get_event_loop()
            
            def sync_dify_call():
                response, _ = connector.chat(messages, stream=False)
                return response
            
            response_text = await loop.run_in_executor(None, sync_dify_call)
            return response_text
            
        except Exception as e:
            raise Exception(f"Dify API调用失败: {str(e)}")
    
    def split_long_text(self, text: str, chunk_size: int = 2000) -> List[str]:
        """
        分割长文本
        
        Args:
            text: 要分割的文本
            chunk_size: 每段的大小
            
        Returns:
            分割后的文本列表
        """
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    async def wx_message_sender(self):
        """专用的微信消息发送处理器 - 串行化所有微信RPA操作"""
        self.log_process("INFO", "微信消息发送器启动")
        
        while self.is_running:
            try:
                # 从发送队列获取消息
                try:
                    send_data = await asyncio.wait_for(self.wx_send_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # 使用锁确保微信操作的原子性
                async with self.wx_send_lock:
                    try:
                        chat = send_data['chat']
                        message = send_data['message']
                        at_user = send_data['at_user']
                        message_id = send_data['message_id']
                        segment_info = send_data['segment_info']
                        
                        if hasattr(chat, 'SendMsg'):
                            # 执行微信发送操作
                            if at_user:
                                chat.SendMsg(msg=message, at=at_user)
                            else:
                                chat.SendMsg(message)
                            
                            # 记录发送日志
                            if segment_info:
                                self.log_process("INFO", f"发送第 {segment_info} 段消息完成", message_id)
                            else:
                                self.log_process("INFO", f"消息发送完成，长度: {len(message)} 字符", message_id)
                            
                            # 微信操作间隔，避免过快操作导致问题
                            await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        self.log_process("ERROR", f"微信发送失败: {str(e)}", send_data.get('message_id', 'unknown'))
                        # 发送失败时稍微等待更长时间
                        await asyncio.sleep(1.0)
                
            except Exception as e:
                self.log_process("ERROR", f"微信发送器错误: {str(e)}")
                await asyncio.sleep(1.0)
        
        self.log_process("INFO", "微信消息发送器已停止")
    
    async def message_processor(self):
        """消息处理主循环"""
        self.log_process("INFO", "异步消息处理器启动")
        
        while self.is_running:
            try:
                # 控制并发数量
                if len(self.processing_messages) >= self.max_concurrent:
                    await asyncio.sleep(0.1)
                    continue
                
                # 从队列获取消息（优先级队列）
                try:
                    priority, message_id, message_data = await asyncio.wait_for(
                        self.message_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # 创建处理任务
                task = asyncio.create_task(self.process_single_message(message_data))
                self.processing_messages[message_id] = task
                
                # 不等待任务完成，继续处理下一个消息
                
            except Exception as e:
                self.log_process("ERROR", f"消息处理器错误: {str(e)}")
                await asyncio.sleep(1)
        
        self.log_process("INFO", "异步消息处理器已停止")
    
    def start(self):
        """启动异步消息处理器"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 创建新的事件循环
        def run_async_handler():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # 创建两个任务
            async def run_both():
                # 启动微信发送器任务
                self.wx_sender_task = asyncio.create_task(self.wx_message_sender())
                # 运行消息处理器
                await self.message_processor()
            
            self.loop.run_until_complete(run_both())
        
        # 在新线程中运行事件循环
        handler_thread = threading.Thread(target=run_async_handler, daemon=True)
        handler_thread.start()
        
        self.log_process("INFO", "异步消息处理器和微信发送器已启动")
    
    def stop(self):
        """停止异步消息处理器"""
        self.is_running = False
        
        # 取消所有正在处理的任务
        for task in self.processing_messages.values():
            task.cancel()
        
        self.processing_messages.clear()
        
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        self.log_process("INFO", "异步消息处理器已停止")
    
    def get_status(self) -> Dict:
        """获取处理器状态"""
        return {
            'is_running': self.is_running,
            'queue_size': self.message_queue.qsize() if self.message_queue else 0,
            'processing_count': len(self.processing_messages),
            'max_concurrent': self.max_concurrent,
            'log_lines': len(self.process_logs),
            'max_log_lines': self.max_log_lines
        }

# 全局实例
async_handler = AsyncMessageHandler()

def sync_add_message(chat, message, api_config=None):
    """
    同步接口：添加消息到异步处理队列
    用于从同步代码中调用异步处理
    """
    try:
        print(f"[DEBUG] sync_add_message 被调用: {chat.who} - {message.content[:50]}")
            
        if not async_handler.is_running:
            print("[DEBUG] 异步处理器未运行，正在启动...")
            async_handler.start()
            # 等待一下让处理器启动
            time.sleep(0.5)
            
        # 生成唯一的消息ID，避免重复处理
        import time
        message_id = f"{chat.who}_{int(time.time()*1000)}"
            
        print(f"[DEBUG] 消息ID: {message_id}")
        print(f"[DEBUG] 异步处理器状态: running={async_handler.is_running}, loop={async_handler.loop is not None}")
            
        # 检查是否已经在处理队列中
        if hasattr(async_handler, '_processing_ids'):
            if message_id in async_handler._processing_ids:
                print(f"消息 {message_id} 已在处理队列中，跳过重复添加")
                return
        else:
            async_handler._processing_ids = set()
            
        # 标记正在处理
        async_handler._processing_ids.add(message_id)
            
        # 在新线程中运行异步操作
        def run_async():
            try:
                if async_handler.loop and async_handler.loop.is_running():
                    print(f"[DEBUG] 向事件循环添加任务: {message_id}")
                    # 向运行中的事件循环添加任务
                    future = asyncio.run_coroutine_threadsafe(
                        async_handler.add_message(chat, message, api_config),
                        async_handler.loop
                    )
                    # 等待任务完成并移除ID标记
                    def cleanup_callback(fut):
                        try:
                            async_handler._processing_ids.discard(message_id)
                            if fut.exception():
                                print(f"[ERROR] 异步任务异常: {fut.exception()}")
                        except Exception as e:
                            print(f"[ERROR] cleanup_callback 异常: {e}")
                    future.add_done_callback(cleanup_callback)
                else:
                    print(f"[DEBUG] 事件循环不可用，创建新的事件循环处理: {message_id}")
                    # 创建新的事件循环
                    asyncio.run(async_handler.add_message(chat, message, api_config))
                    async_handler._processing_ids.discard(message_id)
            except Exception as e:
                print(f"[ERROR] 添加消息到队列失败: {e}")
                import traceback
                traceback.print_exc()
                async_handler._processing_ids.discard(message_id)
            
        # 在新线程中运行以避免阻塞
        threading.Thread(target=run_async, daemon=True).start()
        print(f"[DEBUG] 已启动处理线程: {message_id}")
            
    except Exception as e:
        print(f"[ERROR] sync_add_message 异常: {e}")
        import traceback
        traceback.print_exc()