import json
import time
from typing import Dict, List, Tuple
import requests
from .base import BaseAPIConnector

class OpenAIConnector(BaseAPIConnector):
    """OpenAI API连接器"""

    def __init__(self, api_key: str, base_url: str, name: str = "OpenAI", organization_id: str = "", timeout: int = 30, retry_count: int = 3):
        super().__init__(api_key, base_url, name, timeout, retry_count)
        self.organization_id = organization_id
        if organization_id:
            self.headers["OpenAI-Organization"] = organization_id
    
    def search(self, query: str, **kwargs) -> Tuple[str, float]:
        start_time = time.time()
        try:
            model = kwargs.get("model", "gpt-3.5-turbo")
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": kwargs.get("system_prompt", "你是一个企业助手，提供简洁明了的回答。")},
                    {"role": "user", "content": query}
                ],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 500)
            }
            optional_params = [
                "top_p", "frequency_penalty", "presence_penalty", "stop",
                "logit_bias", "user", "seed", "tools", "tool_choice",
                "response_format", "stream"
            ]
            for param in optional_params:
                if param in kwargs:
                    data[param] = kwargs[param]
            response = self._make_request_with_retry(self.base_url, self.headers, data)
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and result["choices"]:
                    response_text = result["choices"][0]["message"]["content"]
                else:
                    response_text = json.dumps(result, ensure_ascii=False)
            else:
                response_text = f"OpenAI API调用失败: HTTP {response.status_code}"
        except Exception as e:
            response_text = f"OpenAI API调用出错: {str(e)}"
        request_time = time.time() - start_time
        self.last_request_time = request_time
        self._save_to_history(query, response_text, request_time)
        return response_text, request_time
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Tuple[str, float]:
        start_time = time.time()
        try:
            model = kwargs.get("model", "gpt-3.5-turbo")
            data = {
                "model": model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 500)
            }
            optional_params = [
                "top_p", "frequency_penalty", "presence_penalty", "stop",
                "logit_bias", "user", "seed", "tools", "tool_choice",
                "response_format", "stream"
            ]
            for param in optional_params:
                if param in kwargs:
                    data[param] = kwargs[param]
            response = requests.post(self.base_url, headers=self.headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and result["choices"]:
                    response_text = result["choices"][0]["message"]["content"]
                else:
                    response_text = json.dumps(result, ensure_ascii=False)
            else:
                response_text = f"OpenAI API调用失败: HTTP {response.status_code}"
        except Exception as e:
            response_text = f"OpenAI API调用出错: {str(e)}"
        request_time = time.time() - start_time
        self.last_request_time = request_time
        return response_text, request_time
