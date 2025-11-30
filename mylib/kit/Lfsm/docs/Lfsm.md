# kit Lfsm 状态机文档

> 此文档面向 **模块开发者**，在代码层简述了各文件实现

###### By - Lian 2025 | Updated 2025-11-30

---

## 概述

`Lfsm`（Lian Finite State Machine）是一个通用的有限状态机框架，核心类为 `LStateMachine[S, R]`。它面向“按序读取的流”（字符流/Token 流/对象流），通过“状态枚举 + 动态分发”的方式组织解析逻辑，适用于 Tokenizer、Parser、协议/格式解析、DSL 解释等场景。

---

## 核心类 LStateMachine[S, R]

- 泛型参数：
  - `S`: 状态类型（Enum 派生）
  - `R`: 产出结果类型（如 `Token`、语法节点、自定义对象等）

## 类起源 Generic[S, R]

- 用于声明泛型类，`S` 和 `R` 是两个泛型参数

#### 实例变量（Why & For What）

##### (1) `state: S`

> 一般来说, 需要**子类实现一个状态枚举并继承**

- 状态机所有可切换的状态

##### (2) `buffer: List[str]`

- 状态机应该逐个读取字符，然后添加到 `buffer` 直到满足发出条件

##### (3) `results: List[R]`

- 最终产出的结果，从 `buffer` 中按需获取

##### (4) `context: Dict[str, Any]`

> 有些状态信息和上下文信息只靠 `buffer` 是不够的, 为了让状态机更强大, 设计了 `context` 存储这些信息

- 跨步存放信息

##### (5) `line: int`, `col: int`

- 用于追踪行列信息

#### 实例方法（Why & For What）

##### (1) `switch_state(new_state: S)`

- 用于切换状态

##### (2) `parse(content: Any) -> List[R]`

1. 输入需要解析的文本
2. 提取文本长度并且按字符全遍历
     - 获取值
     - 触发回调函数
     - 自动分发处理 (每一个状态`state`都应该实现对应的`handle_state`方法)
     - 根据自动分发处理的结果决定下一个读取的位置
3. 处理可能残留的 `buffer`
4. 返回 `result`

##### (3) `_on_step(item: Any)`

> 子类可以自由实现, 相当于一个钩子

- 每一步的回调函数, 触发时机是 **提取到值之后** **动态分发之前**

##### (4) `_reset()`

- 重置所有状态

##### (5) `handle_default(char, i, content, n) -> int`

> 默认处理策略, 直接添加字符

- 将内容添加到 `buffer`, 并且返回下一个位置的索引

##### (6) `on_finish()`

> 子类应该重写这个方法, 处理可能残留的 `buffer`

- 提取 `buffer` 中剩余的所有内容

##### (7) `emit(result: R)`

- 将结果添加到 `result`

##### (8) `append_buffer(char: str)` / `flush_buffer() -> str`

- 将一个字符添加进 `buffer`
- 弹出 `buffer` 中所有内容

##### (9) `error(message: str)`

> 子类可选择重写, 提供更多的信息

- 抛出一个错误

---
