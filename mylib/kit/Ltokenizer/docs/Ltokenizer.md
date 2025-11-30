# kit Ltokenizer 词法解析器文档

> 此文档面向 **模块开发者**，在代码层简述了各文件实现

###### By - Lian 2025 | Updated 2025-11-30

---

## 概述

`LTokenizer`（Lian Tokenizer）是一套基于轻量级状态逻辑的词法分析器框架
它通常作为语法分析(paser)之前的第一阶段，用于把原始字符流切分成更高层次的“词”（Token）

---

## 父类 LStateMachine[S, R]

> 详见 [Lfsm.md](../../Lfsm/docs/Lfsm.md)

#### 初始化方法

##### (1) `__init__`

- 添加了两个新的实例变量
    1. `self.token_start_line`: 用于追踪开始行
    2. `self.token_start_col`: 用于追踪开始列

#### 实例方法

##### (1) `_on_step`

> 重写了父类的 `_on_step` 方法

- 对 `str` 类型做出处理:
    - 如果是换行符 `\n`: `line += 1` `col = 1`
    - 否则: `col += 1`

##### (2) `mark_start`

> 直接继承父类的 `self.line` `self.col`

##### (3) `_reset`

> 调用父类的 `_reset`, 并且清空自己的实例变量

##### (4) `emit`

1. 如果没有传入值, 就取当前 `buffer`
2. 将 `buffer` 内容包装为 `token`
3. 将 `token` 添加到 `result`
4. 清空 `buffer`
5. 标记下一轮的起始行列
