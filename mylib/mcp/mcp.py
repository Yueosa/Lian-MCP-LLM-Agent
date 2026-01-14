"""MCP Server - FastAPI 服务器实现"""

import uvicorn

from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime
from collections import deque
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

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
        if config_path is None:
            config_path = str(Path(__file__).parent / "config" / "mcp_config.toml")
        self._config_loader = ConfigLoader(config_path=config_path)
        self._load_config()

        self._tool_loader = get_tool_loader()
        
        # 日志缓存（最多保存最近500条）
        self._logs: deque = deque(maxlen=500)
        self._add_log("MCP Server 初始化完成")

        self.app = FastAPI(
            title="MCP Server",
            version="1.0.0",
            description="Model Context Protocol Server - 提供统一的工具调用接口",
        )

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )
        
        # 添加请求日志中间件
        @self.app.middleware("http")
        async def log_requests(request, call_next):
            response = await call_next(request)
            # 记录请求日志
            log_msg = f"{request.client.host}:{request.client.port} - \"{request.method} {request.url.path} HTTP/1.1\" {response.status_code}"
            self._add_log(log_msg)
            return response

        self._register_routes()

        # 挂载静态文件目录
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    def _load_config(self):
        """从配置文件加载服务器配置"""
        fastapi_cfg = getattr(self._config_loader, "fastapi", None)
        if fastapi_cfg is None:
            self.host = "0.0.0.0"
            self.port = 8080
            self.debug = False
        else:
            self.host = fastapi_cfg.get("host", "0.0.0.0")
            self.port = int(fastapi_cfg.get("port", 8080))
            self.debug = bool(fastapi_cfg.get("debug", False))

    def _add_log(self, message: str):
        """添加日志到缓存"""
        self._logs.append({
            "timestamp": datetime.now().isoformat(),
            "message": message
        })

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
                    "/": "获取服务状态",
                    "/help": "获取服务帮助",
                    "/healthy": "健康检查",
                    "/bysj": "毕业设计答辩展示页面",
                    "/tools": "获取所有可用工具列表",
                    "/tools/{tool_name}": "获取指定工具的详细信息",
                    "/tools/{tool_name}/call": "调用单个工具",
                    "/tools/reload": "热重载工具元数据与绑定",
                },
            }

        @self.app.get("/bysj", response_class=HTMLResponse)
        async def bysj_page():
            """毕业设计答辩展示页面 - MCP 模块可视化"""
            html_path = Path(__file__).parent / "static" / "bysj.html"
            if not html_path.exists():
                raise HTTPException(status_code=404, detail="答辩展示页面未找到")
            return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

        @self.app.get("/logs")
        async def get_logs():
            """获取服务器日志"""
            return {"logs": list(self._logs)}

        @self.app.get("/tools")
        async def list_tools():
            """获取所有可用工具列表"""
            return {"tools": self._tool_loader.get_tools_list()}

        @self.app.get("/tools/{tool_name}")
        async def get_tool_info(tool_name: str):
            """获取指定工具的详细信息"""
            self._add_log(f"查询工具信息: {tool_name}")
            meta = self._tool_loader.get_tool_meta(tool_name)
            if meta is None:
                raise HTTPException(status_code=404, detail=f"工具不存在: {tool_name}")
            return {"tool": meta.to_dict()}

        @self.app.post("/tools/{tool_name}/call")
        async def call_single_tool(tool_name: str, arguments: Dict[str, Any]):
            """调用单个工具"""
            self._add_log(f"调用工具: {tool_name} - 参数: {arguments}")
            try:
                result = await self._tool_loader.call(tool_name, **arguments)
                self._add_log(f"工具 {tool_name} 执行成功")
                return ToolResponse(result=result, success=True).dict()
            except ValueError as exc:
                self._add_log(f"工具 {tool_name} 执行失败: {exc}")
                return ToolResponse(result=None, success=False, error=str(exc)).dict()
            except Exception as exc:  # noqa: BLE001
                self._add_log(f"工具 {tool_name} 执行异常: {exc}")
                return ToolResponse(result=None, success=False, error=str(exc)).dict()

        @self.app.post("/tools/reload")
        async def reload_tools():
            """热重载工具元数据与绑定（不重启服务）"""
            self._add_log("开始热重载工具")
            try:
                self._tool_loader.reload()
                self._add_log(f"热重载完成，加载了 {len(self._tool_loader.tools_meta)} 个工具")
                return {
                    "success": True,
                    "tools_count": len(self._tool_loader.tools_meta),
                    "tools": self._tool_loader.get_tools_list(),
                }
            except Exception as exc:  # noqa: BLE001
                self._add_log(f"热重载失败: {exc}")
                return {"success": False, "error": str(exc)}

    def run(self, host: str = None, port: int = None, reload: bool = False, **kwargs):
        """
        运行服务器

        Args:
            host: 主机地址，默认使用配置文件中的值
            port: 端口号，默认使用配置文件中的值
            reload: 是否启用热重载（开发模式）
            **kwargs: 传递给 uvicorn.run 的其他参数
        """
        run_host = host or self.host
        run_port = port or self.port

        if reload:
            print("⚠️  热重载模式需要使用导入字符串，已自动禁用 reload")
            print("💡 提示: 如需热重载，请直接运行: uvicorn mylib.mcp.mcp:app --reload")
            reload = False

        self._add_log(f"启动 MCP Server 于 {run_host}:{run_port}")
        
        uvicorn.run(
            self.app,
            host=run_host,
            port=run_port,
            log_level="debug" if self.debug else "info",
            reload=reload,
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


# 全局应用实例（用于 uvicorn 热重载）
# 使用方式: uvicorn mylib.mcp.mcp:app --reload --host 0.0.0.0 --port 8080
app = MCPServer().app


if __name__ == "__main__":
    server = MCPServer()
    server.run()
