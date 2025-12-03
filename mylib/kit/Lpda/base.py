from typing import Optional, Dict, Any, Type, Generic, Union
from enum import Enum
from mylib.kit.Lfsm.machine import LStateMachine
from mylib.kit.Lstack import Lstack
from .scope import ScopeDef, ScopeInstance
from mylib.kernel.Ltypevar import S, R, P

class LPDA(LStateMachine[S, R], Generic[S, R, P]):
    """
    Lian Pushdown Automaton (LPDA)
    
    继承自 LStateMachine, 增加了栈 (Stack) 支持。
    适用于需要处理嵌套结构 (如括号匹配、作用域管理) 的解析任务。
    """
    
    def __init__(self, initial_state: S, scope_enum: Type[P] = None):
        super().__init__(initial_state)
        self.stack = Lstack()
        self.scope_definitions: Dict[str, ScopeDef] = {}
        self.scope_enum = scope_enum
        
        if scope_enum:
            for member in scope_enum:
                if isinstance(member.value, ScopeDef):
                    # self.scope_definitions[member.name] = member.value
                    self.define_scope(member.name, member.value.start_token, member.value.end_token, member.value.description)

    def _reset(self):
        super()._reset()
        self.stack.clear()

    def define_scope(self, name: str, start_token: str, end_token: str, description: str = ""):
        """定义一个作用域类型"""
        self.scope_definitions[name] = ScopeDef(name, start_token, end_token, description)

    def enter_scope(self, scope: Union[P, str], context: Any = None):
        """进入一个新的作用域 (压栈) """
        scope_name = scope.name if isinstance(scope, Enum) else scope
        
        if scope_name not in self.scope_definitions:
            raise ValueError(f"Undefined scope: {scope_name}")
        
        definition = self.scope_definitions[scope_name]
        instance = ScopeInstance(
            definition=definition,
            start_line=self.line,
            start_col=self.col,
            context=context
        )
        self.stack.push(instance)

    def exit_scope(self, expected_scope: Union[P, str] = None) -> ScopeInstance:
        """
        退出当前作用域 (出栈) 。
        
        :param expected_scope: 如果提供, 会检查弹出的作用域是否匹配。如果不匹配则抛出错误。
        :return: 弹出的作用域实例
        """
        if self.stack.is_empty():
            self.error(f"Unexpected closing of scope. Stack is empty.")
            
        top: ScopeInstance = self.stack.pop()
        
        expected_name = None
        if expected_scope:
            expected_name = expected_scope.name if isinstance(expected_scope, Enum) else expected_scope
        
        if expected_name and top.definition.name != expected_name:
            self.error(f"Mismatched scope: expected to close '{expected_name}', but found '{top.definition.name}'")
            
        return top

    def current_scope(self) -> Optional[ScopeInstance]:
        """获取当前作用域实例 (栈顶) , 如果栈为空返回 None"""
        if self.stack.is_empty():
            return None
        return self.stack.peek()

    def in_scope(self, scope: Union[P, str]) -> bool:
        """检查当前是否在指定的作用域内 (检查栈顶) """
        scope_name = scope.name if isinstance(scope, Enum) else scope
        current = self.current_scope()
        return current is not None and current.definition.name == scope_name
