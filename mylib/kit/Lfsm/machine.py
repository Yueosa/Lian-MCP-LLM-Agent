from typing import Generic, List, Any, Dict

from .type import S, R

class LStateMachine(Generic[S, R]):
    """
    Lian Finite State Machine (Lfsm) 通用基类
    
    这是一个通用的状态机引擎, 用于驱动基于流 (Stream) 的解析逻辑。
    它不仅支持字符流 (用于词法分析/Tokenizer) , 也支持对象流 (如 Token 流, 用于语法分析/Parser) 。
    
    核心功能：
    1. 状态管理：维护当前状态 (S) 并支持状态切换。
    2. 动态分发：自动将处理逻辑分发到 `handle_{state_name}` 方法。
    3. 上下文追踪：内置行号、列号追踪及上下文存储。
    
    泛型参数：
    - S: 状态枚举类型 (Enum)
    - R: 产出结果类型 (Result Type)
    """
    
    def __init__(self, initial_state: S):
        self.state: S = initial_state
        self.buffer: List[str] = []
        self.results: List[R] = []
        self.context: Dict[str, Any] = {}  # 用于存储上下文信息, 如 dollar_tag
        self.line = 1
        self.col = 1
    
    def switch_state(self, new_state: S):
        """切换状态"""
        if self.state != new_state:
            self.state = new_state

    def parse(self, content: Any) -> List[R]:
        """解析入口
        content 可以是字符串, 也可以是 Token 列表
        """
        self._reset()
        
        n = len(content)
        i = 0
        while i < n:
            item = content[i]
            
            self._on_step(item)

            # 动态分发到 handle_{state_name} 方法
            handler = getattr(self, f"handle_{self.state.name.lower()}", self.handle_default)
            new_i = handler(item, i, content, n)
            
            if new_i is not None:
                i = new_i
            else:
                i += 1
        
        self.on_finish()
        return self.results

    def _on_step(self, item: Any):
        """每一步的回调, 用于更新行号等"""
        pass

    def _reset(self):
        """重置内部状态"""
        self.buffer = []
        self.results = []
        self.context = {}
        self.line = 1
        self.col = 1

    def handle_default(self, char: str, i: int, content: str, len: int) -> int:
        """默认处理逻辑：直接写入 buffer"""
        self.buffer.append(char)
        return i + 1
        
    def on_finish(self):
        """解析结束时的回调, 可用于处理 buffer 中剩余的内容"""
        remaining = self.flush_buffer()
        if remaining:
            # 默认行为：如果 buffer 还有东西, 尝试作为一个结果发出
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
    
    def flush_result(self) -> List[R]:
        """返回result"""
        return self.results
    
    def error(self, message: str):
        """抛出错误, 子类可重写以提供更多上下文"""
        raise ValueError(f"StateMachine Error at line {self.line}, col {self.col}: {message}")
