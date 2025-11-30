# kit LParserBase 语法解析器文档

> 此文档面向 **模块开发者**，在代码层简述了各文件实现

###### By - Lian 2025 | Updated 2025-11-30

---

## 概述

`LParserBase` 是一个抽象语法解析器基类，构建在 `LPDA` 之上，用于处理由 `LTokenizer` 生成的 `LToken` 列表。

---

## 父类 `LPDA[S, R]`

> 详情见 [Lpda.md](../../Lpda/docs/Lpda.md)

#### 初始化方法

##### (1) `__init__`

- 添加了一个新的实例变量
    1. `self.current_token`: 用于追踪正在处理的 `LToken`

#### 实例方法

##### (1) `_on_step`

> 重写父类的 `_on_step` 方法

- 如果类型是 `LToken`:
    1. 更新 `self.current_token`
    2. 更新行列

##### (2) `error`

- 抛出一个错误
