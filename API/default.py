import json
import time
from typing import Dict, List, Tuple
import requests
from .base import BaseAPIConnector

class DefaultAPIConnector(BaseAPIConnector):
    """默认API连接器"""

    def __init__(self, api_key: str, base_url: str, name: str = "默认API", timeout: int = 30, retry_count: int = 3):
        super().__init__(api_key, base_url, name, timeout, retry_count)
    
    def search(self, query: str, **kwargs) -> Tuple[str, float]:
        """搜索API"""
        start_time = time.time()  # 记录开始时间
        try:
            data = {
                "prompt": query,
                "max_tokens": kwargs.get("max_tokens", 500)
            }

            response = self._make_request_with_retry(self.base_url, self.headers, data)

            if response.status_code == 200:
                result = response.json()
                response_text = result.get("text", json.dumps(result, ensure_ascii=False))
            else:
                response_text = f"API调用失败: HTTP {response.status_code}"
        except Exception as e:
            response_text = f"API调用出错: {str(e)}"

        # 计算请求时长并记录
        request_time = time.time() - start_time
        self.last_request_time = request_time

        # 保存到历史记录
        self._save_to_history(query, response_text, request_time)

        return response_text, request_time
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Tuple[str, float]:
        """聊天API"""
        query = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        return self.search(query, **kwargs)
