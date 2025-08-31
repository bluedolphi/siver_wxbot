import json
import time
from typing import Dict, List, Tuple
import requests
from .base import BaseAPIConnector

class RAGflowAPIConnector(BaseAPIConnector):
    """RAGflow API连接器"""

    def __init__(self, api_key: str, base_url: str, name: str = "RAGflow", timeout: int = 30, retry_count: int = 3):
        super().__init__(api_key, base_url, name, timeout, retry_count)
        # RAGflow使用Authorization header
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def search(self, query: str, **kwargs) -> Tuple[str, float]:
        start_time = time.time()
        try:
            if not self.base_url:
                raise ValueError("RAGflow base_url is not configured.")
            endpoint = self.base_url.rstrip('/')
            data = {
                "model": kwargs.get("model", "model"),
                "messages": [{"role": "user", "content": query}],
                "stream": kwargs.get("stream", False)
            }
            
            # 添加其他可能的参数
            if "session_id" in kwargs:
                data["session_id"] = kwargs["session_id"]
            
            print(f"[DEBUG] 发送请求到: {endpoint}")
            print(f"[DEBUG] 请求数据: {data}")
            
            response = requests.post(endpoint, headers=self.headers, json=data, timeout=self.timeout)
            
            print(f"[DEBUG] 响应状态码: {response.status_code}")
            print(f"[DEBUG] 响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                # RAGflow返回OpenAI兼容格式
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        response_text = choice["message"]["content"]
                    else:
                        response_text = json.dumps(choice, ensure_ascii=False)
                elif "data" in result:
                    if isinstance(result["data"], dict):
                        response_text = result["data"].get("answer", json.dumps(result["data"], ensure_ascii=False))
                    else:
                        response_text = str(result["data"])
                elif "answer" in result:
                    response_text = result["answer"]
                elif "response" in result:
                    response_text = result["response"]
                else:
                    response_text = json.dumps(result, ensure_ascii=False)
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    response_text = f"RAGflow API调用失败: {error_message}"
                except Exception:
                    response_text = f"RAGflow API调用失败: HTTP {response.status_code}"
                    
        except Exception as e:
            print(f"[DEBUG] 异常: {e}")
            response_text = f"RAGflow API调用出错: {str(e)}"
        
        request_time = time.time() - start_time
        self.last_request_time = request_time
        
        return response_text, request_time

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Tuple[str, float]:
        """聊天API，将对话转换为搜索请求"""
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if user_messages:
            query = user_messages[-1].get("content", "")
            return self.search(query, **kwargs)
        return "没有用户消息", 0