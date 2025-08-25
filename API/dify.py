import json
import time
from typing import Dict, List, Tuple
import requests
from .base import BaseAPIConnector

class DifyAPIConnector(BaseAPIConnector):
    """Dify API连接器"""

    def __init__(self, api_key: str, base_url: str, name: str = "Dify", timeout: int = 30, retry_count: int = 3):
        super().__init__(api_key, base_url, name, timeout, retry_count)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def search(self, query: str, **kwargs) -> Tuple[str, float]:
        start_time = time.time()
        try:
            endpoint = self.base_url.rstrip('/')
            data = {
                "inputs": kwargs.get("inputs", {}),
                "query": query,
                "response_mode": "blocking",
                "user": kwargs.get("user", "user_" + str(int(time.time())))
            }
            response = requests.post(endpoint, headers=self.headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if "answer" in result:
                    response_text = result["answer"]
                elif "message" in result and isinstance(result["message"], dict) and "content" in result["message"]:
                    response_text = result["message"]["content"]
                else:
                    response_text = json.dumps(result, ensure_ascii=False)
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    response_text = f"Dify API调用失败: {error_message}"
                except Exception:
                    response_text = f"Dify API调用失败: HTTP {response.status_code}"
        except Exception as e:
            response_text = f"Dify API调用出错: {str(e)}"
        request_time = time.time() - start_time
        self.last_request_time = request_time
        self._save_to_history(query, response_text, request_time)
        return response_text, request_time
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Tuple[str, float]:
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if user_messages:
            query = user_messages[-1].get("content", "")
            context = [{"role": msg["role"], "content": msg["content"]}
                      for msg in messages if msg.get("role") in ["user", "assistant"]]
            kwargs["conversation_context"] = context
            return self.search(query, **kwargs)
        return "没有用户消息", 0
