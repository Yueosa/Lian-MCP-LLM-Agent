from typing import Optional
from mylib.kit.Lfsm.machine import LStateMachine
from mylib.kit.Lstack import Lstack

from .type import S, R

class LPDA(LStateMachine[S, R]):
    """
    Lian Pushdown Automaton (LPDA)
    
    继承自 LStateMachine，增加了栈（Stack）支持。
    适用于需要处理嵌套结构（如括号匹配、作用域管理）的解析任务。
    """
    
    def __init__(self, initial_state: S):
        super().__init__(initial_state)
        self.stack = Lstack()

    def _reset(self):
        super()._reset()
        self.stack.clear()

    def enter_scope(self, scope_name: str):
        """进入一个新的作用域（压栈）"""
        self.stack.push(scope_name)

    def exit_scope(self, expected_scope_name: str = None) -> str:
        """
        退出当前作用域（出栈）。
        
        :param expected_scope_name: 如果提供，会检查弹出的作用域是否匹配。如果不匹配则抛出错误。
        :return: 弹出的作用域名称
        """
        if self.stack.is_empty():
            self.error(f"Unexpected closing of scope. Stack is empty.")
            
        top = self.stack.pop()
        
        if expected_scope_name and top != expected_scope_name:
            self.error(f"Mismatched scope: expected to close '{expected_scope_name}', but found '{top}'")
            
        return top

    def current_scope(self) -> Optional[str]:
        """获取当前作用域名称（栈顶），如果栈为空返回 None"""
        if self.stack.is_empty():
            return None
        return self.stack.peek()

    def in_scope(self, scope_name: str) -> bool:
        """检查当前是否在指定的作用域内（检查栈顶）"""
        return self.current_scope() == scope_name
