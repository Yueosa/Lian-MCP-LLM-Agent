"""
Agent 监控页面 (Monitor Web)

提供四智能体虚拟网络的可视化监控。

功能：
1. Agent 网络拓扑可视化
2. 实时日志流
3. 多进度条并行任务监控
4. FSM 状态显示

数据来源：从 StateStore 读取实时状态
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Any

# 导入状态存储
from mylib.agent.state_store import state_store

# 注入自定义 CSS 和 HTML
MONITOR_CSS = """
<style>
/* 监控面板主题 */
:root {
    --monitor-bg: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    --card-bg: rgba(255, 255, 255, 0.05);
    --border-color: rgba(255, 255, 255, 0.1);
    --text-primary: #e0e0e0;
    --text-secondary: #a0a0a0;
    --accent-pink: #ff69b4;
    --accent-blue: #00bfff;
    --accent-green: #00ff88;
    --accent-yellow: #ffd700;
    --accent-red: #ff4444;
}

.monitor-container {
    font-family: 'Segoe UI', system-ui, sans-serif;
    padding: 20px;
}

/* Agent 网络节点 */
.agent-node {
    display: inline-block;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    text-align: center;
    line-height: 120px;
    margin: 10px;
    font-weight: bold;
    transition: all 0.3s ease;
    box-shadow: 0 0 20px rgba(255, 105, 180, 0.3);
}

