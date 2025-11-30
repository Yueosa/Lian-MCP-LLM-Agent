# kit Lpda 状态机文档

> 此文档面向 **模块开发者**，在代码层简述了各文件实现

###### By - Lian 2025 | Updated 2025-11-30

---

## 概述

`Lpda`（Lian Pushdown Automaton）是在 `Lfsm` 状态机框架基础上扩展的带栈的有限状态机
它继承自 `LStateMachine[S, R]`，并额外引入一个可控的栈结构 (实现了**作用域**概念)，用于追踪解析过程中的“嵌套”与“层级关系”。

---

## 父类 `LStateMachine[S, R]`

> 详情见 [Lfsm.md](../../Lfsm/docs/Lfsm.md)

## 栈 `Lstack`

> 详情见 [Lstack.md](../../Lstack/docs/Lstack.md)

#### 初始化方法

##### (1) `__init__`

- 在初始化时额外初始化一个 `Lstack`

#### 实例方法

##### (1) `_reset`

- 清空栈
- 重置状态机

##### (2) `enter_scope`

- 压栈

##### (5) `exit_scope`

1. 检查栈是否为空
2. 弹出栈顶, 并检查作用域是否正确

##### (6) `current_scope`

- 获取当前作用域名称

##### (7) `in_scope`

- 查看当前是否在指定作用域内

---
