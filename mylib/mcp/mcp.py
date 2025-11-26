"""MCP Server - FastAPI 服务器实现"""

from pathlib import Path
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from mylib.config import ConfigLoader

from .base import ToolResponse
from .tools import get_tool_loader


class MCPServer:
    """MCP 服务器主类"""

    def __init__(self, config_path: str = None):
        """
        初始化 MCP 服务器

        Args:
            config_path: 配置文件路径，默认使用 mylib/mcp/config/mcp_config.toml
        """
        # 加载配置
        if config_path is None:
            config_path = str(Path(__file__).parent / "config" / "mcp_config.toml")
        self._config_loader = ConfigLoader(config_path=config_path)
        self._load_config()

        # 初始化工具加载器
        self._tool_loader = get_tool_loader()

        # 创建 FastAPI 应用
        self.app = FastAPI(
            title="MCP Server",
            version="1.0.0",
            description="Model Context Protocol Server - 提供统一的工具调用接口",
        )

        # 配置 CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )

        # 注册路由
        self._register_routes()

    def _load_config(self):
        """从配置文件加载服务器配置"""
        fastapi_cfg = getattr(self._config_loader, "fastapi", None)
        if fastapi_cfg is None:
            # 使用默认配置
            self.host = "0.0.0.0"
            self.port = 8080
            self.debug = False
        else:
            self.host = fastapi_cfg.get("host", "0.0.0.0")
            self.port = int(fastapi_cfg.get("port", 8080))
            self.debug = bool(fastapi_cfg.get("debug", False))

    def _register_routes(self):
        """注册所有 API 路由"""

        @self.app.get("/")
        async def root():
            """根路径 - 服务器状态检查"""
            return {
                "message": "MCP Server is running",
                "version": "1.0.0",
                "tools_count": len(self._tool_loader.tools_meta),
            }

        @self.app.get("/health")
        async def health():
            """健康检查端点"""
            return {"status": "healthy", "service": "mcp-server"}
        
        @self.app.get("/help")
        async def help():
            """帮助信息端点"""
            return {
                "message": "欢迎使用 MCP Server !",
                "endpoints": {
                    "/tools": "获取所有可用工具列表",
                    "/tools/{tool_name}": "获取指定工具的详细信息",
                    "/tools/{tool_name}/call": "调用单个工具",
                    "/tools/reload": "热重载工具元数据与绑定",
                },
            }

        @self.app.get("/tools")
        async def list_tools():
            """获取所有可用工具列表"""
            return {"tools": self._tool_loader.get_tools_list()}

        @self.app.get("/tools/{tool_name}")
        async def get_tool_info(tool_name: str):
            """获取指定工具的详细信息"""
            meta = self._tool_loader.get_tool_meta(tool_name)
            if meta is None:
                raise HTTPException(status_code=404, detail=f"工具不存在: {tool_name}")
            return {"tool": meta.to_dict()}

        @self.app.post("/tools/{tool_name}/call")
        async def call_single_tool(tool_name: str, arguments: Dict[str, Any]):
            """调用单个工具"""
            try:
                result = await self._tool_loader.call(tool_name, **arguments)
                return ToolResponse(result=result, success=True).dict()
            except ValueError as exc:
                return ToolResponse(result=None, success=False, error=str(exc)).dict()
            except Exception as exc:  # noqa: BLE001
                return ToolResponse(result=None, success=False, error=str(exc)).dict()

        @self.app.post("/tools/reload")
        async def reload_tools():
            """热重载工具元数据与绑定（不重启服务）"""
            try:
                self._tool_loader.reload()
                return {
                    "success": True,
                    "tools_count": len(self._tool_loader.tools_meta),
                    "tools": self._tool_loader.get_tools_list(),
                }
            except Exception as exc:  # noqa: BLE001
                return {"success": False, "error": str(exc)}

    def run(self, host: str = None, port: int = None, **kwargs):
        """
        运行服务器

        Args:
            host: 主机地址，默认使用配置文件中的值
            port: 端口号，默认使用配置文件中的值
            **kwargs: 传递给 uvicorn.run 的其他参数
        """
        run_host = host or self.host
        run_port = port or self.port

        uvicorn.run(
            self.app,
            host=run_host,
            port=run_port,
            log_level="debug" if self.debug else "info",
            **kwargs,
        )

    def get_tools_list(self) -> List[Dict[str, Any]]:
        """获取所有工具列表"""
        return self._tool_loader.get_tools_list()

    def get_tool_meta(self, tool_name: str):
        """获取指定工具的元数据"""
        return self._tool_loader.get_tool_meta(tool_name)

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """直接调用工具（不通过 HTTP）"""
        return await self._tool_loader.call(tool_name, **kwargs)




if __name__ == "__main__":
    server = MCPServer()
    server.run()
