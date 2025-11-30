# Lstack 栈结构文档

> 此文档面向 **模块开发者**，在代码层简述了各文件实现

###### By - Lian 2025 | Updated 2025-11-30

---

## 概述

`Lstack` 是一个封装的标准栈结构，提供了严谨的压栈、出栈接口。

它是实现 **下推自动机 (LPDA)** 和 **递归算法** 的基础容器，支持 Python 原生操作符（如 `len()`, `in`, `==`）。

---

## 核心类 Lstack

> 位于 `mylib/kit/Lstack/stack.py`

#### 初始化方法

##### (1) \_\_init\_\_(self, items: List[Any] = None)

> 初始化栈实例

- **items**: 可选的初始列表。如果提供，会创建该列表的副本作为栈的初始内容。

#### 魔术方法

##### (1) \_\_len\_\_(self) -> int

> 支持 `len(stack)`

- 返回 -> 栈中元素的数量 (`self.size()`)

##### (2) \_\_str\_\_(self) -> str

> 支持 `str(stack)` 和 `print(stack)`

- 返回 -> 格式化的字符串，例如 `"栈(3 个元素): [1, 2, 3]"`

##### (3) \_\_repr\_\_(self) -> str

> 支持 `repr(stack)`，用于调试显示

- 返回 -> 例如 `"Lstack<[1, 2, 3]>"`

##### (4) \_\_contains\_\_(self, item: Any) -> bool

> 支持 `in` 操作符

- 检查 -> `item` 是否存在于栈中

##### (5) \_\_eq\_\_(self, other: Union['Lstack', Any]) -> bool

> 支持 `==` 操作符

- 比较 -> 如果 `other` 也是 `Lstack`，比较两者的内部列表是否相等

#### 实例方法

##### (1) push(self, item: Any) -> None

> 压栈操作

- 将元素添加到栈顶（列表末尾）

##### (2) pop(self) -> Any

> 出栈操作

- 移除并返回栈顶元素
- **异常**: 如果栈为空，抛出 `IndexError("栈已经空啦!")`

##### (3) peek(self) -> Any

> 查看栈顶元素

- 返回栈顶元素但不移除
- **异常**: 如果栈为空，抛出 `IndexError("栈已经空啦!")`

##### (4) is_empty(self) -> bool

> 检查栈是否为空

- 返回 -> `True` 如果栈为空，否则 `False`

##### (5) size(self) -> int

> 获取栈的大小

- 返回 -> 栈中元素的数量

##### (6) clear(self) -> None

> 清空栈

- 将内部列表重置为空列表

#### 内部方法

##### (1) _empty_raise(self) -> None

> 栈空检查辅助方法

- 如果 `is_empty()` 为真，则抛出 `IndexError`