.agent-node.rag { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); color: #333; }
.agent-node.planner { background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%); color: #333; }
.agent-node.executor { background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%); color: #333; }
.agent-node.summary { background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #333; }

.agent-node.active {
    animation: pulse 1s infinite;
    box-shadow: 0 0 30px rgba(255, 255, 255, 0.5);
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

/* 状态指示器 */
.state-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
}

.state-idle { background: #888; }
.state-processing { background: var(--accent-blue); animation: blink 1s infinite; }
.state-calling { background: var(--accent-yellow); animation: blink 0.5s infinite; }
.state-completed { background: var(--accent-green); }
.state-error { background: var(--accent-red); }

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* 日志条目 */
.log-entry {
    padding: 8px 12px;
    margin: 4px 0;
    border-radius: 4px;
    font-family: 'Consolas', monospace;
    font-size: 12px;
    border-left: 3px solid;
}

.log-system { border-color: var(--accent-pink); background: rgba(255, 105, 180, 0.1); }
.log-agent { border-color: var(--accent-blue); background: rgba(0, 191, 255, 0.1); }
.log-llm { border-color: var(--accent-yellow); background: rgba(255, 215, 0, 0.1); }
.log-tool { border-color: var(--accent-green); background: rgba(0, 255, 136, 0.1); }
.log-error { border-color: var(--accent-red); background: rgba(255, 68, 68, 0.1); }

/* 进度条 */
.progress-container {
    margin: 10px 0;
}

.progress-bar {
    height: 24px;
    border-radius: 12px;
    background: var(--card-bg);
    overflow: hidden;
    position: relative;
}

.progress-fill {
    height: 100%;
    border-radius: 12px;
    transition: width 0.3s ease;
}

.progress-fill.parallel { background: linear-gradient(90deg, var(--accent-pink), var(--accent-blue)); }
.progress-fill.sequential { background: linear-gradient(90deg, var(--accent-blue), var(--accent-green)); }

.progress-text {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 12px;
    font-weight: bold;
    color: white;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
}

/* 连接线 SVG */
.connection-line {
    stroke: rgba(255, 255, 255, 0.3);
    stroke-width: 2;
    fill: none;
    stroke-dasharray: 5, 5;
    animation: dash 1s linear infinite;
}

.connection-line.active {
    stroke: var(--accent-pink);
    stroke-width: 3;
    stroke-dasharray: none;
}

@keyframes dash {
    to { stroke-dashoffset: -10; }
}
</style>
"""


def render_agent_network(agent_states: Dict[str, str]):
    """
    渲染 Agent 网络拓扑
    
    :param agent_states: Agent 状态映射 {"RAG": "IDLE", "Planner": "PROCESSING", ...}
    """
    st.markdown(MONITOR_CSS, unsafe_allow_html=True)
    
    # 网络拓扑 SVG
    network_svg = f"""
    <div style="text-align: center; padding: 20px;">
        <svg width="500" height="300" viewBox="0 0 500 300">
            <!-- 连接线 -->
            <path class="connection-line {'active' if agent_states.get('RAG') == 'PROCESSING' else ''}" 
                  d="M 100 80 Q 175 120 250 80" />
            <path class="connection-line {'active' if agent_states.get('Planner') == 'PROCESSING' else ''}" 
                  d="M 250 80 Q 325 120 400 80" />
            <path class="connection-line {'active' if agent_states.get('Executor') == 'PROCESSING' else ''}" 
                  d="M 400 80 Q 400 180 250 220" />
            <path class="connection-line {'active' if agent_states.get('Summary') == 'PROCESSING' else ''}" 
                  d="M 250 220 Q 100 180 100 80" />
            
            <!-- 中心标签 -->
            <text x="250" y="150" text-anchor="middle" fill="#888" font-size="14">
                Agent Network
            </text>
        </svg>
    </div>
    """
    
    # Agent 节点
    cols = st.columns(4)
    agents = [
        ("RAG", "rag", "记忆检索"),
        ("Planner", "planner", "任务规划"),
        ("Executor", "executor", "工具执行"),
        ("Summary", "summary", "结果总结")
    ]
    
    for i, (name, css_class, desc) in enumerate(agents):
        with cols[i]:
            state = agent_states.get(name, "IDLE")
            active_class = "active" if state in ["PROCESSING", "CALLING_LLM", "CALLING_TOOL"] else ""
            
            st.markdown(f"""
                <div class="agent-node {css_class} {active_class}" title="{desc}">
                    {name}
                </div>
                <div style="text-align: center; margin-top: 8px;">
                    <span class="state-indicator state-{'processing' if 'PROCESSING' in state else 'idle'}"></span>
                    <span style="color: #888; font-size: 12px;">{state}</span>
                </div>
            """, unsafe_allow_html=True)


def render_log_stream(logs: List[Dict], max_display: int = 50):
    """
    渲染实时日志流
    
    :param logs: 日志列表 [{"level": "AGENT", "message": "...", "timestamp": "..."}]
    :param max_display: 最大显示数量
    """
    st.markdown("### 📋 实时日志")
    
    log_container = st.container()
    
    with log_container:
        for log in logs[-max_display:]:
            level = log.get("level", "SYSTEM").lower()
            message = log.get("message", "")
            timestamp = log.get("timestamp", "")[:19]  # 截取到秒
            agent = log.get("agent_id", "")
            
            css_class = f"log-{level}"
            
            st.markdown(f"""
                <div class="{css_class} log-entry">
                    <span style="color: #888;">[{timestamp}]</span>
                    <span style="color: var(--accent-blue);">[{agent}]</span>
                    {message}
                </div>
            """, unsafe_allow_html=True)


def render_progress_bars(tasks: List[Dict]):
    """
    渲染多进度条
    
    :param tasks: 任务列表 [{"name": "Step 1", "progress": 0.5, "type": "parallel"}, ...]
    """
    st.markdown("### 📊 执行进度")
    
    for task in tasks:
        name = task.get("name", "Task")
        progress = task.get("progress", 0)
        task_type = task.get("type", "sequential")
        status = task.get("status", "pending")
        
        progress_pct = int(progress * 100)
        fill_class = "parallel" if task_type == "parallel" else "sequential"
        
        st.markdown(f"""
            <div class="progress-container">
                <div style="margin-bottom: 4px;">
                    <span style="font-weight: bold;">{name}</span>
                    <span style="color: #888; float: right;">{status}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill {fill_class}" style="width: {progress_pct}%"></div>
                    <span class="progress-text">{progress_pct}%</span>
                </div>
            </div>
        """, unsafe_allow_html=True)


def render_callback_history(callbacks: List[Dict]):
    """
    渲染回调历史
    
    :param callbacks: 回调记录 [{"from": "Executor", "to": "Planner", "action": "REPLAN", ...}]
    """
    st.markdown("### 🔄 回调记录")
    
    if not callbacks:
        st.info("暂无回调记录")
        return
    
    for cb in callbacks[-10:]:
        source = cb.get("source_agent", "")
        target = cb.get("target_agent", "")
        action = cb.get("action", "")
        reason = cb.get("reason", "")[:50]
        status = cb.get("status", "")
        
        status_color = {
            "ACCEPTED": "var(--accent-green)",
            "REJECTED": "var(--accent-red)",
            "TIMEOUT": "var(--accent-yellow)"
        }.get(status, "#888")
        
        st.markdown(f"""
            <div style="padding: 8px; margin: 4px 0; background: var(--card-bg); border-radius: 4px;">
                <span style="color: var(--accent-pink);">{source}</span>
                <span style="color: #888;"> → </span>
                <span style="color: var(--accent-blue);">{target}</span>
                <span style="background: rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 10px; margin-left: 8px;">
                    {action}
                </span>
                <span style="color: {status_color}; float: right;">{status}</span>
                <div style="color: #888; font-size: 12px; margin-top: 4px;">{reason}</div>
            </div>
        """, unsafe_allow_html=True)


def render_stats_dashboard(stats: Dict):
    """
    渲染统计面板
    
    :param stats: 统计数据
    """
    st.markdown("### 📈 统计概览")
    
    cols = st.columns(4)
    
    metrics = [
        ("🎯 总任务", stats.get("total_tasks", 0), ""),
        ("✅ 已完成", stats.get("completed", 0), "var(--accent-green)"),
        ("❌ 失败", stats.get("failed", 0), "var(--accent-red)"),
        ("⏱️ 耗时", f"{stats.get('total_time_ms', 0)}ms", "var(--accent-blue)")
    ]
    
    for i, (label, value, color) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
                <div style="text-align: center; padding: 15px; background: var(--card-bg); border-radius: 8px;">
                    <div style="font-size: 24px; font-weight: bold; color: {color or '#fff'};">{value}</div>
                    <div style="color: #888; font-size: 12px;">{label}</div>
                </div>
            """, unsafe_allow_html=True)


def monitor_page():
    """
    Streamlit 监控页面主函数
    
    使用方法：
    在 Streamlit 应用中调用此函数渲染监控页面
    """
    st.set_page_config(
        page_title="Agent Monitor",
        page_icon="🔮",
        layout="wide"
    )
    
    st.markdown(MONITOR_CSS, unsafe_allow_html=True)
    st.title("🔮 Agent 监控面板")
    
    # 从 StateStore 读取实时状态
    all_state = state_store.get_all_state()
    
    # 侧边栏控制
    with st.sidebar:
        st.markdown("### ⚙️ 控制面板")
        auto_refresh = st.checkbox("自动刷新", value=True)
        refresh_interval = st.slider("刷新间隔(秒)", 1, 10, 2)
        
        if st.button("🔄 手动刷新"):
            st.rerun()
            
        st.markdown("---")
        if st.button("🗑️ 清空日志"):
            state_store.clear_logs()
            st.rerun()
            
        if st.button("🔄 重置会话"):
            state_store.reset_session()
            st.rerun()
            
        # 显示最后更新时间
        st.markdown("---")
        st.caption(f"最后更新: {all_state.get('timestamp', '')[:19]}")
    
    # 主内容区
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Agent 网络
        st.markdown("### 🌐 Agent 网络")
        # 从 StateStore 获取 Agent 状态
        raw_agents = all_state.get("agents", {})
        agent_states = {
            "RAG": raw_agents.get("RAG_Agent", {}).get("state", "IDLE"),
            "Planner": raw_agents.get("Planner_Lian", {}).get("state", "IDLE"),
            "Executor": raw_agents.get("Executor_Ran", {}).get("state", "IDLE"),
            "Summary": raw_agents.get("Summary_Lian", {}).get("state", "IDLE")
        }
        render_agent_network(agent_states)
        
        # 进度条 - 从 StateStore 获取
        tasks = all_state.get("tasks", [])
        if not tasks:
            st.info("暂无任务执行")
        else:
            render_progress_bars(tasks)
    
    with col2:
        # 统计
        stats = all_state.get("stats", {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "total_time_ms": 0
        })
        render_stats_dashboard(stats)
        
        # 回调历史
        callbacks = all_state.get("callbacks", [])
        render_callback_history(callbacks)
    
    # 日志流
    logs = all_state.get("logs", [])
    if not logs:
        st.info("暂无日志记录。运行 `python main.py agent` 开始对话后，日志将在这里实时显示。")
    else:
        render_log_stream(logs)
    
    # 自动刷新
    if auto_refresh:
        import time
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    monitor_page()
