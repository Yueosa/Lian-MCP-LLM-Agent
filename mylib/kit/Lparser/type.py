from enum import Enum
from typing import TypeVar


S = TypeVar('S', bound=Enum)
R = TypeVar('R') # Result type (e.g. AST node, or SchemaMeta)
P = TypeVar('P', bound=Enum)
