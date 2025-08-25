import json
import time
import re
from typing import Dict, List, Tuple
import requests
from .base import BaseAPIConnector

class CozeAPIConnector(BaseAPIConnector):
    """Coze API连接器"""

    def __init__(self, api_key: str, base_url: str, name: str = "Coze", timeout: int = 30, retry_count: int = 3):
        super().__init__(api_key, base_url, name, timeout, retry_count)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.bot_id = self._extract_bot_id(base_url)
    
    def _extract_bot_id(self, base_url: str) -> str:
        match = re.search(r'bot/(\d+)', base_url)
        if match:
            return match.group(1)
        return ""
    
    def search(self, query: str, **kwargs) -> Tuple[str, float]:
        start_time = time.time()
        try:
            api_url = "https://api.coze.cn/open_api/v2/chat"
            conversation_id = kwargs.get("conversation_id", f"conv_{int(time.time())}")
            user_id = kwargs.get("user", f"user_{int(time.time())}")
            bot_id = kwargs.get("bot_id", self.bot_id)
            data = {
                "conversation_id": conversation_id,
                "bot_id": bot_id,
                "user": user_id,
                "query": query,
                "stream": False
            }
            for key, value in kwargs.items():
                if key not in data and key not in ["conversation_id", "user", "bot_id"]:
                    data[key] = value
            response = requests.post(api_url, headers=self.headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if "messages" in result and result["messages"]:
                    for message in result["messages"]:
                        if message.get("type") == "answer" and message.get("role") == "assistant":
                            response_text = message.get("content", "")
                            break
                    else:
                        response_text = result["messages"][-1].get("content", "")
                else:
                    response_text = json.dumps(result, ensure_ascii=False)
            else:
                response_text = f"Coze API调用失败: HTTP {response.status_code}, {response.text}"
        except Exception as e:
            response_text = f"Coze API调用出错: {str(e)}"
        request_time = time.time() - start_time
        self.last_request_time = request_time
        self._save_to_history(query, response_text, request_time)
        return response_text, request_time
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Tuple[str, float]:
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if user_messages:
            query = user_messages[-1].get("content", "")
            return self.search(query, **kwargs)
        return "没有用户消息", 0
