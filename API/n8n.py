import json
import time
from typing import Dict, List, Tuple
import requests
from .base import BaseAPIConnector

class N8NAPIConnector(BaseAPIConnector):
    """N8N API连接器"""

    def __init__(self, api_key: str, base_url: str, name: str = "N8N", timeout: int = 30, retry_count: int = 3):
        super().__init__(api_key, base_url, name, timeout, retry_count)
        if self._is_webhook_url(base_url):
            self.headers = {"Content-Type": "application/json"}
            self.auth_mode = "webhook"
        else:
            self.headers = {"Content-Type": "application/json", "X-N8N-API-KEY": api_key}
            self.auth_mode = "api"

    def _is_webhook_url(self, url: str) -> bool:
        return "webhook" in url.lower() or "hook" in url.lower()

    def search(self, query: str, **kwargs) -> Tuple[str, float]:
        start_time = time.time()
        try:
            data = {
                "query": query,
                "timestamp": int(time.time()),
                "user_id": kwargs.get("user_id", "default_user")
            }
            workflow_id = kwargs.get("workflow_id")
            if workflow_id:
                data["workflow_id"] = workflow_id
            for key, value in kwargs.items():
                if key not in ["workflow_id", "user_id"]:
                    data[key] = value
            if self.auth_mode == "webhook":
                request_url = self.base_url
            else:
                request_url = f"{self.base_url.rstrip('/')}/api/v1/workflows/run"
                if workflow_id:
                    request_url = f"{self.base_url.rstrip('/')}/api/v1/workflows/{workflow_id}/execute"
            response = requests.post(request_url, headers=self.headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, dict):
                    if "data" in result:
                        if isinstance(result["data"], str):
                            response_text = result["data"]
                        elif isinstance(result["data"], dict) and "output" in result["data"]:
                            response_text = result["data"]["output"]
                        else:
                            response_text = json.dumps(result["data"], ensure_ascii=False)
                    elif "output" in result:
                        response_text = result["output"]
                    elif "result" in result:
                        response_text = result["result"]
                    elif "message" in result:
                        response_text = result["message"]
                    else:
                        response_text = json.dumps(result, ensure_ascii=False)
                else:
                    response_text = str(result)
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    response_text = f"N8N API调用失败: {error_message}"
                except Exception:
                    response_text = f"N8N API调用失败: HTTP {response.status_code}"
        except Exception as e:
            response_text = f"N8N API调用出错: {str(e)}"
        request_time = time.time() - start_time
        self.last_request_time = request_time
       
        return response_text, request_time

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Tuple[str, float]:
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if user_messages:
            query = user_messages[-1].get("content", "")
            kwargs["message_count"] = len(messages)
            return self.search(query, **kwargs)
        return "没有用户消息", 0
