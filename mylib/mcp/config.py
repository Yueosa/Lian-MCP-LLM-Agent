import os
from typing import Optional

from ..config import ConfigLoader
from .base import MCPServerState, LLMClientState, ToolConfig


class Config:
    """统一配置入口：使用项目的 ConfigLoader 发现配置并构造成模型实例，供其他模块导入使用"""
    _loader = ConfigLoader()

    # MCP 服务器运行时配置
    MCP: MCPServerState = MCPServerState(
        host=_loader.MCP.MCP_SERVER_HOST,
        port=int(_loader.MCP.MCP_SERVER_PORT) if hasattr(_loader.MCP, 'MCP_SERVER_PORT') else 8000,
        running=False
    )

    # LLM 客户端运行时配置
    LLM: LLMClientState = LLMClientState(
        provider=getattr(_loader.LLM, 'PROVIDER', 'openai') if hasattr(_loader, 'LLM') else 'openai',
        api_key=getattr(_loader.LLM, 'OPENAI_API_KEY', None) if hasattr(_loader, 'LLM') else None,
        base_url=getattr(_loader.LLM, 'OPENAI_API_URL', None) if hasattr(_loader, 'LLM') else None,
        initialized=False
    )

    # 工具相关配置：因为底层 ConfigLoader 可能会使用不同的键名（如 max/timeout）
    # 我们手动从 loader 中提取常见键并填充到 ToolConfig 中，保证兼容性。
    _tool_section = getattr(_loader, 'Tool', None)
    if _tool_section is not None:
        # 优先常见大写字段
        max_size = None
        timeout = None
        for key in ('MAX_FILE_SIZE', 'max', 'MAX', 'max_file_size'):
            if hasattr(_tool_section, key):
                max_size = getattr(_tool_section, key)
                break
        for key in ('REQUEST_TIMEOUT', 'timeout', 'REQUEST', 'request_timeout'):
            if hasattr(_tool_section, key):
                timeout = getattr(_tool_section, key)
                break

        # 也尝试以 dict 访问（有些 wrapper 可能暴露 dict-like 接口）
        try:
            if max_size is None and isinstance(_tool_section, dict):
                max_size = _tool_section.get('MAX_FILE_SIZE') or _tool_section.get('max') or _tool_section.get('max_file_size')
            if timeout is None and isinstance(_tool_section, dict):
                timeout = _tool_section.get('REQUEST_TIMEOUT') or _tool_section.get('timeout') or _tool_section.get('request_timeout')
        except Exception:
            pass

        try:
            Tool: ToolConfig = ToolConfig(
                MAX_FILE_SIZE=int(max_size) if max_size is not None else ToolConfig().MAX_FILE_SIZE,
                REQUEST_TIMEOUT=int(timeout) if timeout is not None else ToolConfig().REQUEST_TIMEOUT,
            )
        except Exception:
            Tool: ToolConfig = ToolConfig()
    else:
        Tool: ToolConfig = ToolConfig()


if __name__ == "__main__":
    cfg = Config()
    print("MCP host:", cfg.MCP.host, "port:", cfg.MCP.port)
    print("LLM provider:", cfg.LLM.provider)
