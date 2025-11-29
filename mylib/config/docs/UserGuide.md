# ConfigLoader 用户文档 📚

欢迎来到 **ConfigLoader** 用户指南！

## 🌸 简介

**ConfigLoader** 是一个智能配置管理工具，它能够：

-   ✨ **自动发现** : 自动加载配置文件以及所有配置节
-   🎯 **灵活访问** : 支持 **Python** `dict` 和 `list` 的多种原生访问方法
-   🌍 **全局单例** : 一次初始化就可以全局使用

> **哇～ ConfigLoader 会自动帮你发现配置文件喵！** 😊
>
> 每个配置节都会变成可爱的属性，比如 `config.database.host`～

---

## 🚀 快速开始

### 最简单的用法

假设你有一个这样的配置文件 `toml`

```toml
[database]
host = "0.0.0.0"

[server]
port = 8080
```

使用 `ConfigLoader` 加载他

```python
from config import ConfigLoader

# 初始化配置加载器
config = ConfigLoader()

# 访问你的配置节
print(config.database.host)     # 输出 "0.0.0.0"
print(config.server.port)       # 输出 8080

# 查看配置摘要
config.show_config()
```

**`ConfigLoader`** 参数:

-   **config_path** \<str>: 文件路径/目录路径
-   **search_subdirs** \<bool>: 是否递归扫描, 默认为 `False`
-   **ignore_files** \<Set[str]>: 黑名单文件, 默认为 `{'pyproject.toml', '*.example.toml'}`

> 这就是全部！🎉 配置加载器会自动在你的脚本目录扫描 `*.toml` 和 `*.json` 文件。

---

## 🔧 初始化方式

### 方式 1️⃣：直接实例化

#### 自动发现模式

最简单的方式，自动扫描脚本所在目录 (ConfigLoader实例化发生的位置) 的所有配置文件：

```python
from config import ConfigLoader

# 自动扫描当前脚本目录的所有 *.toml 和 *.json 文件
config = ConfigLoader()
```

这会在脚本所在目录搜索所有 `*.toml` 和 `*.json` 文件，加载所有配置节。

#### 单文件模式

直接指定一个配置文件，只加载该文件中的配置：

```python
from config import ConfigLoader

# 相对路径方式（相对于脚本位置）
config = ConfigLoader(config_path="./config.toml")

# 绝对路径方式
config = ConfigLoader(config_path="etc/myapp/config.test.toml")
```

#### 目录模式

指定一个目录，自动扫描该目录中的所有配置文件：

```python
from config import ConfigLoader

# 相对路径
config = ConfigLoader(config_path="./config")

# 绝对路径
config = ConfigLoader(config_path="/etc/myapp/config")
```

#### 过滤不需要的文件

使用 `ignore_files` 排除特定的配置文件：

```python
config = ConfigLoader(
    ignore_files={
        'pyproject.toml',      # 忽略项目元数据
        '*.example.toml',      # 忽略所有示例文件
        'test_*.toml',         # 忽略测试配置
        'deprecated.toml'      # 忽略已弃用配置
    }
)
```

**模式匹配规则：**

-   精确匹配：`pyproject.toml` → 只忽略此文件
-   通配符模式：`*.example.toml` → 忽略所有 `.example.toml` 文件
-   前缀匹配：`test_*.toml` → 忽略所有以 `test_` 开头的 toml 文件

### 方式 2️⃣：全局单例模式

当你使用**单个配置文件**, 但是配置内容需要**多个模块共享**的时候, 建议你使用全局单例模式喵

```python
# 在应用启动时初始化一次
from config import ConfigLoader

ConfigLoader.init_global(config_path="./config")

# 在任何其他模块中获取
from config import ConfigLoader

config = ConfigLoader.get_global()
print(config.database.host)
```

**全局模式的优势：**

-   🌍 一次初始化，全局可用
-   📍 不用重复传递配置对象
-   🎯 避免重复加载配置

**什么时候使用全局模式：**

-   ✅ 多个模块都需要访问配置
-   ✅ 大型项目中的中央配置管理
-   ✅ 无需频繁重新加载配置

---

## 🔍 配置节自动发现

`ConfigLoader` 使用智能扫描机制来发现和加载你的配置：

#### 同时兼容 TOML / JSON

**TOML 格式** - 推荐方式 👍

```toml
# database.toml
[database]
host = "localhost"
port = 5432
user = "admin"
password = "secret"

[cache]
enable = true
ttl = 3600
```

**JSON 格式** - 替代方案

```json
{
	"database": {
		"host": "localhost",
		"port": 5432,
		"user": "admin",
		"password": "secret"
	},
	"cache": {
		"enable": true,
		"ttl": 3600
	}
}
```

