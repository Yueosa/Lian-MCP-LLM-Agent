import json
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Any, Dict, List, Optional
import importlib.util
import sys
from pathlib import Path

# 导入工具模块
from .tools.file_tools import FileTools
from .tools.web_tools import WebTools
from .tools.math_tools import MathTools


from .base import ToolCall, ToolCallRequest, ToolResponse


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
        self.file_tools = FileTools()
        self.web_tools = WebTools()
        self.math_tools = MathTools()
        self.custom_tools = {}
    
    def get_tools_list(self) -> List[Dict]:
        """返回所有可用工具列表"""
        tools = []
        
        # 文件工具
        tools.extend([
            {
                "name": "read_file",
                "description": "读取文件内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "文件路径"}
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "write_file",
                "description": "写入文件内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "文件路径"},
                        "content": {"type": "string", "description": "文件内容"}
                    },
                    "required": ["file_path", "content"]
                }
            }
        ])
        
        # 网络工具
        tools.extend([
            {
                "name": "fetch_webpage",
                "description": "获取网页内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "网页URL"}
                    },
                    "required": ["url"]
                }
            }
        ])
        
        # 数学工具
        tools.extend([
            {
                "name": "calculate_expression",
                "description": "计算数学表达式",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "数学表达式"}
                    },
                    "required": ["expression"]
                }
            }
        ])
        
        return tools
    
    async def execute_tool(self, tool_name: str, arguments: Dict) -> ToolResponse:
        """执行工具调用"""
        try:
            if tool_name == "read_file":
                result = await self.file_tools.read_file(arguments["file_path"])
            elif tool_name == "write_file":
                result = await self.file_tools.write_file(arguments["file_path"], arguments["content"])
            elif tool_name == "fetch_webpage":
                result = await self.web_tools.fetch_webpage(arguments["url"])
            elif tool_name == "calculate_expression":
                result = await self.math_tools.calculate_expression(arguments["expression"])
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
