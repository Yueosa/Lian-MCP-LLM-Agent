"""
Agent 回调机制 (CallbackManager)

实现 Agent 间的异步通信和请求路由，打破固定流水线。

支持的回调类型：
- REPLAN: Executor → Planner，请求重新规划
- MORE_CONTEXT: Summary → RAG，请求更多上下文
- CLARIFY: Summary → Executor，请求澄清结果
- RETRY: 任意 Agent，请求重试
- ABORT: 任意 Agent，请求终止
"""

import asyncio
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Awaitable

from mylib.kernel.Lenum.agent import CallbackAction
from mylib.kit.Loutput import Loutput, FontColor8


@dataclass
class CallbackRequest:
    """回调请求"""
    request_id: str
    source_agent: str
    target_agent: str
    action: CallbackAction
    reason: str
    context: Dict[str, Any] = field(default_factory=dict)
    priority: str = "NORMAL"  # HIGH, NORMAL, LOW
    timeout_ms: int = 30000
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "action": self.action.value
        }


@dataclass
class CallbackResponse:
    """回调响应"""
    request_id: str
    status: str  # ACCEPTED, REJECTED, PARTIAL, TIMEOUT, ERROR
    source_agent: str
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)


# 回调处理器类型：接收 CallbackRequest，返回 CallbackResponse
CallbackHandler = Callable[[CallbackRequest], Awaitable[CallbackResponse]]


class CallbackManager:
    """
    回调管理器
    
    负责 Agent 间的异步通信和请求路由。
    
    使用示例:
    ```python
    manager = CallbackManager()
    
    # 注册处理器
    async def planner_handler(req: CallbackRequest) -> CallbackResponse:
        if req.action == CallbackAction.REPLAN:
            new_steps = generate_new_steps(req.context)
            return CallbackResponse(
                request_id=req.request_id,
                status="ACCEPTED",
                source_agent="Planner",
                data={"new_steps": new_steps}
            )
    
    manager.register_handler("Planner_Lian", planner_handler)
    
    # 发送回调
    request = CallbackRequest(
        request_id=str(uuid.uuid4()),
        source_agent="Executor_Ran",
        target_agent="Planner_Lian",
        action=CallbackAction.REPLAN,
        reason="工具调用失败"
    )
    response = await manager.send_callback(request)
    ```
    """
    
    def __init__(self, max_history: int = 1000):
        """
        初始化回调管理器
        
        :param max_history: 最大历史记录数
        """
        self.handlers: Dict[str, CallbackHandler] = {}
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.request_history: List[Dict] = []
        self.response_history: List[Dict] = []
        self.max_history = max_history
        self.lo = Loutput()
        
        # 回调统计
        self.stats = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "timeout": 0,
        }
        
    def register_handler(self, agent_id: str, handler: CallbackHandler):
        """
        注册 Agent 的回调处理器
        
        :param agent_id: Agent 标识
        :param handler: 异步处理函数
        """
        self.handlers[agent_id] = handler
        self.lo.lput(
            f"[CallbackManager] Registered handler for {agent_id}",
            font_color=FontColor8.CYAN
        )
        
    def unregister_handler(self, agent_id: str):
        """注销处理器"""
        if agent_id in self.handlers:
            del self.handlers[agent_id]
            
    async def send_callback(self, request: CallbackRequest) -> CallbackResponse:
        """
        发送回调请求
        
        :param request: 回调请求
        :return: 回调响应
        """
        self.stats["total_requests"] += 1
        
        # 1. 备份请求
        self._backup_request(request)
        
        self.lo.lput(
            f"[CallbackManager] {request.source_agent} → {request.target_agent}: "
            f"{request.action.value} ({request.reason[:50]})",
            font_color=FontColor8.YELLOW
        )
        
        # 2. 查找目标处理器
        handler = self.handlers.get(request.target_agent)
        if not handler:
            self.stats["failed"] += 1
            response = CallbackResponse(
                request_id=request.request_id,
                status="REJECTED",
                source_agent=request.target_agent,
                message=f"Target agent {request.target_agent} not found"
            )
            self._backup_response(response)
            return response
        
        # 3. 执行回调（带超时）
        try:
            response = await asyncio.wait_for(
                handler(request),
                timeout=request.timeout_ms / 1000
            )
            
            if response.status in ["ACCEPTED", "PARTIAL"]:
                self.stats["successful"] += 1
            else:
                self.stats["failed"] += 1
                
        except asyncio.TimeoutError:
            self.stats["timeout"] += 1
            response = CallbackResponse(
                request_id=request.request_id,
                status="TIMEOUT",
                source_agent=request.target_agent,
                message=f"Callback request timed out after {request.timeout_ms}ms"
            )
            
        except Exception as e:
            self.stats["failed"] += 1
            response = CallbackResponse(
                request_id=request.request_id,
                status="ERROR",
                source_agent=request.target_agent,
                message=f"Callback handler error: {str(e)}"
            )
        
        # 4. 备份响应
        self._backup_response(response)
        
        self.lo.lput(
            f"[CallbackManager] Response: {response.status} - {response.message[:50] if response.message else 'OK'}",
            font_color=FontColor8.GREEN if response.status == "ACCEPTED" else FontColor8.RED
        )
        
        return response
    
    def create_request(
        self,
        source_agent: str,
        target_agent: str,
        action: CallbackAction,
        reason: str,
        context: Dict = None,
        priority: str = "NORMAL",
        timeout_ms: int = 30000
    ) -> CallbackRequest:
        """
        创建回调请求的便捷方法
        """
        return CallbackRequest(
            request_id=str(uuid.uuid4()),
            source_agent=source_agent,
            target_agent=target_agent,
            action=action,
            reason=reason,
            context=context or {},
            priority=priority,
            timeout_ms=timeout_ms
        )
    
    def _backup_request(self, request: CallbackRequest):
        """备份请求到历史"""
        self.request_history.append(request.to_dict())
        if len(self.request_history) > self.max_history:
            self.request_history.pop(0)
            
    def _backup_response(self, response: CallbackResponse):
        """备份响应到历史"""
        self.response_history.append(response.to_dict())
        if len(self.response_history) > self.max_history:
            self.response_history.pop(0)
            
    def get_request_history(self, limit: int = 100) -> List[Dict]:
        """获取请求历史"""
        return self.request_history[-limit:]
    
    def get_response_history(self, limit: int = 100) -> List[Dict]:
        """获取响应历史"""
        return self.response_history[-limit:]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "registered_handlers": list(self.handlers.keys()),
            "history_size": {
                "requests": len(self.request_history),
                "responses": len(self.response_history)
            }
        }


