"""
Agent 状态机模块 (AgentFSM)

基于 kit/Lfsm 实现的 Agent 专用状态机，用于约束 LLM 操作流程。

核心功能：
1. 状态管理：维护 Agent 当前状态，支持状态切换
2. 转换约束：只允许预定义的状态转换
3. 历史追踪：记录所有状态转换，支持回溯
4. 回调支持：状态变化时触发回调函数
5. 状态持久化：自动同步到 StateStore，支持监控页面实时查看
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field, asdict

from mylib.kernel.Lenum.agent import AgentState, AgentTransition
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


@dataclass
class StateTransitionRecord:
    """状态转换记录"""
    from_state: str
    to_state: str
    event: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None


class AgentFSM:
    """
    Agent 专用状态机
    
    约束 LLM 操作，确保每一步都在可控范围内。
    继承自 LStateMachine 的设计理念，但专门针对 Agent 场景优化。
    
    使用示例:
    ```python
    fsm = AgentFSM("Executor_001")
    
    # 注册状态回调
    fsm.on_state(AgentState.COMPLETED, lambda r: print("任务完成!"))
    
    # 执行状态转换
    fsm.transition(AgentTransition.START)
    fsm.transition(AgentTransition.LLM_REQUEST)
    ...
    ```
    """
    
    # 状态转换表：定义了每个状态允许的转换
    TRANSITIONS: Dict[AgentState, Dict[AgentTransition, AgentState]] = {
        AgentState.IDLE: {
            AgentTransition.START: AgentState.INITIALIZING,
            AgentTransition.TERMINATE: AgentState.TERMINATED,
            AgentTransition.LLM_CALL: AgentState.WAITING_LLM,  # 直接开始 LLM 调用
        },
        AgentState.INITIALIZING: {
            AgentTransition.INIT_COMPLETE: AgentState.PROCESSING,
            AgentTransition.LLM_REQUEST: AgentState.WAITING_LLM,
            AgentTransition.LLM_CALL: AgentState.WAITING_LLM,
            AgentTransition.FAIL: AgentState.ERROR,
            AgentTransition.ERROR: AgentState.ERROR,
        },
        AgentState.PROCESSING: {
            AgentTransition.LLM_REQUEST: AgentState.WAITING_LLM,
            AgentTransition.LLM_CALL: AgentState.WAITING_LLM,
            AgentTransition.TOOL_CALL: AgentState.WAITING_TOOL,
            AgentTransition.CALLBACK_REQUEST: AgentState.CALLBACK_PENDING,
            AgentTransition.SUMMARIZE: AgentState.SUMMARIZING,
            AgentTransition.COMPLETE: AgentState.COMPLETED,
            AgentTransition.FAIL: AgentState.ERROR,
            AgentTransition.ERROR: AgentState.ERROR,
        },
        AgentState.WAITING_LLM: {
            AgentTransition.LLM_RESPONSE: AgentState.PARSING_RESPONSE,
            AgentTransition.LLM_DONE: AgentState.PROCESSING,  # 简化流程
            AgentTransition.FAIL: AgentState.ERROR,
            AgentTransition.ERROR: AgentState.ERROR,
        },
        AgentState.PARSING_RESPONSE: {
            AgentTransition.PARSE_COMPLETE: AgentState.PROCESSING,
            AgentTransition.TOOL_CALL: AgentState.WAITING_TOOL,
            AgentTransition.CALLBACK_REQUEST: AgentState.CALLBACK_PENDING,
            AgentTransition.COMPLETE: AgentState.SUMMARIZING,
            AgentTransition.FAIL: AgentState.ERROR,
            AgentTransition.ERROR: AgentState.ERROR,
        },
        AgentState.WAITING_TOOL: {
            AgentTransition.TOOL_RESULT: AgentState.PROCESSING,
            AgentTransition.FAIL: AgentState.ERROR,
            AgentTransition.ERROR: AgentState.ERROR,
        },
        AgentState.CALLBACK_PENDING: {
            AgentTransition.CALLBACK_RESPONSE: AgentState.PROCESSING,
            AgentTransition.FAIL: AgentState.ERROR,
            AgentTransition.ERROR: AgentState.ERROR,
        },
        AgentState.SUMMARIZING: {
            AgentTransition.COMPLETE: AgentState.COMPLETED,
            AgentTransition.CALLBACK_REQUEST: AgentState.CALLBACK_PENDING,
            AgentTransition.FAIL: AgentState.ERROR,
            AgentTransition.ERROR: AgentState.ERROR,
        },
        AgentState.COMPLETED: {
            AgentTransition.RESET: AgentState.IDLE,
            AgentTransition.START: AgentState.INITIALIZING,  # 支持直接开始新任务
        },
        AgentState.ERROR: {
            AgentTransition.RESET: AgentState.IDLE,
            AgentTransition.RETRY: AgentState.PROCESSING,
        },
        AgentState.TERMINATED: {
            # 终止状态无法转换
        },
    }
    
    def __init__(self, agent_id: str, agent_name: str = None):
        """
        初始化状态机
        
        :param agent_id: Agent 唯一标识
        :param agent_name: Agent 名称（可选）
        """
        self.agent_id = agent_id
        self.agent_name = agent_name or agent_id
        self.state: AgentState = AgentState.IDLE
        self.history: List[StateTransitionRecord] = []
        self.callbacks: Dict[AgentState, List[Callable]] = {}
        self.context: Dict[str, Any] = {}  # 状态上下文
        self._last_transition_time: Optional[datetime] = None
        self.lo = Loutput()
        
    @property
    def is_idle(self) -> bool:
        return self.state == AgentState.IDLE
    
    @property
    def is_running(self) -> bool:
        return self.state not in [AgentState.IDLE, AgentState.COMPLETED, AgentState.ERROR, AgentState.TERMINATED]
    
    @property
    def is_completed(self) -> bool:
        return self.state == AgentState.COMPLETED
    
    @property
    def is_error(self) -> bool:
        return self.state == AgentState.ERROR
        
    def transition(self, event: AgentTransition, data: Optional[Dict] = None) -> bool:
        """
        执行状态转换
        
        :param event: 触发事件
        :param data: 附加数据（可选）
        :return: 转换是否成功
        """
        current = self.state
        allowed = self.TRANSITIONS.get(current, {})
        
        if event not in allowed:
            self._log_invalid_transition(current, event)
            return False
        
        new_state = allowed[event]
        old_state = self.state
        self.state = new_state
        
        # 计算持续时间
        now = datetime.now()
        duration_ms = None
        if self._last_transition_time:
            duration_ms = int((now - self._last_transition_time).total_seconds() * 1000)
        self._last_transition_time = now
        
        # 记录历史
        record = StateTransitionRecord(
            from_state=old_state.name,
            to_state=new_state.name,
            event=event.name,
            timestamp=now.isoformat(),
            data=data,
            duration_ms=duration_ms
        )
        self.history.append(record)
        
        # 日志输出
        self._log_transition(record)
        
        # === 持久化状态到 StateStore（供监控页面读取）===
        try:
            store = _get_state_store()
            store.update_agent_state(self.agent_id, new_state.name, event.name)
        except Exception as e:
            pass  # 静默失败，不影响主流程
        
        # 触发通用转换回调
        if "_transition_callbacks" in self.context:
            for callback in self.context["_transition_callbacks"]:
                try:
                    callback(old_state, new_state, event)
                except Exception as e:
                    self.lo.lput(
                        f"[{self.agent_name}] FSM: Callback error: {e}",
                        font_color=FontColor8.RED
                    )
        
        # 触发特定状态回调
        if new_state in self.callbacks:
            for callback in self.callbacks[new_state]:
                try:
                    callback(record)
                except Exception as e:
                    self.lo.lput(
                        f"[{self.agent_name}] FSM: State callback error: {e}",
                        font_color=FontColor8.RED
                    )
        
        return True
    
    def can_transition(self, event: AgentTransition) -> bool:
        """
        检查是否允许某个转换
        
        :param event: 触发事件
        :return: 是否允许
        """
        allowed = self.TRANSITIONS.get(self.state, {})
        return event in allowed
    
    def get_allowed_transitions(self) -> List[AgentTransition]:
        """
        获取当前状态允许的所有转换
        
        :return: 允许的转换列表
        """
        return list(self.TRANSITIONS.get(self.state, {}).keys())
    
    def on_state(self, state: AgentState, callback: Callable[[StateTransitionRecord], None]):
        """
        注册状态变化回调
        
        :param state: 目标状态
        :param callback: 回调函数，接收 StateTransitionRecord
        """
        if state not in self.callbacks:
            self.callbacks[state] = []
        self.callbacks[state].append(callback)
    
    def on_transition(self, callback: Callable[[AgentState, AgentState, AgentTransition], None]):
        """
        注册通用状态转换回调
        
        :param callback: 回调函数，接收 (old_state, new_state, event)
        """
        # 使用特殊键存储通用回调
        if "_transition_callbacks" not in self.context:
            self.context["_transition_callbacks"] = []
        self.context["_transition_callbacks"].append(callback)
        
    def off_state(self, state: AgentState, callback: Callable = None):
        """
        移除状态变化回调
        
        :param state: 目标状态
        :param callback: 要移除的回调函数，None 表示移除所有
        """
        if state not in self.callbacks:
            return
        if callback is None:
            self.callbacks[state] = []
        else:
            self.callbacks[state] = [cb for cb in self.callbacks[state] if cb != callback]
    
    def reset(self) -> bool:
        """
        重置状态机到 IDLE 状态
        
        :return: 重置是否成功
        """
        if self.state in [AgentState.COMPLETED, AgentState.ERROR]:
            return self.transition(AgentTransition.RESET)
        elif self.state == AgentState.IDLE:
            return True  # 已经是 IDLE
        else:
            # 强制重置
            self.state = AgentState.IDLE
            self.history.append(StateTransitionRecord(
                from_state=self.state.name,
                to_state=AgentState.IDLE.name,
                event="FORCE_RESET",
                timestamp=datetime.now().isoformat()
            ))
            return True
    
    def get_history(self, limit: int = None) -> List[Dict]:
        """
        获取状态转换历史
        
        :param limit: 返回最近 N 条记录，None 表示全部
        :return: 历史记录列表
        """
        records = self.history[-limit:] if limit else self.history
        return [asdict(r) for r in records]
    
    def set_context(self, key: str, value: Any):
        """设置上下文数据"""
        self.context[key] = value
        
    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.context.get(key, default)
    
    def clear_context(self):
        """清空上下文"""
        self.context = {}
        
    def _fire_callbacks(self, state: AgentState, record: StateTransitionRecord):
        """触发状态回调"""
        callbacks = self.callbacks.get(state, [])
        for cb in callbacks:
            try:
                cb(record)
            except Exception as e:
                self.lo.lput(
                    f"[{self.agent_name}] Callback error for state {state.name}: {e}",
                    font_color=FontColor8.RED
                )
    
    def _log_transition(self, record: StateTransitionRecord):
        """日志记录状态转换"""
        duration_str = f" ({record.duration_ms}ms)" if record.duration_ms else ""
        self.lo.lput(
            f"[{self.agent_name}] FSM: {record.from_state} → {record.to_state} "
            f"[{record.event}]{duration_str}",
            font_color=FontColor8.CYAN
        )
    
    def _log_invalid_transition(self, current: AgentState, event: AgentTransition):
        """日志记录无效转换"""
        allowed = self.get_allowed_transitions()
        allowed_str = ", ".join([t.name for t in allowed]) if allowed else "无"
        self.lo.lput(
            f"[{self.agent_name}] FSM: Invalid transition! "
            f"Current={current.name}, Event={event.name}, Allowed=[{allowed_str}]",
            font_color=FontColor8.RED
        )
    
    def __repr__(self) -> str:
        return f"AgentFSM(agent_id={self.agent_id}, state={self.state.name})"


class AgentFSMManager:
    """
    状态机管理器
    
    用于管理多个 Agent 的状态机实例，支持全局状态查询。
    """
    
    def __init__(self):
        self.fsm_instances: Dict[str, AgentFSM] = {}
        
    def register(self, agent_id: str, fsm: AgentFSM):
        """注册状态机实例"""
        self.fsm_instances[agent_id] = fsm
        
    def create_fsm(self, agent_id: str, agent_name: str = None) -> AgentFSM:
        """创建新的状态机实例"""
        fsm = AgentFSM(agent_id, agent_name)
        self.fsm_instances[agent_id] = fsm
        return fsm
    
    def get_fsm(self, agent_id: str) -> Optional[AgentFSM]:
        """获取状态机实例"""
        return self.fsm_instances.get(agent_id)
    
    def remove_fsm(self, agent_id: str):
        """移除状态机实例"""
        if agent_id in self.fsm_instances:
            del self.fsm_instances[agent_id]
            
    def get_all_states(self) -> Dict[str, str]:
        """获取所有 Agent 的当前状态"""
        return {
            agent_id: fsm.state.name 
            for agent_id, fsm in self.fsm_instances.items()
        }
    
    def get_running_agents(self) -> List[str]:
        """获取正在运行的 Agent 列表"""
        return [
            agent_id 
            for agent_id, fsm in self.fsm_instances.items() 
            if fsm.is_running
        ]


# 全局状态机管理器实例
fsm_manager = AgentFSMManager()
