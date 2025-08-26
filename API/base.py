import json
import requests
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
import time

class BaseAPIConnector(ABC):
    """API连接器基类"""
    
    def __init__(self, api_key: str, base_url: str, name: str = "", timeout: int = 30, retry_count: int = 3):
        self.api_key = api_key
        self.base_url = base_url
        self.name = name or "Unknown API"
        self.timeout = timeout
        self.retry_count = retry_count
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.last_request_time = 0  # 添加请求时长记录变量

    def _make_request_with_retry(self, url: str, headers: dict, data: dict) -> requests.Response:
        """带重试机制的请求方法"""
        last_exception = None

        for attempt in range(self.retry_count):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
                return response
            except Exception as e:
                last_exception = e
                if attempt < self.retry_count - 1:
                    print(f"请求失败，第 {attempt + 1} 次重试: {e}")
                    time.sleep(1)  # 等待1秒后重试
                else:
                    print(f"请求失败，已达到最大重试次数: {e}")

        # 如果所有重试都失败，抛出最后一个异常
        raise last_exception


    @abstractmethod
    def search(self, query: str, **kwargs) -> Tuple[str, float]:
        """搜索API，返回结果和请求时长"""
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Tuple[str, float]:
        """聊天API，返回结果和请求时长"""
        pass
