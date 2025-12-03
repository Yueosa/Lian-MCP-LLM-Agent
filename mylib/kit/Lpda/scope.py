from typing import Any
from dataclasses import dataclass


@dataclass
class ScopeDef:
    """
    Scope Definition
    作用域定义
    
    Describes a type of scope, including its boundaries and metadata.
    描述作用域的类型，包括其边界和元数据。
    """
    name: str
    start_token: str
    end_token: str
    description: str = ""


@dataclass
class ScopeInstance:
    """
    Scope Runtime Instance
    作用域运行时实例
    
    Represents an active scope in the stack.
    表示栈中处于活动状态的作用域。
    """
    definition: ScopeDef
    start_line: int = 0
    start_col: int = 0
    context: Any = None