---

## 📖 配置访问方式

一旦加载完成，你有多种灵活的方式来访问配置。

### 1️⃣ 链式访问（推荐 ⭐）

最优雅的方式：

```python
config = ConfigLoader()

# 直接链式访问
print(config.database.host)
print(config.database.port)
print(config.server.debug)

# 支持任意深度
print(config.section.subsection.key)
```

### 2️⃣ 字典式访问

支持下标访问和列表访问

```python
# 下标访问
print(config["database"]["host"])

# 列表访问与混合访问
servers = config.servers
print(servers[0].host)
print(servers[1]["port"])
```

### 3️⃣ get() 支持默认值

安全的访问方式，避免 KeyError：

```python
# 使用 get() 方法（类似字典）
host = config.database.get("host", "localhost")
port = config.database.get("port", 5432)
timeout = config.database.get("timeout", 30)

# 深层链式 get
value = config.server.get("max_connections", 100)
```

### 4️⃣ 迭代配置节

遍历配置中的所有项：

```python
# 迭代字典类型的配置
config = ConfigLoader()

for key, value in config.database.items():
    print(f"{key}: {value}")
```

**常用迭代方法：**

```python
# 获取所有键
for key in config.database.keys():
    print(key)

# 获取所有值
for value in config.database.values():
    print(value)

# 获取键值对
for key, value in config.database.items():
    print(f"{key} = {value}")
```

### 5️⃣ 列表访问

配置中包含列表结构也能自然处理：

```toml
# servers.toml
[[servers]]
host = "server1.com"
port = 8080

[[servers]]
host = "server2.com"
port = 8080
```

```python
config = ConfigLoader()

# 访问列表元素
print(config.servers[0].host)  # "server1.com"
print(config.servers[1].port)  # 8080

# 迭代列表
for server in config.servers:
    print(server.host, server.port)
```

### 6️⃣ 转为原始 dict

需要原始的 Python 字典？使用 `to_dict()` 或 `raw` 属性：

```python
# 方法 1：to_dict()
raw1 = config.database.to_dict()
print(type(raw1))  # dict

# 方法 2：raw 属性
raw2 = config.database.raw
print(type(raw2))  # dict

# 可用于 JSON 序列化等场景
import json
json_str = json.dumps(config.database.to_dict())
```

---

## 🔐 查看配置来源

了解你的配置从何而来是很重要的。

### 方式 1️⃣：完整摘要

```python
cfg = ConfigLoader()
cfg.show_config()
```

**输出示例：**

```
🔍 找到 1 个配置文件: ['config.test.toml']

✅ 配置文件加载完成: E:\YeaSakura\CodeLixir\LML\lml\config.test.toml
  📦 发现配置节: database
  📦 发现配置节: redis
  📦 发现配置节: app
  📦 发现配置节: test

🔧 ConfigLoader 配置摘要
📁 搜索路径: E:\YeaSakura\CodeLixir\LML\lml

🔍 自动发现配置节:
   ✅ database
      ← 来源: toml:E:\YeaSakura\CodeLixir\LML\lml\config.test.toml
   ✅ redis
      ← 来源: toml:E:\YeaSakura\CodeLixir\LML\lml\config.test.toml
   ✅ app
      ← 来源: toml:E:\YeaSakura\CodeLixir\LML\lml\config.test.toml
   ✅ test
      ← 来源: toml:E:\YeaSakura\CodeLixir\LML\lml\config.test.toml

📋 配置节详情:
   🗂️  database:
      host: localhost
      port: 5432
      credentials: {'username': 'admin', 'password': 'secret'}
   🗂️  redis:
      host: 127.0.0.1
      port: 6379
      cluster_nodes: ['node1:7000', 'node2:7001', 'node3:7002']
   🗂️  app:
      debug: True
      log_level: INFO
      features: ['auth', 'cache', 'api']
   🗂️  test:
      Test: 200

📄 加载的配置文件:
   ✅ E:\YeaSakura\CodeLixir\LML\lml\config.test.toml

💡 使用示例:
   # 访问配置:
   config.database.host
   config.database.get('host')
   config.database.to_dict()
```

### 方式 2️⃣：简化摘要

不需要那么多细节？使用 `simple=True`：

```python
config.show_config(simple=True)
```

**输出示例：**

```
📋 配置摘要:
搜索路径: E:\YeaSakura\CodeLixir\LML\lml
发现 4 个配置节:
  - database
  - redis
  - app
  - test
加载 1 个文件
```

---

**祝你使用愉快！** 🎉
