from typing import List, Any, Union


class Lstack:
    def __init__(self, items: List[Any] = None):
        self.items = items.copy() if items else []

    def __len__(self) -> int:
        """支持 len()"""
        return self.size()  
    
    def __str__(self) -> List[Any]:
        """支持 str()"""
        return f"栈({len(self.items)} 个元素): {self.items}"
    
    def __repr__(self):
        """支持 repr()"""
        return f"Lstack<{self.items}>"
    
    def __contains__(self, item: Any) -> bool:
        """支持 in 操作符"""
        return item in self.items
    
    def __eq__(self, other: Union['Lstack', Any]):
        """支持 == 操作符"""
        if isinstance(other, Lstack):
            return self.items == other.items
        return False

    def _empty_raise(self) -> None:
        """如果栈为空就抛出错误"""
        if self.is_empty():
            raise IndexError("栈已经空啦!")

    def push(self, item: Any) -> None:
        """压栈"""
        self.items.append(item)

    def pop(self) -> Any:
        """出栈"""
        self._empty_raise()
        return self.items.pop()
    
    def peek(self) -> Any:
        """查看栈顶"""
        self._empty_raise()
        return self.items[-1]
    
    def is_empty(self):
        """检查是否为空"""
        return len(self.items) == 0
    
    def size(self) -> int:
        """返回栈深度"""
        return len(self.items)
    
    def clear(self) -> None:
        """清空栈"""
        self.items = []
