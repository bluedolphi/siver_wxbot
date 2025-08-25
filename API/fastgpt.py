import json
import time
import re
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
        self.app_id = self._extract_app_id(base_url)

    def _extract_app_id(self, base_url: str) -> str:
        match = re.search(r'app[_-]([a-zA-Z0-9]+)', base_url)
        if match:
            return match.group(1)
        return ""

    def search(self, query: str, **kwargs) -> Tuple[str, float]:
        start_time = time.time()
        try:
            if "/v1/chat/completions" not in self.base_url:
                api_url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
            else:
                api_url = self.base_url
            data = {
                "model": kwargs.get("model", "fastgpt"),
                "messages": [{"role": "user", "content": query}],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000),
                "stream": False
            }
            chat_id = kwargs.get("chatId") or kwargs.get("chat_id")
            if chat_id:
                data["chatId"] = chat_id
            variables = kwargs.get("variables", {})
            if variables:
                data["variables"] = variables
            for key, value in kwargs.items():
                if key not in ["model", "temperature", "max_tokens", "chatId", "chat_id", "variables"]:
                    data[key] = value
            response = requests.post(api_url, headers=self.headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
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
                    response_text = f"FastGPT API调用失败: {error_message}"
                except Exception:
                    response_text = f"FastGPT API调用失败: HTTP {response.status_code}"
        except Exception as e:
            response_text = f"FastGPT API调用出错: {str(e)}"
        request_time = time.time() - start_time
        self.last_request_time = request_time
        self._save_to_history(query, response_text, request_time)
        return response_text, request_time

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Tuple[str, float]:
        start_time = time.time()
        try:
            if "/v1/chat/completions" not in self.base_url:
                api_url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
            else:
                api_url = self.base_url
            data = {
                "model": kwargs.get("model", "fastgpt"),
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000),
                "stream": False
            }
            chat_id = kwargs.get("chatId") or kwargs.get("chat_id")
            if chat_id:
                data["chatId"] = chat_id
            variables = kwargs.get("variables", {})
            if variables:
                data["variables"] = variables
            detail = kwargs.get("detail", False)
            if detail:
                data["detail"] = detail
            response = requests.post(api_url, headers=self.headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
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
                    response_text = f"FastGPT API调用失败: {error_message}"
                except Exception:
                    response_text = f"FastGPT API调用失败: HTTP {response.status_code}"
        except Exception as e:
            response_text = f"FastGPT API调用出错: {str(e)}"
        request_time = time.time() - start_time
        self.last_request_time = request_time
        return response_text, request_time
