"""
Agent 日志系统 (AgentLogger)

基于 kit/Loutput 实现的细粒度日志系统，支持：
1. 终端彩色输出
2. 内存缓存（循环缓冲）
3. 结构化日志格式
4. WebSocket 实时推送（用于监控页面）
5. 日志级别过滤
6. 状态持久化（同步到 StateStore）

日志级别：
- SYSTEM: 系统级事件（启动/关闭/配置）
- AGENT: Agent 生命周期（创建/销毁/状态变化）
- TASK: 任务级（任务创建/步骤执行/完成）
- LLM: LLM 交互（请求/响应/Token 统计）
- TOOL: 工具调用（调用/结果/耗时）
- DEBUG: 调试信息
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Callable

from mylib.kit.Loutput import Loutput, FontColor8

# 延迟导入避免循环依赖
_state_store = None

def _get_state_store():
    """延迟获取 state_store 实例"""
    global _state_store
    if _state_store is None:
        from mylib.agent.state_store import state_store
        _state_store = state_store
    return _state_store


class LogLevel(Enum):
    """日志级别"""
    SYSTEM = 1   # 系统级事件
    AGENT = 2    # Agent 生命周期
    TASK = 3     # 任务级
    LLM = 4      # LLM 交互
    TOOL = 5     # 工具调用
    DEBUG = 6    # 调试信息


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: LogLevel
    agent_id: str
    agent_name: str
    event: str
    message: str
    session_id: Optional[str] = None
    task_id: Optional[int] = None
    step_id: Optional[int] = None
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.name,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "step_id": self.step_id,
            "event": self.event,
            "message": self.message,
            "data": self.data,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AgentLogger:
    """
    Agent 专用日志器
    
    支持终端输出、内存缓存、WebSocket 推送。
    
    使用示例:
    ```python
    logger = AgentLogger("exec_001", "Executor_Ran")
    
    # 记录日志
    logger.log(LogLevel.TOOL, "TOOL_CALL", "调用 web_search", data={"tool": "web_search"})
    
    # 便捷方法
    logger.tool("web_search", "开始搜索", args={"query": "test"})
    logger.llm_request(messages=[...], model="deepseek-chat")
    logger.llm_response(content="...", tokens=1234)
    ```
    """
    
    # 日志级别颜色映射
    LEVEL_COLORS = {
        LogLevel.SYSTEM: FontColor8.CYAN,
        LogLevel.AGENT: FontColor8.MAGENTA,
        LogLevel.TASK: FontColor8.BLUE,
        LogLevel.LLM: FontColor8.YELLOW,
        LogLevel.TOOL: FontColor8.GREEN,
        LogLevel.DEBUG: FontColor8.WHITE,
    }
    
    # 日志级别图标
    LEVEL_ICONS = {
        LogLevel.SYSTEM: "⚙️",
        LogLevel.AGENT: "🤖",
        LogLevel.TASK: "📋",
        LogLevel.LLM: "🧠",
        LogLevel.TOOL: "🔧",
        LogLevel.DEBUG: "🔍",
    }
    
    def __init__(
        self, 
        agent_id: str, 
        agent_name: str = None,
        session_id: str = None,
        max_buffer_size: int = 1000,
        min_level: LogLevel = LogLevel.DEBUG,
        enable_terminal: bool = True
    ):
        """
        初始化日志器
        
        :param agent_id: Agent 唯一标识
        :param agent_name: Agent 名称
        :param session_id: 会话 ID
        :param max_buffer_size: 最大缓存条目数
        :param min_level: 最小日志级别
        :param enable_terminal: 是否启用终端输出
        """
        self.agent_id = agent_id
        self.agent_name = agent_name or agent_id
        self.session_id = session_id or self._generate_session_id()
        self.max_buffer_size = max_buffer_size
        self.min_level = min_level
        self.enable_terminal = enable_terminal
        
        self.lo = Loutput()
        self.buffer: List[LogEntry] = []
        self.subscribers: List[asyncio.Queue] = []  # WebSocket 订阅者
        self._task_id: Optional[int] = None
        self._step_id: Optional[int] = None
        
    @staticmethod
    def _generate_session_id() -> str:
        """生成会话 ID"""
        return f"sess_{uuid.uuid4().hex[:12]}"
    
    def set_task_context(self, task_id: int = None, step_id: int = None):
        """设置当前任务上下文"""
        self._task_id = task_id
        self._step_id = step_id
        
    def clear_task_context(self):
        """清除任务上下文"""
        self._task_id = None
        self._step_id = None
        
    def log(
        self, 
        level: LogLevel, 
        event: str, 
        message: str,
        task_id: int = None,
        step_id: int = None,
        data: Dict = None,
        duration_ms: int = None,
        metadata: Dict = None
    ) -> LogEntry:
        """
        记录日志
        
        :param level: 日志级别
        :param event: 事件类型
        :param message: 日志消息
        :param task_id: 任务 ID（可选）
        :param step_id: 步骤 ID（可选）
        :param data: 附加数据
        :param duration_ms: 持续时间（毫秒）
        :param metadata: 元数据
        :return: 日志条目
        """
        # 级别过滤
        if level.value > self.min_level.value:
            return None
            
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            session_id=self.session_id,
            task_id=task_id or self._task_id,
            step_id=step_id or self._step_id,
            event=event,
            message=message,
            data=data or {},
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        
        # 1. 终端输出
        if self.enable_terminal:
            self._print_to_terminal(entry)
        
        # 2. 缓存
        self._add_to_buffer(entry)
        
        # 3. 推送到订阅者
        self._notify_subscribers(entry)
        
        # 4. 持久化到 StateStore（供监控页面读取）
        try:
            store = _get_state_store()
            store.add_log(entry.to_dict())
        except Exception:
            pass  # 静默失败，不影响主流程
        
        return entry
    
    # ==================== 便捷方法 ====================
    
    def system(self, event: str, message: str, **kwargs) -> LogEntry:
        """记录系统级日志"""
        return self.log(LogLevel.SYSTEM, event, message, **kwargs)
    
    def agent(self, event: str, message: str, **kwargs) -> LogEntry:
        """记录 Agent 级日志"""
        return self.log(LogLevel.AGENT, event, message, **kwargs)
    
    def task(self, event: str, message: str, **kwargs) -> LogEntry:
        """记录任务级日志"""
        return self.log(LogLevel.TASK, event, message, **kwargs)
    
    def llm(self, event: str, message: str, **kwargs) -> LogEntry:
        """记录 LLM 级日志"""
        return self.log(LogLevel.LLM, event, message, **kwargs)
    
    def tool(self, event: str, message: str, **kwargs) -> LogEntry:
        """记录工具级日志"""
        return self.log(LogLevel.TOOL, event, message, **kwargs)
    
    def debug(self, event: str, message: str, **kwargs) -> LogEntry:
        """记录调试日志"""
        return self.log(LogLevel.DEBUG, event, message, **kwargs)
    
    # ==================== 场景化便捷方法 ====================
    
    def llm_request(self, messages: List[Dict], model: str = None, **kwargs) -> LogEntry:
        """记录 LLM 请求"""
        msg_count = len(messages)
        total_chars = sum(len(m.get("content", "")) for m in messages)
        
        # 构建消息预览（保留更多内容用于详情展开）
        messages_preview = []
        for m in messages:
            content = m.get("content", "")
            preview = content[:500] + "..." if len(content) > 500 else content
            messages_preview.append({
                "role": m.get("role", "?"),
                "content_preview": preview,
                "content_length": len(content)
            })
        
        return self.llm(
            "LLM_REQUEST",
            f"发起 LLM 请求: {msg_count} 条消息, {total_chars} 字符",
            data={
                "model": model, 
                "message_count": msg_count, 
                "total_chars": total_chars,
                "messages": messages_preview
            },
            **kwargs
        )
    
    def llm_response(self, content: str, tokens: int = None, duration_ms: int = None, **kwargs) -> LogEntry:
        """记录 LLM 响应"""
        # 保留更长的内容预览
        content_preview = content[:1000] + "..." if len(content) > 1000 else content
        return self.llm(
            "LLM_RESPONSE",
            f"收到 LLM 响应: {len(content)} 字符",
            data={
                "content_preview": content_preview, 
                "content_length": len(content),
                "tokens": tokens
            },
            duration_ms=duration_ms,
            **kwargs
        )
    
    def tool_call(self, tool_name: str, args: Dict, **kwargs) -> LogEntry:
        """记录工具调用"""
        # 将参数转为字符串预览
        args_str = json.dumps(args, ensure_ascii=False) if args else "{}"
        args_preview = args_str[:500] + "..." if len(args_str) > 500 else args_str
        return self.tool(
            "TOOL_CALL",
            f"调用工具: {tool_name}",
            data={
                "tool_name": tool_name, 
                "arguments": args,
                "arguments_preview": args_preview
            },
            **kwargs
        )
    
    def tool_result(self, tool_name: str, result: Any, duration_ms: int = None, success: bool = True, **kwargs) -> LogEntry:
        """记录工具结果"""
        result_str = str(result)
        result_preview = result_str[:500] + "..." if len(result_str) > 500 else result_str
        return self.tool(
            "TOOL_RESULT" if success else "TOOL_ERROR",
            f"工具 {tool_name} {'成功' if success else '失败'}",
            data={
                "tool_name": tool_name, 
                "result_preview": result_preview, 
                "result_length": len(result_str),
                "success": success
            },
            duration_ms=duration_ms,
            **kwargs
        )
    
    def state_change(self, from_state: str, to_state: str, event: str, **kwargs) -> LogEntry:
        """记录状态变化"""
        return self.agent(
            "STATE_CHANGE",
            f"状态转换: {from_state} → {to_state} [{event}]",
            data={"from_state": from_state, "to_state": to_state, "trigger": event},
            **kwargs
        )
    
    def task_start(self, task_id: int, title: str, **kwargs) -> LogEntry:
        """记录任务开始"""
        self._task_id = task_id
        return self.task(
            "TASK_START",
            f"任务开始: {title}",
            task_id=task_id,
            data={"title": title},
            **kwargs
        )
    
    def task_complete(self, task_id: int, success: bool = True, **kwargs) -> LogEntry:
        """记录任务完成"""
        return self.task(
            "TASK_COMPLETE" if success else "TASK_FAILED",
            f"任务{'完成' if success else '失败'}: ID={task_id}",
            task_id=task_id,
            data={"success": success},
            **kwargs
        )
    
    def step_start(self, step_id: int, step_index: int, instruction: str, **kwargs) -> LogEntry:
        """记录步骤开始"""
        self._step_id = step_id
        return self.task(
            "STEP_START",
            f"步骤 {step_index} 开始",
            step_id=step_id,
            data={"step_index": step_index, "instruction": instruction[:100]},
            **kwargs
        )
    
    def step_complete(self, step_id: int, step_index: int, success: bool = True, **kwargs) -> LogEntry:
        """记录步骤完成"""
        return self.task(
            "STEP_COMPLETE" if success else "STEP_FAILED",
            f"步骤 {step_index} {'完成' if success else '失败'}",
            step_id=step_id,
            data={"step_index": step_index, "success": success},
            **kwargs
        )
    
    def callback_request(self, target: str, action: str, reason: str, **kwargs) -> LogEntry:
        """记录回调请求"""
        return self.agent(
            "CALLBACK_REQUEST",
            f"发起回调: {target}.{action}",
            data={"target": target, "action": action, "reason": reason},
            **kwargs
        )
    
    def callback_response(self, source: str, status: str, **kwargs) -> LogEntry:
        """记录回调响应"""
        return self.agent(
            "CALLBACK_RESPONSE",
            f"收到回调响应: {source} -> {status}",
            data={"source": source, "status": status},
            **kwargs
        )
    
    # ==================== 内部方法 ====================
    
    def _print_to_terminal(self, entry: LogEntry):
        """格式化输出到终端"""
        color = self.LEVEL_COLORS.get(entry.level, FontColor8.WHITE)
        icon = self.LEVEL_ICONS.get(entry.level, "📝")
        
        time_str = entry.timestamp.strftime('%H:%M:%S.%f')[:-3]
        level_str = f"[{entry.level.name:6}]"
        agent_str = f"[{entry.agent_name}]"
        duration_str = f" ({entry.duration_ms}ms)" if entry.duration_ms else ""
        
        self.lo.lput(
            f"{icon} {time_str} {level_str} {agent_str} {entry.event}: {entry.message}{duration_str}",
            font_color=color
        )
        
    def _add_to_buffer(self, entry: LogEntry):
        """添加到缓存（循环缓冲）"""
        self.buffer.append(entry)
        if len(self.buffer) > self.max_buffer_size:
            self.buffer.pop(0)
            
    def _notify_subscribers(self, entry: LogEntry):
        """通知 WebSocket 订阅者"""
        for queue in self.subscribers:
            try:
                queue.put_nowait(entry)
            except asyncio.QueueFull:
                # 队列满了，丢弃旧日志
                try:
                    queue.get_nowait()
                    queue.put_nowait(entry)
                except:
                    pass
                    
    # ==================== 订阅管理 ====================
    
    def subscribe(self, max_size: int = 100) -> asyncio.Queue:
        """
        订阅日志流
        
        :param max_size: 队列最大容量
        :return: 日志队列
        """
        queue = asyncio.Queue(maxsize=max_size)
        self.subscribers.append(queue)
        return queue
        
    def unsubscribe(self, queue: asyncio.Queue):
        """取消订阅"""
        if queue in self.subscribers:
            self.subscribers.remove(queue)
            
    # ==================== 查询方法 ====================
    
    def get_history(self, limit: int = 100, level: LogLevel = None, event: str = None) -> List[Dict]:
        """
        获取历史日志
        
        :param limit: 返回最近 N 条记录
        :param level: 过滤日志级别
        :param event: 过滤事件类型
        :return: 日志列表
        """
        entries = self.buffer[-limit:] if limit else self.buffer
        
        if level:
            entries = [e for e in entries if e.level == level]
        if event:
            entries = [e for e in entries if e.event == event]
            
        return [e.to_dict() for e in entries]
    
    def get_stats(self) -> Dict:
        """获取日志统计信息"""
        level_counts = {}
        for entry in self.buffer:
            level_name = entry.level.name
            level_counts[level_name] = level_counts.get(level_name, 0) + 1
            
        return {
            "total_entries": len(self.buffer),
            "buffer_capacity": self.max_buffer_size,
            "level_counts": level_counts,
            "subscribers": len(self.subscribers),
            "session_id": self.session_id,
        }


class LoggerManager:
    """
    日志器管理器
    
    集中管理所有 Agent 的日志器实例。
    """
    
    def __init__(self):
        self.loggers: Dict[str, AgentLogger] = {}
        self.global_subscribers: List[asyncio.Queue] = []  # 全局订阅者
    
    def register(self, agent_id: str, logger: AgentLogger):
        """注册日志器实例"""
        # 连接全局订阅者
        for queue in self.global_subscribers:
            if queue not in logger.subscribers:
                logger.subscribers.append(queue)
        self.loggers[agent_id] = logger
        
    def create_logger(
        self, 
        agent_id: str, 
        agent_name: str = None,
        session_id: str = None,
        **kwargs
    ) -> AgentLogger:
        """创建新的日志器"""
        logger = AgentLogger(agent_id, agent_name, session_id, **kwargs)
        
        # 连接全局订阅者
        for queue in self.global_subscribers:
            logger.subscribers.append(queue)
            
        self.loggers[agent_id] = logger
        return logger
    
    def get_logger(self, agent_id: str) -> Optional[AgentLogger]:
        """获取日志器"""
        return self.loggers.get(agent_id)
    
    def remove_logger(self, agent_id: str):
        """移除日志器"""
        if agent_id in self.loggers:
            del self.loggers[agent_id]
            
    def subscribe_all(self, max_size: int = 500) -> asyncio.Queue:
        """订阅所有 Agent 的日志"""
        queue = asyncio.Queue(maxsize=max_size)
        self.global_subscribers.append(queue)
        
        # 连接到现有日志器
        for logger in self.loggers.values():
            logger.subscribers.append(queue)
            
        return queue
    
    def unsubscribe_all(self, queue: asyncio.Queue):
        """取消全局订阅"""
        if queue in self.global_subscribers:
            self.global_subscribers.remove(queue)
            
        for logger in self.loggers.values():
            logger.unsubscribe(queue)
            
    def get_all_history(self, limit: int = 100) -> List[Dict]:
        """获取所有日志器的历史（按时间排序）"""
        all_entries = []
        for logger in self.loggers.values():
            all_entries.extend(logger.buffer)
            
        # 按时间排序
        all_entries.sort(key=lambda x: x.timestamp)
        
        # 返回最近的
        return [e.to_dict() for e in all_entries[-limit:]]


# 全局日志管理器实例
logger_manager = LoggerManager()
