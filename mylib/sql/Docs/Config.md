# sql config 说明文档

###### By - Lian 2025

---

##### sql 模块的配置文件默认位置为 `sql/config/sql_config.toml`

> 也可以在实例化 `Sql()` 的时候传入参数 `config_path` 来指定路径

#### 以下是最小示例:

**`TOML`**

```toml
[Postgresql]
host = "your server ip"
port = 5432
dbname = "your db name"
user = "your db user"
password = "your db user passwd"
```

**`JSON`**

```json
{
  "Postgresql": {
    "host": "your server ip",
    "port": 5432,
    "dbname": "your db name",
    "user": "your db user",
    "password": "your db user passwd"
  }
}
```

#### 访问示例

> 基于 `ConfigLoader` 实现, [点击跳转 ConfigLoader 文档](../../config/docs/UserGuide.md)

```python
from config import ConfigLoader

cfg = ConfigLoader()

# 访问示例
host: str = cfg.Postgresql.host
```

---
