from typing import TypeVar
from enum import Enum

# ============================
#  表示任何从 Enum 继承而来的类型
# ============================
S = TypeVar('S', bound=Enum)

# ============
#  表示一个结果
# ============
R = TypeVar('R') 

# =================
#  表示一个作用域类型
# =================
P = TypeVar('P', bound=Enum)