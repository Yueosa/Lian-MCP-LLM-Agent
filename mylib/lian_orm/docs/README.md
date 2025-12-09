# package sql 数据库

###### By - Lian 2025

---

## | 技术栈

使用 `Postgresql` 作为数据库, 主要用于存储对话记录, 工具调用, 任务流程等信息

| pgsql 语法               | 说明           |
| ------------------------ | -------------- |
| `psql -U username -d db` | 进入数据库     |
| `psql -U username`       | 进入 `psql`    |
| `\l`                     | 查看所有数据库 |
| `\c db`                  | 切换数据库     |
| `\dt`                    | 查看所有表     |
| `\d name`                | 查看表结构     |
| `\di`                    | 查看索引       |
| `\dx`                    | 查看拓展       |

## | 表结构

> 这里主要说明所有数据库表的结构设计信息

#### 日志表 memory_log

| 字段名        | 数据类型                                 | 说明                                                              |
| ------------- | ---------------------------------------- | ----------------------------------------------------------------- |
| `id`          | **_SERIAl PRIMARY KEY_**                 | 自增主键, 唯一标识每条记录                                        |
| `user_id`     | **_VARCHAR(64) DEFAULT 'default'_**      | 用户 ID, 支持多用户                                               |
| `role`        | **_VARCHAR(16) NOT NULL_**               | 角色类型: user / assistant / system                               |
| `content`     | **_TEXT NOT NULL_**                      | 文本内容                                                          |
| `embedding`   | **_VECTOR(1536)_**                       | 文本向量表示(1536 维), 用于相似性检索                             |
| `memory_type` | **_VARCHAR(32) DEFAULT 'conversation'_** | 记忆类型: conversation / summary / reflection / preference / plan |
| `importance`  | **_FLOAT DEFAULT 0_**                    | 重要性评分(由 LLM 评估)                                           |
| `created_at`  | **_TIMESTAMP DEFAULT NOW()_**            | 创建时间戳                                                        |

#### 任务表 tasks

| 字段名        | 数据类型                            | 说明                                        |
| ------------- | ----------------------------------- | ------------------------------------------- |
| `id`          | **_SERIAl PRIMARY KEY_**            | 自增主键, 标识每一条记录                    |
| `user_id`     | **_VARCHAR(64) DEFAULT 'default'_** | 用户 ID, 支持多用户                         |
| `title`       | **_TEXT_**                          | 任务标题(由 LLM 自动生成)                   |
| `description` | **_TEXT_**                          | 任务详细描述(由任务规划器生成)              |
| `status`      | **_VARCHAR(32) DEFAULT 'pending'_** | 任务状态: pending / running / done / failed |
| `created_at`  | **_TIMESTAMP DEFAULT NOW()_**       | 任务创建时间                                |
| `updated_at`  | **_TIMESTAMP DEFAULT NOW()_**       | 任务最后更新时间                            |

#### 任务步骤表 task_steps

| 字段名        | 数据类型                            | 说明                                        |
| ------------- | ----------------------------------- | ------------------------------------------- |
| `id`          | **_SERIAl PRIMARY KEY_**            | 自增主键, 标识每一条记录                    |
| `task_id`     | **_INTEGER REFERENCES tasks(id)_**  | 外键, 关联到父任务(级联删除)                |
| `step_index`  | **_INTEGER NOT NULL_**              | 步骤序号(表示执行顺序)                      |
| `instruction` | **_TEXTv NOT NULL_**                | 执行指令(由任务规划期生成)                  |
| `output`      | **_TEXT_**                          | 执行结果(由执行器返回)                      |
| `status`      | **_VARCHAR(32) DEFAULT 'pending'_** | 步骤状态: pending / running / done / failed |
| `created_at`  | **_TIMESTAMP DEFAULT NOW()_**       | 步骤创建时间                                |
| `updated_at`  | **_TIMESTAMP DEFAULT NOW()_**       | 步骤最后更新时间                            |

#### 工具调用表 tool_calls

| 字段名       | 数据类型                                | 说明                           |
| ------------ | --------------------------------------- | ------------------------------ |
| `id`         | **_SERIAl PRIMARY KEY_**                | 自增主键, 标识每一条记录       |
| `task_id`    | **_INTEGER REFERENCES tasks(id)_**      | 外键，关联到父任务(置空删除)   |
| `step_id`    | **_INTEGER REFERENCES task_steps(id)_** | 外键，关联到具体步骤(置空删除) |
| `tool_name`  | **_VARCHAR(128) NOT NULL_**             | 工具名称                       |
| `arguments`  | **_JSONB_**                             | 调用参数(JSON 格式)            |
| `response`   | **_JSONB_**                             | 工具返回结果(JSON 格式)        |
| `status`     | **_VARCHAR(32) DEFAULT 'success'_**     | 调用状态: success / failed     |
| `created_at` | **_TIMESTAMP DEFAULT NOW()_**           | 调用创建时间                   |

