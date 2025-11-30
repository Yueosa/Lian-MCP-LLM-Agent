from enum import Enum
from typing import TypeVar


S = TypeVar("S", bound=Enum)    # State Enum Type
R = TypeVar("R")    # Result Type
