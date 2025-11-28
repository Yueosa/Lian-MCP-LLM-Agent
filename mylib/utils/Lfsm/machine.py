from typing import Generic, TypeVar, List, Any, Optional, Dict
from enum import Enum
from mylib.utils.Lstack import Lstack

S = TypeVar('S', bound=Enum)  # State Enum Type
R = TypeVar('R')              # Result Type

class LStateMachine(Generic[S, R]):
    """
    Lian Finite State Machine (Lfsm) 基类
    
    用于构建基于字符流的解析器，集成了 Lstack 用于处理嵌套结构。
    """
    
    def __init__(self, initial_state: S):
        self.state: S = initial_state
        self.stack = Lstack()
        self.buffer: List[str] = []
        self.results: List[R] = []
        self.context: Dict[str, Any] = {}  # 用于存储上下文信息，如 dollar_tag
    
    def switch_state(self, new_state: S):
        """切换状态"""
        if self.state != new_state:
            # 未来可以扩展 on_exit / on_enter 钩子
            self.state = new_state

    def parse(self, content: str) -> List[R]:
        """解析字符串入口"""
        self._reset()
        
        n = len(content)
        i = 0
        while i < n:
            char = content[i]
            
            # 动态分发到 handle_{state_name} 方法
            # 例如: handle_normal, handle_string
            handler_name = f"handle_{self.state.name.lower()}"
            handler = getattr(self, handler_name, self.handle_default)
            
            # Handler 接收当前字符、索引、完整内容、总长度
            # 返回新的索引位置 (int)，如果返回 None 则默认 +1
            new_i = handler(char, i, content, n)
            
            if new_i is not None:
                i = new_i
            else:
                i += 1
        
        self.on_finish()
        return self.results

    def _reset(self):
        """重置内部状态"""
        self.buffer = []
        self.results = []
        self.stack.clear()
        self.context = {}

    def handle_default(self, char: str, i: int, content: str, n: int) -> int:
        """默认处理逻辑：直接写入 buffer"""
        self.buffer.append(char)
        return i + 1
        
    def on_finish(self):
        """解析结束时的回调，可用于处理 buffer 中剩余的内容"""
        remaining = self.flush_buffer()
        if remaining:
            # 默认行为：如果 buffer 还有东西，尝试作为一个结果发出
            # 子类可以重写此行为
            pass
            
    def emit(self, result: R):
        """产出一个结果"""
        self.results.append(result)
        
    def append_buffer(self, char: str):
        """写入 buffer"""
        self.buffer.append(char)
        
    def flush_buffer(self) -> str:
        """清空并返回 buffer 内容"""
        res = "".join(self.buffer)
        self.buffer = []
        return res.strip()
