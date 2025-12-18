
import streamlit as st
import asyncio
import os
from typing import List, Dict, Any
import time

from mylib.agent.rag_agent import RAGAgent
from mylib.agent.planner_agent import PlannerAgent
from mylib.agent.executor_agent import ExecutorAgent
from mylib.agent.summary_agent import SummaryAgent
from mylib.mcp.tools import get_tools_list, call_tool
from mylib.lian_orm.models import TasksStatus

# --- Configuration & Setup ---
st.set_page_config(
    page_title="Lian's Magic Atelier",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Theme & CSS ---
def get_custom_css():
    return """
    <style>
        /* Import Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap');
        
        :root {
            --bg-color: #121212;
            --sidebar-bg: #1E1E2E;
            --primary-color: #FF69B4; /* Hot Pink */
            --secondary-color: #9370DB; /* Medium Purple */
            --accent-color: #E94560; /* Red-Pink */
            --text-color: #E0E0E0;
            --user-bubble-bg: #2B2D42;
            --bot-bubble-bg: #252535;
        }

        /* Global Reset & Font */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: var(--text-color);
        }
        
        /* Spinner & Status Text Color */
        [data-testid="stSpinner"] > div {
            color: var(--primary-color) !important;
        }
        .stMarkdown p {
            color: var(--text-color);
        }
        
        /* App Background */
        .stApp {
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: rgba(30, 30, 46, 0.95);
            border-right: 1px solid rgba(255, 105, 180, 0.2);
            backdrop-filter: blur(10px);
        }
        
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: var(--primary-color) !important;
            font-family: 'Inter', sans-serif;
        }

        /* Hide Streamlit Branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        /* header {visibility: hidden;}  <-- Removed to show Sidebar Toggle */
        [data-testid="stHeader"] {
            background-color: transparent;
        }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: transparent; 
        }
        ::-webkit-scrollbar-thumb {
            background: var(--primary-color); 
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-color); 
        }

        /* Chat Input Styling */
        .stChatInputContainer {
            padding-bottom: 0px !important;
            background-color: transparent !important;
        }
        
        /* Fix: Remove white background from bottom fixed container */
        [data-testid="stBottom"] {
            background-color: #151520 !important;
            border-top: 1px solid rgba(255, 105, 180, 0.1);
            padding-top: 10px !important;
            padding-bottom: 30px !important;
        }
        [data-testid="stBottom"] > div {
            background-color: transparent !important;
        }
        
        /* Remove extra spacing from the inner wrapper of chat input */
        [data-testid="stChatInput"] {
            padding-bottom: 0 !important;
            margin-bottom: 0 !important;
        }
        
        /* Target the specific div that often holds the input and adds spacing */
        [data-testid="stBottom"] > div > div {
            padding-bottom: 0 !important;
        }

        .stChatInputContainer textarea {
            background-color: #1E1E2E !important;
            border: 1px solid rgba(255, 105, 180, 0.3);
            color: var(--text-color) !important;
            border-radius: 12px;
        }
        .stChatInputContainer textarea:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 10px rgba(255, 105, 180, 0.2);
        }
        
        /* Button Styling */
        .stButton > button {
            color: var(--text-color);
            border-color: var(--primary-color);
            background-color: transparent;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            color: #FFFFFF !important;
            border-color: var(--accent-color) !important;
            background-color: rgba(233, 69, 96, 0.2);
        }

        /* Chat Message Styling */
        [data-testid="stChatMessage"] {
            background-color: transparent;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 0.5rem;
            transition: all 0.3s ease;
        }
        
        [data-testid="stChatMessage"]:hover {
            background-color: rgba(255, 255, 255, 0.02);
        }
        
        /* Ensure text in chat bubbles is readable (Light color) */
        [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] div {
            color: #E0E0E0 !important;
        }

        /* User Message */
        [data-testid="stChatMessage"][data-testid="user"] {
            background-color: rgba(43, 45, 66, 0.6);
            border-left: 3px solid var(--primary-color);
        }

        /* Avatar Styling - Rounded Corners for User Avatar */
        [data-testid="stChatMessage"] img {
            border-radius: 12px !important;
        }

        /* Assistant Message */
        [data-testid="stChatMessage"][data-testid="assistant"] {
            background-color: rgba(37, 37, 53, 0.6);
            border-left: 3px solid var(--secondary-color);
        }
        
        /* Code Blocks */
        code {
            font-family: 'JetBrains Mono', monospace;
            color: #FFB6C1;
        }
        
        /* Status Container */
        [data-testid="stStatusWidget"] {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(147, 112, 219, 0.3);
            border-radius: 8px;
        }

        /* Custom Expert Badges */
        .expert-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .badge-rag { background-color: rgba(52, 152, 219, 0.2); color: #3498db; border: 1px solid #3498db; }
        .badge-planner { background-color: rgba(155, 89, 182, 0.2); color: #9b59b6; border: 1px solid #9b59b6; }
        .badge-executor { background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
        .badge-summary { background-color: rgba(255, 105, 180, 0.2); color: #FF69B4; border: 1px solid #FF69B4; }
        .badge-main { background-color: rgba(255, 105, 180, 0.2); color: #FF69B4; border: 1px solid #FF69B4; }

    </style>
    """

st.markdown(get_custom_css(), unsafe_allow_html=True)

import requests
from mylib.config import ConfigLoader

# --- Helper Functions ---

# 加载配置以获取 MCP Server 地址
# 指向 ../llm 目录以加载 llm_config.toml
config = ConfigLoader(config_path="../llm")
MCP_HOST = str(config.LLM_CONFIG.MCP_SERVER_HOST)
MCP_PORT = str(config.LLM_CONFIG.MCP_SERVER_PORT)
MCP_SERVER_URL = f"http://{MCP_HOST}:{MCP_PORT}"

# Avatar Path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_AVATAR_PATH = os.path.join(CURRENT_DIR, "avatar.jpg")

def get_remote_tools_list() -> List[Dict]:
    """从 MCP Server 获取工具列表"""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/tools", timeout=5)
        if response.status_code == 200:
            return response.json()["tools"]
        else:
            st.error(f"Failed to fetch tools from MCP Server: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Connection to MCP Server failed: {e}")
        return []

async def tool_handler_wrapper(name: str, args: Dict) -> Any:
    """包装 MCP 工具调用 (通过 HTTP 请求 MCP Server)"""
    try:
        # 使用 run_in_executor 避免阻塞异步循环
        loop = asyncio.get_running_loop()
        
        def _call_remote():
            response = requests.post(
                f"{MCP_SERVER_URL}/tools/{name}/call",
                json=args,
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP Error {response.status_code}: {response.text}"}

        return await loop.run_in_executor(None, _call_remote)
    except Exception as e:
        return f"Tool Execution Error: {str(e)}"

def get_avatar(agent_name: str) -> str:
    """根据 Agent 名称返回头像"""
    if "RAG" in agent_name:
        return "📖"
    elif "Planner" in agent_name:
        return "🔮"
    elif "Executor" in agent_name:
        return "⚡"
    elif "Summary" in agent_name:
        return "🐱"
    elif "User" in agent_name:
        if os.path.exists(USER_AVATAR_PATH):
            return USER_AVATAR_PATH
        return "👤"
    else:
        return "🐱" # 小恋

def get_badge_html(agent_name: str) -> str:
    """获取 Agent 徽章 HTML"""
    if "RAG" in agent_name:
        return '<span class="expert-badge badge-rag">全知魔导书</span>'
    elif "Planner" in agent_name:
        return '<span class="expert-badge badge-planner">星盘占卜师</span>'
    elif "Executor" in agent_name:
        return '<span class="expert-badge badge-executor">魔力执行官</span>'
    elif "Summary" in agent_name:
        return '<span class="expert-badge badge-summary">傲娇魔女·小恋</span>'
    else:
        return '<span class="expert-badge badge-main">傲娇魔女·小恋</span>'

# --- Main Logic ---

async def run_agent_flow(user_input: str, status_placeholders: Dict):
    """执行多智能体协作流程"""
    
    # 1. 初始化智能体
    rag_agent = RAGAgent()
    planner_agent = PlannerAgent()
    summary_agent = SummaryAgent()
    
    # 获取远程工具列表
    tools = get_remote_tools_list()
    if not tools:
        st.warning("⚠️ 未检测到可用工具，请检查 MCP Server 是否启动。")
        
    executor_agent = ExecutorAgent(tools=tools)
    
    history = st.session_state.chat_history
    
    # 更新侧边栏状态
    status_placeholders["RAG"].info("🔵 全知魔导书 (RAG)")
    
    # --- RAG 阶段 ---
    with st.spinner("📖 全知魔导书正在翻阅记忆..."):
        rag_response = await rag_agent.a_chat(user_input, history)
        st.session_state.messages.append({
            "role": "assistant", 
            "agent": "RAG_Expert", 
            "content": rag_response
        })
    
    status_placeholders["RAG"].success("🟢 全知魔导书 (RAG)")
    status_placeholders["Planner"].info("🔵 星盘占卜师 (Planner)")

    # --- 规划阶段 ---
    task_id = None
    steps = []
    with st.spinner("🔮 星盘占卜师正在绘制命运轨迹..."):
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

    status_placeholders["Planner"].success("🟢 星盘占卜师 (Planner)")
    status_placeholders["Executor"].info("🔵 魔力执行官 (Executor)")

    # --- 执行阶段 ---
    execution_results_text = ""
    if steps:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, step in enumerate(steps):
            status_text.markdown(f"<span style='color: #E0E0E0;'>⚡ 正在施法: 步骤 {step['step_index']}/{len(steps)} - {step['instruction'][:20]}...</span>", unsafe_allow_html=True)
            
            instruction = step['instruction']
            step_id = step.get('step_id')
            
            exec_result = await executor_agent.a_chat(
                instruction, 
                history, 
                tool_handler=tool_handler_wrapper,
                task_id=task_id,
                step_id=step_id
            )
            
            result_text = f"步骤 {step['step_index']} 结果: {exec_result}"
            execution_results_text += result_text + "\n\n"
            
            st.session_state.messages.append({
                "role": "assistant", 
                "agent": "Executor_Expert", 
                "content": result_text
            })
            progress_bar.progress((i + 1) / len(steps))
        
        status_text.empty()
        progress_bar.empty()
        
        # 更新任务状态为完成
        if task_id and executor_agent.sql and executor_agent.sql.tasks:
            try:
                executor_agent.sql.tasks.update(task_id, status=TasksStatus.DONE)
            except Exception as e:
                print(f"Failed to update task status: {e}")
    
    status_placeholders["Executor"].success("🟢 魔力执行官 (Executor)")
    
    # --- 总结阶段 ---
    with st.spinner("🐱 小恋正在整理魔法笔记..."):
        summary_response = await summary_agent.a_chat(
            user_input, 
            history, 
            rag_context=rag_response, 
            plan_context=content,
            execution_results=execution_results_text
        )
        st.session_state.messages.append({
            "role": "assistant", 
            "agent": "Summary_Expert", 
            "content": summary_response
        })
        
        # 将最终回复加入对话历史，支持多轮对话
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": summary_response
        })

