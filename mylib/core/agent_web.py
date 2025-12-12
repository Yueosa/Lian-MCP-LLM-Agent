import streamlit as st
import asyncio
from typing import List, Dict, Any

from mylib.agent.rag_agent import RAGAgent
from mylib.agent.planner_agent import PlannerAgent
from mylib.agent.executor_agent import ExecutorAgent
from mylib.mcp.tools import get_tools_list, call_tool
from mylib.lian_orm.models import TasksStatus

# 初始化页面配置
st.set_page_config(
    page_title="Lian Multi-Agent Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 样式：实现类似聊天软件的布局
st.markdown("""
<style>
    .user-msg {
        background-color: #95ec69;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0 5px auto;
        max-width: 70%;
        text-align: left;
        color: black;
    }
    .agent-msg {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
        margin: 5px auto 5px 0;
        max-width: 70%;
        text-align: left;
        border: 1px solid #e0e0e0;
        color: black;
    }
    .agent-name {
        font-size: 0.8em;
        color: #888;
        margin-bottom: 2px;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

async def tool_handler_wrapper(name: str, args: Dict) -> Any:
    """包装 MCP 工具调用"""
    try:
        # call_tool 可能是异步的，根据 mylib/mcp/tools/__init__.py 的注释
        # 如果 call_tool 是同步的，这里直接调用；如果是异步的，await
        # 假设 call_tool 是异步的 (await call_tool(...))
        return await call_tool(name, **args)
    except Exception as e:
        return f"Tool Execution Error: {str(e)}"

def render_message(role: str, agent_name: str, content: str):
    """渲染单条消息"""
    if role == "user":
        st.markdown(f"""
        <div class="user-msg">
            <div>{content}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 超过20字符折叠
        display_content = content
        is_long = len(content) > 20
        
        st.markdown(f'<div class="agent-name">{agent_name}</div>', unsafe_allow_html=True)
        
        if is_long:
            with st.expander(f"{content[:20]}... (点击展开)"):
                st.write(content)
        else:
            st.markdown(f"""
            <div class="agent-msg">
                <div>{content}</div>
            </div>
            """, unsafe_allow_html=True)

async def run_agent_flow(user_input: str):
    """执行多智能体协作流程"""
    
    # 1. 初始化智能体
    rag_agent = RAGAgent()
    planner_agent = PlannerAgent()
    # 获取工具列表传给 Executor
    tools = get_tools_list()
    executor_agent = ExecutorAgent(tools=tools)
    
    history = st.session_state.chat_history
    
    # --- RAG 阶段 ---
    with st.status("🔍 RAG Agent 正在检索...", expanded=True) as status:
        # RAG Agent 现在会自动检索数据库并总结
        rag_response = await rag_agent.a_chat(user_input, history)
        st.session_state.messages.append({
            "role": "assistant", 
            "agent": "RAG_Expert", 
            "content": rag_response
        })
        status.update(label="RAG 检索完成", state="complete", expanded=False)
        
    # --- 规划阶段 ---
    task_id = None
    steps = []
    with st.status("📝 Planner Agent 正在规划...", expanded=True) as status:
        # 将 RAG 结果作为上下文的一部分
        plan_input = f"用户请求: {user_input}\n\n背景信息: {rag_response}"
        plan_result = await planner_agent.a_chat(plan_input, history)
        
        task_id = plan_result.get('task_id')
        
        if isinstance(plan_result, dict) and "steps" in plan_result:
            steps = plan_result["steps"]
            content = f"已生成计划，共 {len(steps)} 步:\n" + "\n".join([f"{s['step_index']}. {s['instruction']}" for s in steps])
        else:
            steps = []
            content = f"规划失败或直接回答: {plan_result}"
            
        st.session_state.messages.append({
            "role": "assistant", 
            "agent": "Planner_Expert", 
            "content": content
        })
        status.update(label="任务规划完成", state="complete", expanded=False)

    # --- 执行阶段 ---
    if steps:
        progress_bar = st.progress(0)
        for i, step in enumerate(steps):
            with st.status(f"⚙️ Executor Agent 正在执行步骤 {step['step_index']}...", expanded=True) as status:
                instruction = step['instruction']
                step_id = step.get('step_id')
                
                st.write(f"指令: {instruction}")
                
                exec_result = await executor_agent.a_chat(
                    instruction, 
                    history, 
                    tool_handler=tool_handler_wrapper,
                    task_id=task_id,
                    step_id=step_id
                )
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "agent": "Executor_Expert", 
                    "content": f"步骤 {step['step_index']} 结果: {exec_result}"
                })
                progress_bar.progress((i + 1) / len(steps))
                status.update(label=f"步骤 {step['step_index']} 完成", state="complete", expanded=False)
        
        # 更新任务状态为完成
        if task_id and executor_agent.sql and executor_agent.sql.tasks:
            try:
                executor_agent.sql.tasks.update(task_id, status=TasksStatus.DONE)
            except Exception as e:
                print(f"Failed to update task status: {e}")

def main():
    st.title("💬 Lian Multi-Agent Platform")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 侧边栏
    with st.sidebar:
        st.header("控制面板")
        if st.button("🗑️ 清空对话"):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()
            
        st.markdown("### 在线专家")
        st.success("🟢 RAG Summary Expert")
        st.success("🟢 Task Planner Expert")
        st.success("🟢 Executor Expert")

    # 显示消息历史
    for msg in st.session_state.messages:
        render_message(msg["role"], msg.get("agent", "User"), msg["content"])

    # 用户输入
    if prompt := st.chat_input("请输入您的任务..."):
        # 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.rerun()

    # 处理逻辑 (在 rerun 后执行)
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        # 获取最后一条用户消息
        last_user_msg = st.session_state.messages[-1]["content"]
        
        # 运行异步流程
        asyncio.run(run_agent_flow(last_user_msg))
        
        # 强制刷新以显示结果
        st.rerun()

if __name__ == "__main__":
    main()
