"""
Agent 监控 API (Monitor API)

提供 Agent 状态监控的 HTTP API 接口。

功能：
1. /api/state - 获取完整状态
2. /api/agents - 获取 Agent 状态
3. /api/logs - 获取日志
4. /api/stats - 获取统计信息
5. /api/log/{id} - 获取单条日志详情
6. /api/clear - 清空数据
"""

import os
import uvicorn
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from mylib.agent.state_store import state_store


# 创建 FastAPI 应用
app = FastAPI(
    title="Agent Monitor API",
    description="Multi-Agent 系统监控 API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件目录
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


# ==================== API 路由 ====================

@app.get("/")
async def root():
    """根路由 - 返回监控页面"""
    html_path = STATIC_DIR / "monitor.html"
    if html_path.exists():
        return FileResponse(html_path)
    return JSONResponse({
        "status": "ok",
        "service": "Agent Monitor API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })


@app.get("/api/state")
async def get_full_state():
    """获取完整状态"""
    return state_store.get_all_state()


@app.get("/api/agents")
async def get_agents():
    """获取所有 Agent 状态"""
    agents = state_store.get_agent_states()
    return {
        "agents": agents,
        "count": len(agents),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """获取单个 Agent 状态"""
    agent = state_store.get_agent_state(agent_id)
    if agent:
        return agent
    return JSONResponse(
        status_code=404,
        content={"error": f"Agent '{agent_id}' not found"}
    )


@app.get("/api/logs")
async def get_logs(
    limit: int = Query(100, ge=1, le=500),
    agent_id: Optional[str] = None,
    level: Optional[str] = None
):
    """获取日志列表"""
    logs = state_store.get_logs(limit=limit, agent_id=agent_id, level=level)
    return {
        "logs": logs,
        "count": len(logs),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/logs/{log_index}")
async def get_log_detail(log_index: int):
    """获取单条日志详情"""
    logs = state_store.get_logs(limit=500)
    if 0 <= log_index < len(logs):
        return logs[log_index]
    return JSONResponse(
        status_code=404,
        content={"error": f"Log index {log_index} not found"}
    )


@app.get("/api/tasks")
async def get_tasks():
    """获取任务列表"""
    tasks = state_store.get_tasks()
    return {
        "tasks": tasks,
        "count": len(tasks),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/callbacks")
async def get_callbacks(limit: int = Query(50, ge=1, le=200)):
    """获取回调记录"""
    callbacks = state_store.get_callbacks(limit=limit)
    return {
        "callbacks": callbacks,
        "count": len(callbacks),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    stats = state_store.get_stats()
    return {
        **stats,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/clear/logs")
async def clear_logs():
    """清空日志"""
    state_store.clear_logs()
    return {"status": "ok", "message": "Logs cleared"}


@app.post("/api/clear/tasks")
async def clear_tasks():
    """清空任务"""
    state_store.clear_tasks()
    return {"status": "ok", "message": "Tasks cleared"}


@app.post("/api/clear/callbacks")
async def clear_callbacks():
    """清空回调"""
    state_store.clear_callbacks()
    return {"status": "ok", "message": "Callbacks cleared"}


@app.post("/api/reset")
async def reset_session():
    """重置整个会话"""
    state_store.reset_session()
    return {"status": "ok", "message": "Session reset"}


# 挂载静态文件（放在最后，避免覆盖 API 路由）
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def run_monitor_server(host: str = "0.0.0.0", port: int = 8502):
    """启动监控服务器"""
    print(f"🔮 Agent Monitor API 启动中...")
    print(f"   地址: http://{host}:{port}")
    print(f"   监控页面: http://localhost:{port}/")
    print(f"   API 文档: http://localhost:{port}/docs")
    
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    run_monitor_server()
