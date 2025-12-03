# Agent

By Lian - 2025

---

## | 设计哲学

> 自我认知是一切的起点

#### Agent 必须拥有的三样东西

1. 身份 (Identity)

   - 我是谁
   - 我的角色和能力界限是什么

2. 目标 (Objectives)

   - 我此刻正试图完成什么任务
   - 我的工作范围是什么

3. 记忆 (Memory)

   - 我刚做了什么 (短期)
   - 我曾经做过什么 (长期)
   - 我应该怎么做的更好 (元认识)

---

## LLMBaseAgent 基类

> 设计一个基类, 让所有LLM实例都继承于他

#### 类变量

1. 大模型调用相关 (API模式)
    - provider
    - api_key
    - api_url
2. 请求协议 request_schema
3. 响应协议 response_schema

协议可以抽象为独立的类

#### 实例变量

详见 [LLMBaseAgent](./base.py)

#### 实例方法

##### `think`

> 执行一次 LLM 调用, 加入自我认知, 返回结构化结果

1. 将 identity_prompt 注入 system prompt
2. 将 memory 加入 context
3. 发送给模型
4. 按 response_schema 校验
5. 返回

##### `receive`

> 加入短期记忆

```python
def receive(self, message: dict) -> None:
    self.memory.append(message)
```

##### `respond`

```python
def respond(self) -> dict:
    return self.think(user_input=None)
```

#### 系统方法

##### `tool_call`

> MCP 工具调用

```python
def tool_call(self, args: dict) -> Dict:
    pass
```

##### `spawn_agent`

> 生成子代理

```python
def spawn_agent(self, role, desc, goals):
    return Agentmanager.create_agent(...)
```

##### `memory`

> 记忆系统

```python
def save_memory(self, text: str) -> Dict:
def retrieve_memory(self, query: str):
```

##### `log`

> 日志能力

```python
def log(self, event):
    pass
```

#### 权限系统

> 让子类继承不同能力, 清晰职责边界

```python
class LLMBaseAgent:
    capabilities = {
        "spawn": False,
        "tool_call": False,
        "memory_write": False,
    }
```

---

## 自我认知

> 目前打算通过 **实例级prompt** 实现

在每次 `think` 时注入认知:

```text
[
  {"role": "system", "content": "<IDENTITY_PROMPT>"},
  {"role": "system", "content": "<GLOBAL_RULES_OR_SCHEMA>"},
  {"role": "assistant", "content": "<RETRIEVED_SUMMARY_FROM_LONG_TERM_MEMORY>"},
  {"role": "user", "content": "<RECENT_USER_INPUT>"},
  {"role": "user", "content": "<ADDITIONAL_TASK_METADATA_IF_ANY>"}
]
```

#### 伪代码 (构建思路)

```python
def build_identity_prompt(agent):
    # agent.role, agent.description, agent.goals, agent.agent_id
    return (
        f"你是 {agent.role}（ID: {agent.agent_id}）。\n"
        f"自我介绍：{agent.description}\n"
        f"当前目标：{', '.join(agent.goals)}\n"
        "行为约束：\n"
        "- 只在你的权限范围内行动；\n"
        "- 若需要调用外部工具，请以 request_tool 格式返回；\n"
        "- 输出必须符合 response_schema。\n"
    )

def build_messages(agent, user_input, retrieved_memory_summary=None, recent_msgs=None):
    messages = []
    # 1. 固定身份（system）
    messages.append({"role": "system", "content": build_identity_prompt(agent)})

    # 2. 添加全局行为规范 / 输出 schema（可选但强烈建议）
    messages.append({
        "role": "system",
        "content": "输出须为 JSON，符合 AgentResponse schema: {agent_id, message, proposed_action, metadata}。"
    })

    # 3. 注入检索到的长期记忆摘要（简短）
    if retrieved_memory_summary:
        messages.append({"role": "assistant", "content": f"相关记忆摘要：{retrieved_memory_summary}"})

    # 4. 最近对话（短期记忆）
    if recent_msgs:
        for m in recent_msgs:
            messages.append(m)   # m 为 {"role":"user"/"assistant","content":...}

    # 5. 当前用户输入
    messages.append({"role": "user", "content": user_input})

    return messages

def call_llm_api(messages):
    payload = {"messages": messages, "max_tokens": 800}
    # 伪函数，替换为你实际的 HTTP 调用
    return remote_chat_api_call(payload)

# 使用示例（放在 LLMBaseAgent.think 中）
retrieved_summary = vector_db.search_and_summarize(agent.goals, top_k=5)
recent = agent.memory[-6:]   # 保留最近 6 条短期记忆
messages = build_messages(agent, "请实现一个分页的 SQL 查询模块", retrieved_summary, recent)
resp = call_llm_api(messages)
```

#### 长期记忆的注入与检索策略

#### 防止 token 爆炸 (目前调用模型的上限大概是 `131072 tokens`)

#### 自我认知写法

#### 工程细节

#### Tips

