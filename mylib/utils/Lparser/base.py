from typing import Any, Optional
from mylib.utils.Lfsm.machine import LStateMachine
from mylib.utils.Ltokenizer import LToken

from .type import S, R


class LParserBase(LStateMachine[S, R]):
    """
    Abstract base class for Parsers.
    解析器的抽象基类
    Inherits from LStateMachine and processes a list of LToken.
    继承于 LStateMachine, 并处理 LToken 列表
    """
    def __init__(self, initial_state: S):
        super().__init__(initial_state)
        self.current_token: Optional[LToken] = None

    def _on_step(self, item: Any):
        if isinstance(item, LToken):
            self.current_token = item
            # Sync line/col from token for context
            # 从令牌同步行/列以获取上下文
            self.line = item.line
            self.col = item.col

    def error(self, message: str):
        """抛出一个包含上下文信息的解析错误"""
        token_info = f" at {self.current_token}" if self.current_token else ""
        raise ValueError(f"Parse Error{token_info}: {message}")
