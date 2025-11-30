from typing import Any
from enum import Enum
from mylib.kit.Lfsm.machine import LStateMachine
from .token import LToken
from .type import S

class LTokenizerBase(LStateMachine[S, LToken]):
    """
    Abstract base class for Tokenizers.
    Tokenizer 的抽象基类
    Inherits from LStateMachine and produces a list of LToken.
    继承于 LStateMachine, 并生成一个 LToken 列表
    """
    def __init__(self, initial_state: S):
        super().__init__(initial_state)
        self.token_start_line = 1
        self.token_start_col = 1

    def _on_step(self, item: Any):
        if isinstance(item, str):
            if item == '\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1

    def mark_start(self):
        """标记当前 Token 的起始位置"""
        self.token_start_line = self.line
        self.token_start_col = self.col

    def emit(self, token_type: S, value: str = None):
        """
        Emit a token.
        发出一个 Token 
        If value is None, it uses the current buffer content.
        如果值为 None, 使用当前缓冲区内容
        Clears the buffer after emitting.
        发送 Token 后清空缓冲区
        """
        if value is None:
            value = "".join(self.buffer)
        
        token = LToken(
            type=token_type,
            value=value,
            line=self.token_start_line,
            col=self.token_start_col
        )
        self.results.append(token)
        self.buffer = []
        # Reset start marker to current position (approximate, usually caller will mark_start again)
        # 将起始标记重置为当前位置（近似值，通常调用者会再次调用 mark_start）
        self.mark_start()

    def _reset(self):
        super()._reset()
        self.token_start_line = 1
        self.token_start_col = 1