---

## | PostgreSQL + pgvector 安装部署

> 本节详细讲解了 psql 数据库的安装与配置

#### (1) 配置软件源

```shell
# 添加清华源
echo "deb https://mirrors.tuna.tsinghua.edu.cn/postgresql/repos/apt/ noble-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list

# 导入GPG密钥
wget -qO - https://mirrors.tuna.tsinghua.edu.cn/postgresql/repos/apt/ACCC4CF8.asc | sudo apt-key add -
```

#### (2) 安装 PostgreSQL 和 pgvector

```shell
# 更新包列表并安装
sudo apt update && sudo apt install postgresql-16 postgresql-client-16 postgresql-16-pgvector

# 启动PostgreSQL服务并设置开机自启
sudo systemctl enable postgresql && sudo systemctl start postgresql
```

#### (3) 数据库用户和权限配置

```shell
# 切换到postgres系统用户
sudo -i -u postgres

# 进入PostgreSQL交互终端
psql
```

```sql
-- 创建超级用户 sakurine
CREATE ROLE sakurine WITH LOGIN SUPERUSER PASSWORD 'passwd';

-- 创建业务数据库 lml_sql，所有者为 sakurine
CREATE DATABASE lml_sql OWNER sakurine;

-- 创建普通用户 lml_sql_admin
CREATE ROLE lml_sql_admin WITH LOGIN PASSWORD 'passwd';

-- 授予 lml_sql_admin 对数据库的基本操作权限
GRANT ALL PRIVILEGES ON DATABASE lml_sql TO lml_sql_admin;

-- 连接到业务数据库
\c lml_sql

-- 授予 lml_sql_admin 对 public 模式的完全权限
GRANT ALL ON SCHEMA public TO lml_sql_admin;

-- 授予 lml_sql_admin 对所有现有表的增删改查权限
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lml_sql_admin;

-- 设置默认权限：以后新建的表也自动继承权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lml_sql_admin;

-- 授予 lml_sql_admin 对所有现有序列的使用和更新权限
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO lml_sql_admin;

-- 设置默认权限：以后新建的序列也自动继承权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO lml_sql_admin;

-- 退出psql
\q
```

```shell
exit
```

#### (4) 配置认证方式

```shell
# 编辑客户端认证配置文件
sudo vim /etc/postgresql/16/main/pg_hba.conf
```

```text
# 修改前：
local   all             all                                     peer
host    all             all             127.0.0.1/32            ident
host    all             all             ::1/128                 ident

# 修改后：
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
```

#### (5) 导入 SQL 架构文件

```shell
# 使用sakurine用户导入SQL文件
psql -U sakurine -d lml_sql -f /root/sql/LML_SQL.sql
```

> [SQL 架构文件 (LML_SQL.sql)](../schema/localfile/LML_SQL.sql) (点击跳转)

#### (6) 配置远程访问

```shell
# 编辑PostgreSQL主配置文件
sudo vim /etc/postgresql/16/main/postgresql.conf
```

```text
# 修改前：
#listen_addresses = 'localhost'

# 修改后：
listen_addresses = '*'
```

```shell
# 编辑认证配置文件，添加远程访问规则
sudo vim /etc/postgresql/16/main/pg_hba.conf
```

```text
host    all             all             0.0.0.0/0               md5
```

#### (7) 重启服务

```shell
# 重启PostgreSQL服务
sudo systemctl restart postgresql
```

#### (8) 使用 Python 验证

```shell
# 使用 uv 项目管理工具
uv add psycopg2-binary

# 兼容pip
echo "psycopg2-binary==2.9.11" >> requirements.txt
```

```python
import psycopg2
from mylib import ConfigLoader

def get_all_tables():
    cfg = ConfigLoader()
    conn = psycopg2.connect(
        host=cfg.Postgresql.host,
        port=cfg.Postgresql.port,
        dbname=cfg.Postgresql.dbname,
        user=cfg.Postgresql.user,
        password=cfg.Postgresql.password
    )

    cursor = conn.cursor()

    cursor.execute("""
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY tablename;
    """)

    tables = cursor.fetchall()

    print("\n\033[36m 数据库中的表: \033[0m")
    for table in tables:
        print(f"  - {table[0]}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    get_all_tables()

```

```shell
  ⚡a3197 ❯❯ uv run python -m mylib.sql.sql_test
找到 1 个配置文件: ['sql_config.toml']
  📦 发现配置节: Postgresql
✅ 成功加载配置文件: sql_config.toml

 数据库中的表:
  - memory_log
  - task_steps
  - tasks
  - tool_calls
```
