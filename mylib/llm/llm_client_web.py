"""
Streamlit Web UI for MCP Client
用来测试的，不是最终版本
"""

import json
import requests
import streamlit as st
from typing import List, Dict, Any
from datetime import datetime

from mylib.config import ConfigLoader


class MCPClientWeb:
    """Web 版本的 MCP 客户端"""
    
    def __init__(self):
        self.config = ConfigLoader()
        host = str(self.config.LLM_CONFIG.MCP_SERVER_HOST)
        port = str(self.config.LLM_CONFIG.MCP_SERVER_PORT)
        self.mcp_server_url = f"http://{host}:{port}"
        self.api_key = getattr(self.config.LLM_CONFIG, "DEEPSEEK_API_KEY", "")
        self.base_url = "https://api.deepseek.com/v1"
        self.available_tools = self._load_tools()
    
    def _load_tools(self) -> List[Dict]:
        """从MCP服务器加载可用工具"""
        try:
            response = requests.get(f"{self.mcp_server_url}/tools", timeout=5)
            if response.status_code == 200:
                return response.json()["tools"]
            else:
                return []
        except Exception as e:
            st.error(f"连接MCP服务器错误: {e}")
            return []
    
    def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """调用MCP工具"""
        try:
            response = requests.post(
                f"{self.mcp_server_url}/tools/{tool_name}/call",
                json=arguments,
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                return {"error": f"HTTP错误: {response.status_code}"}
        except Exception as e:
            return {"error": f"调用工具错误: {str(e)}"}
    
    def chat_with_llm(self, message: str, conversation_history: List[Dict], is_tool_result: bool = False) -> str:
        """与LLM对话, 支持工具调用"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        system_prompt = f"""你是一个AI助手，可以调用各种工具来帮助用户完成任务。

可用工具:
{json.dumps(self.available_tools, indent=2, ensure_ascii=False)}

工具调用规则:
1. 当需要调用工具时，请按照以下格式响应：
TOOL_CALL: {{
    "tool_calls": [
        {{
            "name": "tool_name",
            "arguments": {{
                "param1": "value1",
                "param2": "value2"
            }}
        }}
    ]
}}

2. 你可以连续多次调用工具来完成复杂任务
3. 每次工具调用后，我会返回结果给你，你可以基于结果决定：
    - 继续调用其他工具（返回新的 TOOL_CALL）
    - 已获得足够信息，给出最终答案（返回 TOOL_CALL_END）

4. 当你认为已经收集到足够信息可以回答用户问题时，必须在回复开头添加标记：
TOOL_CALL_END

然后给出你的最终答案。

注意：不要在工具调用阶段尝试回答问题，先完成所有必要的工具调用，最后统一回答。"""

        if not conversation_history:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        else:
            messages = [{"role": "system", "content": system_prompt}] + conversation_history
            if is_tool_result:
                messages.append({"role": "user", "content": f"工具调用结果:\n{message}\n\n请基于结果决定下一步操作。"})
            else:
                messages.append({"role": "user", "content": message})
        
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result["choices"][0]["message"]["content"]
                return assistant_message
            else:
                return f"API调用错误: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"LLM调用错误: {str(e)}"
    
    def process_user_request(self, user_input: str, log_history: List[Dict], update_callback=None) -> tuple[str, List[Dict]]:
        """处理用户请求，支持连续工具调用
        
        Args:
            user_input: 用户输入
            log_history: 日志历史列表（会被修改）
            update_callback: 更新回调函数，每次添加日志后调用以刷新界面
            
        Returns:
            (最终答案, 对话历史)
        """
        conversation_history = []
        
        # 首次 LLM 调用
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_history.append({
            "type": "info",
            "content": "发送用户请求到 LLM...",
            "timestamp": timestamp
        })
        if update_callback:
            update_callback()
        
        llm_response = self.chat_with_llm(user_input, conversation_history, is_tool_result=False)
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": llm_response})
        
        log_history.append({
            "type": "llm_response",
            "content": llm_response,
            "round": 1,
            "timestamp": datetime.now().strftime('%H:%M:%S')
        })
        if update_callback:
            update_callback()
        
        # 工具调用循环计数
        tool_call_round = 0
        max_rounds = 10
        
        while tool_call_round < max_rounds:
            if "TOOL_CALL_END" in llm_response:
                log_history.append({
                    "type": "success",
                    "content": "工具调用结束，返回最终答案",
                    "timestamp": datetime.now().strftime('%H:%M:%S')
                })
                if update_callback:
                    update_callback()
                final_answer = llm_response.replace("TOOL_CALL_END", "").strip()
                return final_answer, conversation_history
            
            if "TOOL_CALL:" not in llm_response:
                return llm_response, conversation_history
            
            try:
                tool_call_round += 1
                
                log_history.append({
                    "type": "tool_call_start",
                    "round": tool_call_round,
                    "timestamp": datetime.now().strftime('%H:%M:%S')
                })
                if update_callback:
                    update_callback()
                
                tool_call_json = llm_response.split("TOOL_CALL:")[1].strip()
                json_start = tool_call_json.find('{')
                json_end = tool_call_json.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    tool_call_json = tool_call_json[json_start:json_end]
                
                tool_call_data = json.loads(tool_call_json)
                
                tool_results = []
                for idx, tool_call in enumerate(tool_call_data.get("tool_calls", []), 1):
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("arguments", {})
                    
                    result = self.call_tool(tool_name, tool_args)
                    
                    log_history.append({
                        "type": "tool_execution",
                        "tool_name": tool_name,
                        "arguments": tool_args,
                        "result": result,
                        "idx": idx,
                        "timestamp": datetime.now().strftime('%H:%M:%S')
                    })
                    if update_callback:
                        update_callback()
                    
                    tool_results.append({
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result": result
                    })
                
                tool_results_message = json.dumps(tool_results, indent=2, ensure_ascii=False)
                conversation_history.append({"role": "user", "content": f"工具调用结果:\n{tool_results_message}"})
                
                log_history.append({
                    "type": "info",
                    "content": "发送工具结果到 LLM...",
                    "timestamp": datetime.now().strftime('%H:%M:%S')
                })
                if update_callback:
                    update_callback()
                
                llm_response = self.chat_with_llm(tool_results_message, conversation_history, is_tool_result=True)
                conversation_history.append({"role": "assistant", "content": llm_response})
                
                log_history.append({
                    "type": "llm_response",
                    "content": llm_response,
                    "round": tool_call_round + 1,
                    "timestamp": datetime.now().strftime('%H:%M:%S')
                })
                if update_callback:
                    update_callback()
                
            except json.JSONDecodeError as e:
                error_msg = f"工具调用 JSON 解析错误: {e}"
                log_history.append({
                    "type": "error",
                    "content": error_msg,
                    "timestamp": datetime.now().strftime('%H:%M:%S')
                })
                if update_callback:
                    update_callback()
                return error_msg, conversation_history
            except Exception as e:
                error_msg = f"工具调用过程错误: {e}"
                log_history.append({
                    "type": "error",
                    "content": error_msg,
                    "timestamp": datetime.now().strftime('%H:%M:%S')
                })
                if update_callback:
                    update_callback()
                return error_msg, conversation_history
        
        warning_msg = f"⚠️ 工具调用超过最大轮次限制 ({max_rounds})"
        log_history.append({
            "type": "error",
            "content": warning_msg,
            "timestamp": datetime.now().strftime('%H:%M:%S')
        })
        if update_callback:
            update_callback()
        return llm_response, conversation_history


def main():
    """Streamlit 主应用"""
    
    st.set_page_config(
        page_title="MCP Client - Web UI",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown("""
        <style>
        .user-message {
            background-color: #E8D5F2;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .assistant-message {
            background-color: #D5F2F2;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .message-header {
            font-weight: bold;
            margin-bottom: 8px;
        }
        .stTextInput > div > div > input {
            font-size: 16px;
        }
        .stTextArea > div > div > textarea {
            font-size: 16px;
        }
        .log-container {
            max-height: 70vh;
            overflow-y: auto;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🤖 MCP Client - Web UI")
    st.caption("基于 Model Context Protocol 的智能助手")
    
    if "client" not in st.session_state:
        st.session_state.client = MCPClientWeb()
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "processing" not in st.session_state:
        st.session_state.processing = False
    
    if "log_history" not in st.session_state:
        st.session_state.log_history = []
    
    with st.sidebar:
        st.header("📚 可用工具")
        if st.session_state.client.available_tools:
            for tool in st.session_state.client.available_tools:
                with st.expander(f"🔧 {tool['name']}"):
                    st.write(tool['description'])
                    if 'parameters' in tool:
                        st.json(tool['parameters'])
        else:
            st.warning("⚠️ 无法连接到 MCP 服务器")
            st.info("请确保 MCP Server 已启动：\n```bash\nuv run python ./main.py server\n```")
        
        if st.button("🔄 刷新工具列表"):
            st.session_state.client.available_tools = st.session_state.client._load_tools()
            st.rerun()
        
        if st.button("🗑️ 清空对话历史"):
            st.session_state.chat_history = []
            st.session_state.log_history = []
            st.rerun()
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.header("💬 对话")
        
        chat_container = st.container()
        with chat_container:
            if not st.session_state.chat_history:
                st.info("👋 喵~欢迎回家捏！这里是恋恋，一个会魔法的小猫娘助手")
            else:
                for msg in st.session_state.chat_history:
                    if msg["role"] == "user":
                        st.markdown(f"""
                        <div class="user-message">
                            <div class="message-header">🙋 Sakurine</div>
                            <div>{msg["content"]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    elif msg["role"] == "assistant":
                        st.markdown(f"""
                        <div class="assistant-message">
                            <div class="message-header">🤖 恋</div>
                            <div>{msg["content"]}</div>
                        </div>
                        """, unsafe_allow_html=True)
        
        st.markdown("---")
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "💭 输入你的问题...",
                placeholder="例如：读取 /tmp/test.txt 的内容",
                disabled=st.session_state.processing,
                key="user_input",
                height=100
            )
            submit_button = st.form_submit_button(
                "📤 发送",
                use_container_width=True,
                disabled=st.session_state.processing
            )
        
        if submit_button and user_input:
            st.session_state.processing = True
            st.rerun()
    
    with col2:
        st.header("📊 执行日志")
        
        progress_placeholder = st.empty()
        
        log_display = st.container()
        
        def render_logs():
            with log_display:
                if not st.session_state.log_history:
                    st.info("🔍 等待用户输入...")
                else:
                    for log_entry in st.session_state.log_history:
                        log_type = log_entry.get("type")
                        content = log_entry.get("content")
                        timestamp = log_entry.get("timestamp", "")
                        
                        if log_type == "llm_response":
                            round_num = log_entry.get("round", 1)
                            with st.expander(f"📝 LLM 响应 #{round_num} ({timestamp})", expanded=False):
                                st.text(content[:500] + ("..." if len(content) > 500 else ""))
                        
                        elif log_type == "tool_call_start":
                            round_num = log_entry.get("round")
                            st.markdown(f"### 🔧 工具调用轮次 #{round_num}")
                            st.caption(f"⏰ {timestamp}")
                        
                        elif log_type == "tool_execution":
                            tool_name = log_entry.get("tool_name")
                            tool_args = log_entry.get("arguments")
                            result = log_entry.get("result")
                            idx = log_entry.get("idx", 1)
                            
                            with st.expander(f"🛠️ 工具 #{idx}: {tool_name}", expanded=False):
                                st.json({"arguments": tool_args})
                                result_str = json.dumps(result, ensure_ascii=False)
                                if len(result_str) > 500:
                                    st.text_area("结果", result_str[:500] + "...", height=100, key=f"result_{timestamp}_{idx}")
                                else:
                                    st.json(result)
                        
                        elif log_type == "info":
                            st.info(f"⏰ {timestamp} - {content}")
                        
                        elif log_type == "success":
                            st.success(f"✅ {timestamp} - {content}")
                        
                        elif log_type == "error":
                            st.error(content)
        
        render_logs()
    
    if st.session_state.processing:
        user_input = st.session_state.get("user_input", "")
        
        if user_input:
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })
            
            log_placeholder = st.empty()
            progress_bar = progress_placeholder.progress(0)
            status_text = st.empty()
            
            def update_ui():
                """实时更新 UI"""
                with log_placeholder.container():
                    for log_entry in st.session_state.log_history:
                        log_type = log_entry.get("type")
                        content = log_entry.get("content")
                        timestamp = log_entry.get("timestamp", "")
                        
                        if log_type == "llm_response":
                            round_num = log_entry.get("round", 1)
                            with st.expander(f"📝 LLM 响应 #{round_num} ({timestamp})", expanded=False):
                                st.text(content[:500] + ("..." if len(content) > 500 else ""))
                        
                        elif log_type == "tool_call_start":
                            round_num = log_entry.get("round")
                            st.markdown(f"### 🔧 工具调用轮次 #{round_num}")
                            st.caption(f"⏰ {timestamp}")
                        
                        elif log_type == "tool_execution":
                            tool_name = log_entry.get("tool_name")
                            tool_args = log_entry.get("arguments")
                            result = log_entry.get("result")
                            idx = log_entry.get("idx", 1)
                            
                            with st.expander(f"🛠️ 工具 #{idx}: {tool_name}", expanded=False):
                                st.json({"arguments": tool_args})
                                result_str = json.dumps(result, ensure_ascii=False)
                                if len(result_str) > 500:
                                    st.text_area("结果", result_str[:500] + "...", height=100, key=f"result_{timestamp}_{idx}_{len(st.session_state.log_history)}")
                                else:
                                    st.json(result)
                        
                        elif log_type == "info":
                            st.info(f"⏰ {timestamp} - {content}")
                        
                        elif log_type == "success":
                            st.success(f"✅ {timestamp} - {content}")
                        
                        elif log_type == "error":
                            st.error(content)
                
                total_steps = 10
                current_step = len(st.session_state.log_history)
                progress = min(current_step / total_steps, 0.99)
                progress_bar.progress(progress)
                
                if st.session_state.log_history:
                    last_log = st.session_state.log_history[-1]
                    if last_log["type"] == "info":
                        status_text.info(f"🔄 {last_log['content']}")
                    elif last_log["type"] == "success":
                        status_text.success(f"✅ {last_log['content']}")
                        progress_bar.progress(1.0)
            
            response, _ = st.session_state.client.process_user_request(
                user_input,
                st.session_state.log_history,
                update_callback=update_ui
            )
            
            progress_bar.progress(1.0)
            status_text.success("✅ 处理完成！")
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
        
        st.session_state.processing = False
        st.rerun()


if __name__ == "__main__":
    main()
