# lian_orm mapper 映射系统文档

> 此文档面向 **模块开发者**，在代码层简述了各文件实现

###### By - Lian 2025 | Updated 2025-11-29

---

## 概述

`Mapper` 模块负责 **Python 对象** 与 **SQL 数据** 之间的类型转换，特别是处理 JSON、Vector 等复杂类型。

---

## 核心组件

### (1) DataConverter

> 位于 `mapper/converter.py`

数据转换器，提供静态方法进行双向转换。

- **python_to_sql(data, table_meta)**: 
    - 将 Python 字典转换为 SQL 兼容的字典。
    - 自动处理 `Enum` -> `value`。
    - 根据 `TableMeta` 自动将 `dict/list` 序列化为 JSON 字符串 (针对 JSON/Vector 列)。
- **sql_to_python(row_dict, table_meta)**:
    - 将 SQL 查询结果转换为 Python 字典。
    - 根据 `TableMeta` 自动将 JSON 字符串反序列化为 `dict/list`。

### (2) SQLTypeMapper

> 位于 `mapper/types.py`

SQL 类型与 Python 类型的映射工具。

- **map_to_python_type(sql_type)**: 将 SQL 类型字符串 (e.g., "VARCHAR", "JSONB") 映射为 Python 类型 (e.g., `str`, `dict`)。
- **is_json_type(sql_type)**: 判断是否为 JSON 类型。
- **is_vector_type(sql_type)**: 判断是否为 Vector 类型。

---
