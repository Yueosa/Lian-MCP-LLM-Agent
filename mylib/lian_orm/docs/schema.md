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

基于状态机 (FSM) 的 SQL 解析器，用于解析 SQL 文件并生成 `SchemaMeta`。

- **parse_file(file_path)**: 解析 SQL 文件。
- **parse_string(content)**: 解析 SQL 字符串。

---
