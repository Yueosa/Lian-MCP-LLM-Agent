# lian_orm schema 元数据文档

> 此文档面向 **模块开发者**，在代码层简述了各文件实现

###### By - Lian 2025 | Updated 2025-11-28

---

## 概述

`Schema` 模块是 **lian_orm** 的 **元数据中心**，负责将 `postgresql` 结构解析为结构化的 `Python` 对象。

---

## 数据类

#### (1) ColumnMeta

> 列元数据

#### (2) IndexMeta

> 索引元数据

#### (3) TableMeta

> 表元数据

#### (4) ExtensionMeta

> 扩展元数据

#### (5) SchemaMeta

> 库元数据

---

## SqlParser

这个类继承自 `LParserBase`，是一个**基于状态机（FSM）的 SQL 语法分析器**。

它的核心工作是接收 Token 流（由 `SqlTokenizer` 产生），并根据当前状态（`SqlParserState`）进行流转，最终构建出 `SchemaMeta` 对象。

#### (1) 状态定义 `SqlParserState`

解释: 这里定义了解析器的所有可能状态。
- **IDLE**: 初始状态，等待 `CREATE` 关键字。
- **EXPECT_TABLE_\***: 处理 `CREATE TABLE` 语句的各个阶段。
- **EXPECT_INDEX_\***: 处理 `CREATE INDEX` 语句的各个阶段。
- **EXPECT_EXTENSION_\***: 处理 `CREATE EXTENSION` 语句。

#### (2) 