class CallbackBuilder:
    """
    回调请求构建器
    
    提供流式 API 构建回调请求。
    
    使用示例:
    ```python
    request = (CallbackBuilder()
        .from_agent("Executor_Ran")
        .to_agent("Planner_Lian")
        .action(CallbackAction.REPLAN)
        .reason("工具调用失败")
        .context(failed_step=3, error="Permission denied")
        .high_priority()
        .build())
    ```
    """
    
    def __init__(self):
        self._source: str = ""
        self._target: str = ""
        self._action: CallbackAction = CallbackAction.RETRY
        self._reason: str = ""
        self._context: Dict = {}
        self._priority: str = "NORMAL"
        self._timeout: int = 30000
        
    def from_agent(self, agent_id: str) -> "CallbackBuilder":
        self._source = agent_id
        return self
    
    def to_agent(self, agent_id: str) -> "CallbackBuilder":
        self._target = agent_id
        return self
    
    def action(self, action: CallbackAction) -> "CallbackBuilder":
        self._action = action
        return self
    
    def reason(self, reason: str) -> "CallbackBuilder":
        self._reason = reason
        return self
    
    def context(self, **kwargs) -> "CallbackBuilder":
        self._context.update(kwargs)
        return self
    
    def high_priority(self) -> "CallbackBuilder":
        self._priority = "HIGH"
        return self
    
    def low_priority(self) -> "CallbackBuilder":
        self._priority = "LOW"
        return self
    
    def timeout(self, ms: int) -> "CallbackBuilder":
        self._timeout = ms
        return self
    
    def build(self) -> CallbackRequest:
        return CallbackRequest(
            request_id=str(uuid.uuid4()),
            source_agent=self._source,
            target_agent=self._target,
            action=self._action,
            reason=self._reason,
            context=self._context,
            priority=self._priority,
            timeout_ms=self._timeout
        )


# 全局回调管理器实例
callback_manager = CallbackManager()
