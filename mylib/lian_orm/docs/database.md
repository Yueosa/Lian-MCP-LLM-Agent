# lian_orm database 数据库层文档

> 此文档面向 **模块开发者**，在代码层简述了各文件实现

###### By - Lian 2025 | Updated 2025-11-29

---

## 概述

`Database` 模块封装了底层的数据库连接和执行逻辑，基于 `psycopg2`。

---

## 核心组件

### (1) PostgreSQLConnectionPool

> 位于 `database/pool.py`

基于 `psycopg2.pool.ThreadedConnectionPool` 的连接池封装。

- **get_connection()**: 获取连接。
- **release_connection(conn)**: 释放连接。
- **clear_connections()**: 关闭所有连接。

### (2) DatabaseClient

> 位于 `database/client.py`

数据库操作客户端，提供高层执行接口。

- **execute(sql, params)**: 执行写操作 (INSERT, UPDATE, DELETE)，返回受影响行数。
- **execute_returning(sql, params)**: 执行带 RETURNING 的写操作，返回结果。
- **fetch_all(sql, params)**: 执行读操作，返回字典列表。
- **fetch_one(sql, params)**: 执行读操作，返回单个字典。
- **上下文管理**: 自动处理 Cursor 的获取、提交、回滚和释放。

---
