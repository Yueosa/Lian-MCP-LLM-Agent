"""mylib.mcp package public API

暴露简易的启动函数：start_mcp_server(), run_llm_client()
"""
from .mcp_server import app, mcp_tools
from .llm_client import MCPClient, ModelProvider
from .config import Config

import uvicorn


def start_mcp_server(host: str = None, port: int = None, reload: bool = False):
	host = host or Config.MCP.host
	port = port or Config.MCP.port
	Config.MCP.running = True
	uvicorn.run("mylib.mcp.mcp_server:app", host=host, port=port, reload=reload)


def run_llm_client(provider: str = None, mcp_server_url: str = None):
	"""启动交互式 LLM 客户端（阻塞）。

	provider 可以是 ModelProvider 枚举或字符串（如 'openai'）；如果未提供则使用 config 中的值或默认。
	"""
	# 解析 provider
	prov = None
	if provider:
		try:
			prov = ModelProvider(provider) if isinstance(provider, str) else provider
		except Exception:
			prov = ModelProvider.DEEPSEEK
	else:
		if Config.LLM.provider:
			try:
				prov = ModelProvider(Config.LLM.provider)
			except Exception:
				prov = ModelProvider.DEEPSEEK
		else:
			prov = ModelProvider.DEEPSEEK

	# 实际运行交互式客户端入口（llm_client.main 创建自己的 MCPClient），传入 mcp_server_url 环境变量以便使用
	from . import llm_client
	# 如果用户传入了 mcp_server_url，我们不 attempt to inject it into llm_client.main (which creates its own client),
	# but we can set an environment variable as a simple means for the interactive runner to pick it up if implemented.
	if mcp_server_url:
		import os
		os.environ.setdefault('MCP_SERVER_URL', mcp_server_url)

	llm_client.main()


__all__ = ["app", "mcp_tools", "MCPClient", "start_mcp_server", "run_llm_client", "Config"]
