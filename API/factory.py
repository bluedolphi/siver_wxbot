from .base import BaseAPIConnector
from .default import DefaultAPIConnector
from .openai_connector import OpenAIConnector
from .coze import CozeAPIConnector
from .dify import DifyAPIConnector
from .fastgpt import FastGPTAPIConnector
from .n8n import N8NAPIConnector
from .ragflow import RAGFlowAPIConnector

class APIConnectorFactory:
    """API连接器工厂类"""

    @staticmethod
    def create_connector(platform: str, api_key: str, base_url: str, name: str = "", timeout: int = 30, retry_count: int = 3) -> BaseAPIConnector:
        """创建API连接器"""
        if platform.lower() == "openai":
            return OpenAIConnector(api_key, base_url, name, timeout=timeout, retry_count=retry_count)
        elif platform.lower() == "coze":
            return CozeAPIConnector(api_key, base_url, name, timeout=timeout, retry_count=retry_count)
        elif platform.lower() == "dify":
            return DifyAPIConnector(api_key, base_url, name, timeout=timeout, retry_count=retry_count)
        elif platform.lower() == "n8n":
            return N8NAPIConnector(api_key, base_url, name, timeout=timeout, retry_count=retry_count)
        elif platform.lower() == "fastgpt":
            return FastGPTAPIConnector(api_key, base_url, name, timeout=timeout, retry_count=retry_count)
        elif platform.lower() == "ragflow":
            return RAGFlowAPIConnector(api_key, base_url, name, timeout=timeout, retry_count=retry_count)
        else:
            return DefaultAPIConnector(api_key, base_url, name, timeout=timeout, retry_count=retry_count)