def main():
    # --- Sidebar ---
    with st.sidebar:
        st.title("🐱 Lian's Atelier")
        st.markdown("---")
        
        st.subheader("🔮 在线专家 (Online Experts)")
        
        # 状态占位符
        status_placeholders = {
            "RAG": st.empty(),
            "Planner": st.empty(),
            "Executor": st.empty()
        }
        
        # 初始状态
        status_placeholders["RAG"].success("🟢 全知魔导书 (RAG)")
        status_placeholders["Planner"].success("🟢 星盘占卜师 (Planner)")
        status_placeholders["Executor"].success("🟢 魔力执行官 (Executor)")
        
        st.markdown("---")
        st.markdown("### 🛠️ 控制面板")
        if st.button("🗑️ 清空记忆 (Clear Memory)", type="secondary"):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()
            
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #888; font-size: 0.8em;'>
            Powered by Lian MCP Agent<br>
            Theme: Catgirl Witch
        </div>
        """, unsafe_allow_html=True)

    # --- Main Chat Area ---
    st.markdown("<h1 style='color: var(--primary-color);'>💬 魔法工坊 (Magic Workshop)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: var(--primary-color); opacity: 0.8;'>与小恋和她的魔法使魔们一起解决问题吧！</p>", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 渲染历史消息
    for msg in st.session_state.messages:
        role = msg["role"]
        agent_name = msg.get("agent", "User")
        content = msg["content"]
        
        with st.chat_message(role, avatar=get_avatar(agent_name)):
            if role != "user":
                st.markdown(get_badge_html(agent_name), unsafe_allow_html=True)
            st.markdown(content)

    # 用户输入
    if prompt := st.chat_input("请输入您的愿望... (Input your wish)"):
        # 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt, "agent": "User"})
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        user_avatar = USER_AVATAR_PATH if os.path.exists(USER_AVATAR_PATH) else "👤"
        with st.chat_message("user", avatar=user_avatar):
            st.markdown(prompt)
            
        # 运行异步流程
        asyncio.run(run_agent_flow(prompt, status_placeholders))
        
        # 强制刷新以显示完整历史
        st.rerun()

if __name__ == "__main__":
    main()
