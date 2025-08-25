import json
import time
import re
from typing import Dict, List, Tuple
import requests
from .base import BaseAPIConnector

class RAGFlowAPIConnector(BaseAPIConnector):
    """RAGFlow API连接器 - 支持OpenAI兼容的聊天接口"""

    def __init__(self, api_key: str, base_url: str, name: str = "RAGFlow", timeout: int = 30, retry_count: int = 3):
        super().__init__(api_key, base_url, name, timeout, retry_count)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        # 从base_url中提取chat_id（如果有）
        self.chat_id = self._extract_chat_id(base_url)
    
    def _extract_chat_id(self, base_url: str) -> str:
        """从URL中提取chat_id"""
        # 尝试从URL中提取chat_id: /api/v1/chats_openai/{chat_id}/chat/completions
        match = re.search(r'/chats_openai/([^/]+)/chat/completions', base_url)
        if match:
            return match.group(1)
        return ""
    
    def _build_api_url(self, chat_id: str = None) -> str:
        """构建完整的API URL"""
        chat_id = chat_id or self.chat_id
        if chat_id and "/chat/completions" not in self.base_url:
            # 如果base_url不包含完整路径，则构建完整URL
            base = self.base_url.rstrip('/')
            return f"{base}/api/v1/chats_openai/{chat_id}/chat/completions"
        return self.base_url
    
    def search(self, query: str, **kwargs) -> Tuple[str, float]:
        """搜索API - 转换为聊天格式"""
        messages = [{"role": "user", "content": query}]
        return self.chat(messages, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Tuple[str, float]:
        """聊天API - 使用RAGFlow的OpenAI兼容接口"""
        start_time = time.time()
        try:
            # 确定chat_id
            chat_id = kwargs.get("chat_id", self.chat_id)
            api_url = self._build_api_url(chat_id)
            
            # 构建请求数据（OpenAI兼容格式）
            data = {
                "model": kwargs.get("model", "model"),
                "messages": messages,
                "stream": kwargs.get("stream", False),
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000)
            }
            
            # 添加其他OpenAI兼容参数
            optional_params = [
                "top_p", "frequency_penalty", "presence_penalty", "stop",
                "logit_bias", "user", "seed", "tools", "tool_choice",
                "response_format"
            ]
            
            for param in optional_params:
                if param in kwargs:
                    data[param] = kwargs[param]
            
            print(f"RAGFlow请求URL: {api_url}")
            print(f"RAGFlow请求数据: {json.dumps(data, ensure_ascii=False)}")
            
            response = requests.post(
                api_url,
                headers=self.headers,
                json=data,
                timeout=self.timeout,
                stream=data.get("stream", False)
            )
            
            print(f"RAGFlow响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                if data.get("stream", False):
                    # 处理流式响应
                    response_text = self._handle_stream_response(response)
                else:
                    # 处理非流式响应
                    result = response.json()
                    print(f"RAGFlow响应内容: {json.dumps(result, ensure_ascii=False)[:200]}...")
                    
                    if "choices" in result and result["choices"]:
                        choice = result["choices"][0]
                        if "message" in choice and "content" in choice["message"]:
                            response_text = choice["message"]["content"]
                        else:
                            response_text = json.dumps(choice, ensure_ascii=False)
                    else:
                        response_text = json.dumps(result, ensure_ascii=False)
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    error_code = error_data.get("code", "")
                    response_text = f"RAGFlow API调用失败: {error_message} (code: {error_code})"
                except Exception:
                    response_text = f"RAGFlow API调用失败: HTTP {response.status_code}"
                print(f"RAGFlow API错误: {response_text}")
        except Exception as e:
            response_text = f"RAGFlow API调用出错: {str(e)}"
            print(f"RAGFlow API异常: {str(e)}")
        
        # 计算请求时长并记录
        request_time = time.time() - start_time
        self.last_request_time = request_time
        
        # 保存到历史记录
        query = messages[-1].get("content", "") if messages else ""
        self._save_to_history(query, response_text, request_time)
        
        return response_text, request_time
    
    def _handle_stream_response(self, response) -> str:
        """处理流式响应，合并所有chunk的内容"""
        full_content = ""
        try:
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    data_str = line[6:]  # 移除 "data: " 前缀
                    if data_str.strip() == "[DONE]":
                        break
                    
                    try:
                        chunk_data = json.loads(data_str)
                        if "choices" in chunk_data and chunk_data["choices"]:
                            delta = chunk_data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_content += content
                                print(f"RAGFlow流式内容: {content}")
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"处理RAGFlow流式响应时出错: {e}")
            return f"流式响应处理出错: {str(e)}"
        
        return full_content or "未收到有效响应内容"
