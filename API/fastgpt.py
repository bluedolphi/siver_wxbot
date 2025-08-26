import json
import time
from typing import Dict, List, Tuple
import requests
from .base import BaseAPIConnector

class FastGPTAPIConnector(BaseAPIConnector):
    """FastGPT API连接器"""

    def __init__(self, api_key: str, base_url: str, name: str = "FastGPT", timeout: int = 30, retry_count: int = 3):
        super().__init__(api_key, base_url, name, timeout, retry_count)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def search(self, query: str, **kwargs) -> Tuple[str, float]:
        start_time = time.time()
        try:
            endpoint = self.base_url.rstrip('/')
            if not endpoint.endswith('/chat/completions'):
                endpoint += '/chat/completions'
            
            data = {
                "chatId": kwargs.get("chat_id", f"chat_{int(time.time())}"),
                "stream": False,
                "detail": False,
                "messages": [
                    {
                        "content": query,
                        "role": "user"
                    }
                ]
            }
            
            if "variables" in kwargs:
                data["variables"] = kwargs["variables"]
                
            response = requests.post(endpoint, headers=self.headers, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        response_text = choice["message"]["content"]
                    else:
                        response_text = json.dumps(choice, ensure_ascii=False)
                elif "data" in result:
                    response_text = str(result["data"])
                elif "text" in result:
                    response_text = result["text"]
                else:
                    response_text = json.dumps(result, ensure_ascii=False)
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    response_text = f"FastGPT API调用失败: {error_message}"
                except Exception:
                    response_text = f"FastGPT API调用失败: HTTP {response.status_code}"
                    
        except Exception as e:
            response_text = f"FastGPT API调用出错: {str(e)}"
        
        request_time = time.time() - start_time
        self.last_request_time = request_time
        
        return response_text, request_time

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Tuple[str, float]:
        if not messages:
            return "没有消息", 0
            
        start_time = time.time()
        try:
            endpoint = self.base_url.rstrip('/')
            if not endpoint.endswith('/chat/completions'):
                endpoint += '/chat/completions'
            
            data = {
                "chatId": kwargs.get("chat_id", f"chat_{int(time.time())}"),
                "stream": False,
                "detail": False,
                "messages": messages
            }
            
            if "variables" in kwargs:
                data["variables"] = kwargs["variables"]
                
            response = requests.post(endpoint, headers=self.headers, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
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
                    response_text = f"FastGPT API调用失败: {error_message}"
                except Exception:
                    response_text = f"FastGPT API调用失败: HTTP {response.status_code}"
                    
        except Exception as e:
            response_text = f"FastGPT API调用出错: {str(e)}"
        
        request_time = time.time() - start_time
        self.last_request_time = request_time
        
        user_question = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_question = msg.get("content", "")
                break
        

        return response_text, request_time