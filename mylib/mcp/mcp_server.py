from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Any, Dict, List

from .base import ToolCall, ToolCallRequest, ToolResponse

# 动态工具元数据加载器
from .tools.tools_meta_loader import ToolsMetaLoader


app = FastAPI(title="MCP Server", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class MCPTools:
    def __init__(self):
        # 使用工具元数据加载器发现并实例化工具
        self.loader = ToolsMetaLoader()
        self.loader.discover()
        # 工具元数据（用于 /tools 列表）
        self.tools_meta = self.loader.tools_meta
        # 名称 -> 可调用（绑定方法）
        self.tools_callables = self.loader.callables
        self.custom_tools = {}
    
    def get_tools_list(self) -> List[Dict]:
        """返回所有可用工具列表"""
        # 直接返回加载器格式化后的元数据
        return self.loader.get_tools_list()
    
    async def execute_tool(self, tool_name: str, arguments: Dict) -> ToolResponse:
        """执行工具调用"""
        try:
            # 优先在动态加载的工具中查找
            if tool_name in self.tools_callables:
                fn = self.tools_callables[tool_name]
                # 假设工具方法签名以关键字参数为主，直接解包
                result = await fn(**arguments)
            elif tool_name in self.custom_tools:
                fn = self.custom_tools[tool_name]
                result = await fn(**arguments)
            else:
                return ToolResponse(
                    result=None,
                    success=False,
                    error=f"未知工具: {tool_name}"
                )

            return ToolResponse(result=result, success=True)
            
        except Exception as e:
            return ToolResponse(
                result=None,
                success=False,
                error=str(e)
            )

mcp_tools = MCPTools()

@app.get("/")
async def root():
    return {"message": "MCP Server is running"}

@app.get("/tools")
async def list_tools():
    """获取所有可用工具"""
    return {"tools": mcp_tools.get_tools_list()}

@app.post("/tools/call")
async def call_tools(request: ToolCallRequest):
    """执行工具调用"""
    responses = []
    
    for tool_call in request.tool_calls:
        response = await mcp_tools.execute_tool(tool_call.name, tool_call.arguments)
        responses.append({
            "tool": tool_call.name,
            "result": response.result,
            "success": response.success,
            "error": response.error
        })
    
    return {"responses": responses}

@app.post("/tools/{tool_name}")
async def call_single_tool(tool_name: str, arguments: Dict):
    """执行单个工具调用"""
    response = await mcp_tools.execute_tool(tool_name, arguments)
    return response.dict()

if __name__ == "__main__":
    # 使用统一配置
    try:
        from .config import Config
        host = Config.MCP.host
        port = Config.MCP.port
    except Exception:
        host = "0.0.0.0"
        port = 8000

    uvicorn.run(app, host=host, port=port)
