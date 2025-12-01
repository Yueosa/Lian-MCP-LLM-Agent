# lian_orm schema 元数据文档

> 此文档面向 **模块开发者**，在代码层简述了各文件实现

###### By - Lian 2025 | Updated 2025-11-29

---

## 概述

`Schema` 模块是 **lian_orm** 的 **元数据中心**，负责将 `postgresql` 结构解析为结构化的 `Python` 对象。

---

## 核心组件

### (1) SchemaManager

> 位于 `schema/manager.py`

Schema 管理器，提供对 Schema 元数据的统一访问接口。

- **load_from_file(file_path)**: 从本地 SQL 文件加载 Schema。
- **get_table(table_name)**: 获取指定表的元数据 (`TableMeta`)。
- **all_tables**: 获取所有已加载的表名列表。

### (2) Metadata

> 位于 `schema/metadata/metadata.py`

定义了描述数据库结构的 Dataclass。

- **ColumnMeta**: 列元数据 (name, data_type, is_primary_key, is_nullable, default, references, constraints, description)
- **IndexMeta**: 索引元数据 (name, table_name, columns, method, unique, definition)
- **TableMeta**: 表元数据 (name, columns, indices, primary_key, comment)
- **SchemaMeta**: 完整 Schema 元数据 (tables, extensions)

### (3) SqlParser

> 位于 `schema/localfile/parser.py`

基于状态机 (FSM) 的 SQL 解析器，用于解析 SQL 文件的 Token 序列并生成 `SchemaMeta`。

- **parse_file(file_path)**: 解析 SQL 文件。
- **parse_string(content)**: 解析 SQL 字符串。

### (4) SqlTokenizer

> 位于 `schema/localfile/tokenizer.py`

- **parse**: 解析 `SQL` 流 为 `Token` 序列

`SqlTokenizer` 是一个基于**有限状态机 (FSM)** 的词法分析器。它继承自 `LTokenizerBase`，而 `LTokenizerBase` 又继承自 `LStateMachine`。

它的核心工作原理是：逐字符读取输入流，根据当前状态 (state) 和当前字符 (char) 决定下一步动作（切换状态、累积字符或发射 Token）。

#### 1. 解析流程深度解析
整个解析过程由基类 `LStateMachine.parse()` 驱动，它是一个 while 循环，不断调用 `handle_{state_name}` 方法。

以下是 SqlTokenizer 各个状态的具体解析逻辑：

##### (1) 初始状态 IDLE
默认状态，负责分发任务。
- **空白**: 跳过。
- **注释**: 遇到 `--` 切换至 `IN_COMMENT_LINE`；遇到 `/*` 切换至 `IN_COMMENT_BLOCK`。
- **字符串**: 遇到 `'` 切换至 `IN_STRING_SINGLE`；遇到 `$` 切换至 `IN_STRING_DOLLAR`。
- **引用标识符**: 遇到 `"` 切换至 `IN_QUOTED_IDENTIFIER`。
- **符号**: 遇到 `(`, `)`, `,`, `;` 等，直接发射 `SYMBOL` Token。
- **其他**: 视为标识符开始，切换至 `IDENTIFIER` 并开始收集字符。

##### (2) 标识符状态 IDENTIFIER
负责收集连续的字母、数字或下划线。
- **分隔符检测**: 遇到空格、符号、引号等分隔符时，调用 `_emit_identifier` 发射 Token，并切换回 `IDLE` 重新处理该分隔符。
- **收集**: 其他情况继续将字符追加到缓冲区。

##### (3) 字符串与引用状态
包含 `IN_STRING_SINGLE` (单引号), `IN_STRING_DOLLAR` ($$标签), `IN_QUOTED_IDENTIFIER` (双引号)。
- **收集**: 持续收集字符内容。
- **转义**: 处理 SQL 标准转义（如 `''` 转义为 `'`，`""` 转义为 `"`）。
- **结束**: 遇到闭合符号时，发射对应类型的 Token (`STRING` 或 `IDENTIFIER`) 并切回 `IDLE`。注意：Token 值不包含外层引号。

##### (4) 注释状态
包含 `IN_COMMENT_LINE` (单行) 和 `IN_COMMENT_BLOCK` (块级)。
- **忽略**: 持续读取直到遇到结束符（换行符或 `*/`），期间不产生任何 Token。

#### 2. 关键实例方法

##### _emit_identifier()
**职责**: 消除歧义，区分关键字与普通标识符。
- 当一个标识符收集完成时调用。
- 检查缓冲区内容是否在预定义的 `KEYWORDS` 集合中（如 `CREATE`, `TABLE`）。
- 如果是关键字，发射 `KEYWORD` Token；否则发射 `IDENTIFIER` Token。

##### on_finish()
**职责**: 处理流结束时的收尾工作。
- **收尾**: 如果处于 `IDENTIFIER` 状态，强制发射缓冲区中的最后一个 Token。
- **校验**: 如果处于字符串、引用或块注释状态，说明结构未闭合，抛出 `ValueError` 异常。

---
