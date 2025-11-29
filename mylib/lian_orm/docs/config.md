# lian_orm config 配置文档

> 此文档面向 **模块开发者**，在代码层简述了各文件实现

###### By - Lian 2025 | Updated 2025-11-29

---

## 概述

`Config` 模块负责加载和管理 ORM 的配置信息，如数据库连接参数。

---

## 核心组件

### (1) ConfigLoader

> 位于 `mylib/config/loader.py`

配置加载器，支持从 TOML 文件加载配置。

- **默认路径**: `mylib/lian_orm/config/sql_config.toml`
- **属性访问**: 支持通过点号访问配置项 (e.g., `cfg.Postgresql.host`)。

### (2) 配置文件格式

`TOML`
```toml
[Postgresql]
host = "localhost"
port = 5432
dbname = "mydb"
user = "user"
password = "password"
```
`JSON`
```json
{
    "Postgresql": {
        "host": "localhost",
        "port": 5432,
        "dbname": "mydb",
        "user": "user",
        "password": "password"
    }
}
```

---
