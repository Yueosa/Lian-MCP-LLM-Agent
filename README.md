# Lian-MCP-LLM Agent 系统设计思路

By - Lian - 2025

---

## 初步构想

使用多专家 (多个 llm) 解决问题 (将 llm 封装为类, 每一个 llm session 作为一个实例管理)

使用 **`pydantic` 模型** 管理专家组, 单个专家的参数

## 可实现的核心功能

1. **使用 llm 完成代码创建, 修改任务 (练手使用)**

    - 关键点: 使用任务流专家管理流程, 代码专家生成代码, 调用 mcp 执行文件写入

2. **[废弃: 不是我热爱的东西]** 使用 llm 自动整理表单 (导师指点)

    - 关键点: 使用任务流专家管理流程, 阅读专家分析文件内容, 整理专家操作移动文件

3. **[废弃: 不是我热爱的东西]** llm 自动渗透测试 (导师指点)

    - 关键点: 使用任务流专家管理流程, 渗透专家调用工具, 分析结果

4. **接入 `YosaCat`**

---

## 项目进度

#### | 数据库 --coding--

使用 `psql`, 基本封装已完成 (等待注释与文档)

##### 功能测试 `uv run python -m mylib.sql.example_usage`

##### 测试连接 `uv run python ./tests/sql_connect.test.py`

文档 [sql.md](mylib/sql/docs/sql.md) (点击跳转)

> 已完成封装, 暴露接口, 正在实现`Python`端外键模式

#### | mcp 包 --pedding--

完成了基本的**mcp 服务器**和**llm 客户端**功能 (纯屎山)

测试 `Server`: `uv run python ./main.py server`

测试 `Client`: `uv run python ./main.py client`

##### 目前 mcp 库集成了 mcp_server 与 llm_client 的功能, 后续需要分离:

-   mcp: 负责 mcp_tools 的实现, 元数据提取, 并且与本地知识库进行联动

-   llm: 负责 llm_chat 的创建, 生命周期管理

#### | Config 包 --done--

用于配置加载, 已经完备

测试: `uv run python ./tests/config.test.py`

文档 [UserGuide.md](mylib/config/docs/UserGuide.md) (点击跳转)

#### | utils 包

###### 目前实现的包

##### Printer --done--

提供了一个彩色打印方法

##### Loutput --done--

基于 `Printer` 完全重构, 目前已经支持:

-   基于 ANSI 的文字效果, 文字色彩, 背景色彩显示
-   支持 256 色, rgb 24bit 色彩

测试: `uv run python ,/tests/Loutput.test.py`

文档 [Loutput.md](mylib/utils/Loutput/docs/Loutput.md) (点击跳转)

---

## 🎓 学术使用声明

**本项目为 2025 届毕业设计作品**

⚠️ **重要提醒**：

-   保护期：2025 年 11 月 10 日 - 2026 年 1 月 19 日
-   在此期间，禁止同校同学使用本项目进行毕业设计
-   禁止任何形式的学术作业提交
-   详细条款请参阅 LICENSE 文件

---

## 开发之外

记得抽空去读一读 **任务书** 和 **毕业设计报告模板** ! 还要记得 **读论文** !
