"""
兼容性转发模块：
保留对旧路径 `api_connectors` 的导入支持，实际实现已拆分到 `API/` 包。
建议新代码使用：

    from API import (
        BaseAPIConnector, DefaultAPIConnector, OpenAIConnector, CozeAPIConnector,
        DifyAPIConnector, FastGPTAPIConnector, N8NAPIConnector, APIConnectorFactory
    )
"""

from API import (
    BaseAPIConnector,
    DefaultAPIConnector,
    OpenAIConnector,
    CozeAPIConnector,
    DifyAPIConnector,
    FastGPTAPIConnector,
    N8NAPIConnector,
    RAGFlowAPIConnector,
    APIConnectorFactory,
)

__all__ = [
    "BaseAPIConnector",
    "DefaultAPIConnector",
    "OpenAIConnector",
    "CozeAPIConnector",
    "DifyAPIConnector",
    "FastGPTAPIConnector",
    "N8NAPIConnector",
    "RAGFlowAPIConnector",
    "APIConnectorFactory",
]