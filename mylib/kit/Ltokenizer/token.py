from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    """
    Base Token Types.
    基本 Token 类型
    Specific implementations (like SqlTokenType) should inherit or extend this concept.
    具体的实现 (例如SqlTokenType) 应该继承或实现这个概念
    However, Enum inheritance is tricky in Python. 
    然而, 枚举在 Python 中的继承比较复杂
    Usually, we just define a new Enum in the concrete implementation 
    通常, 我们会在具体的实现中定义一个新的枚举
    and use that.
    并使用它
    """
    UNKNOWN = auto()
    EOF = auto()


@dataclass
class LToken:
    type: Enum
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"LToken({self.type.name}, '{self.value}', {self.line}:{self.col})"
