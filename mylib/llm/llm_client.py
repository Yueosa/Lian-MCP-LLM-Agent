import json
import requests
from typing import List, Dict, Any

from mylib.config import ConfigLoader

from mylib.kit import Loutput

RESET = "\033[0m"
BOLD = "\033[1m"
FG_WHITE = "\033[37m"
FG_CYAN = "\033[36m"
FG_MAGENTA = "\033[35m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"


class MCPClient:
    def __init__(self):
        self.config = ConfigLoader()
        self.lo = Loutput()
        host = str(self.config.LLM_CONFIG.MCP_SERVER_HOST)
        port = str(self.config.LLM_CONFIG.MCP_SERVER_PORT)
        self.mcp_server_url = f"http://{host}:{port}"
        self.api_key = getattr(self.config.LLM_CONFIG, "DEEPSEEK_API_KEY", "")
        self.base_url = "https://api.deepseek.com/v1"
        self.available_tools = self._load_tools()
        self.conversation_history = []
    
    
    def _load_tools(self) -> List[Dict]:
        """从MCP服务器加载可用工具"""
        try:
            response = requests.get(f"{self.mcp_server_url}/tools")
            if response.status_code == 200:
                return response.json()["tools"]
            else:
                print("无法从MCP服务器加载工具")
                return []
        except Exception as e:
            print(f"连接MCP服务器错误: {e}")
            return []
    
    def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """调用MCP工具"""
        try:
            response = requests.post(
                f"{self.mcp_server_url}/tools/{tool_name}/call",
                json=arguments
            )
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                return {"error": f"HTTP错误: {response.status_code}"}
        except Exception as e:
            return {"error": f"调用工具错误: {str(e)}"}
    
    def chat_with_llm(self, message: str, is_tool_result: bool = False) -> str:
        """与LLM对话, 支持工具调用
        
        Args:
            message: 用户消息或工具结果
            is_tool_result: 是否为工具调用结果（影响消息角色）
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 系统提示词
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

        if not self.conversation_history:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        else:
            messages = [{"role": "system", "content": system_prompt}] + self.conversation_history
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
                
                if not is_tool_result:
                    self.conversation_history.append({"role": "user", "content": message})
                else:
                    self.conversation_history.append({"role": "user", "content": f"工具调用结果:\n{message}"})
                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                
                return assistant_message
            else:
                return f"API调用错误: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"LLM调用错误: {str(e)}"
    
    def process_user_request(self, user_input: str) -> str:
        """处理用户请求，支持连续工具调用
        
        Args:
            user_input: 用户输入的问题
            
        Returns:
            最终的回答结果
        """
        self.conversation_history = []
        
        llm_response = self.chat_with_llm(user_input, is_tool_result=False)
        self.lo.lput(f"\n[LLM 响应 #1] {llm_response[:200]}...", font_color="cyan")
        
        tool_call_round = 0
        max_rounds = 10
        
        while tool_call_round < max_rounds:
            if "TOOL_CALL_END" in llm_response:
                self.lo.lput("\n[工具调用结束] LLM 返回最终答案", font_color="yellow")
                final_answer = llm_response.replace("TOOL_CALL_END", "").strip()
                return final_answer
            
            if "TOOL_CALL:" not in llm_response:
                return llm_response
            
            try:
                tool_call_round += 1
                self.lo.lput(f"\n[工具调用轮次 #{tool_call_round}]", font_color="magenta", text_effects="bold")
                
                tool_call_json = llm_response.split("TOOL_CALL:")[1].strip()
                json_start = tool_call_json.find('{')
                json_end = tool_call_json.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    tool_call_json = tool_call_json[json_start:json_end]
                
                tool_call_data = json.loads(tool_call_json)
                
                tool_results = []
                for tool_call in tool_call_data.get("tool_calls", []):
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("arguments", {})
                    
                    self.lo.lput(f"  → 调用工具: {tool_name}", font_color="green")
                    self.lo.lput(f"    参数: {json.dumps(tool_args, ensure_ascii=False)}", font_color=37)
                    
                    result = self.call_tool(tool_name, tool_args)
                    tool_results.append({
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result": result
                    })

                    result_str = json.dumps(result, ensure_ascii=False)
                    result_preview = result_str[:150] + "..." if len(result_str) > 150 else result_str
                    self.lo.lput(f"    结果: {result_preview}", font_color="blue")
                
                tool_results_message = json.dumps(tool_results, indent=2, ensure_ascii=False)
                llm_response = self.chat_with_llm(tool_results_message, is_tool_result=True)
                self.lo.lput(f"\n[LLM 响应 #{tool_call_round + 1}] {llm_response[:200]}...", font_color="cyan")
                
            except json.JSONDecodeError as e:
                error_msg = f"工具调用 JSON 解析错误: {e}\n原始响应: {llm_response}"
                self.lo.lput(error_msg, font_color="red")
                return error_msg
            except Exception as e:
                error_msg = f"工具调用过程错误: {e}"
                self.lo.lput(error_msg, font_color="red")
                return error_msg
        
        return f"⚠️ 工具调用超过最大轮次限制 ({max_rounds})，最后响应:\n{llm_response}"

def main():
    client = MCPClient()
    client.lo.lput("=" * 50, text_effects="bold", font_color="green")
    client.lo.lput(f"MCP 客户端已启动 !", font_color="yellow")
    client.lo.lput("可用工具: ", font_color=37)
    for tool in client.available_tools:
        client.lo.lput(f"  - {tool['name']}: {tool['description']}")
    client.lo.lput("=" * 50, text_effects="bold", font_color="green")
    
    while True:
        try:
            client.lo.lput("(提示) 输入 'quit' 或 '退出' 来结束对话", text_effects=2)
            prompt = f"\n{BOLD}{BG_MAGENTA}{FG_WHITE} Sakurine {RESET}{BOLD}{FG_MAGENTA}: {RESET}"
            user_input = input(prompt).strip()

            if user_input.lower() in ['quit', '退出', 'exit']:
                client.lo.lput("再见 ~", font_color="yellow")
                break

            if not user_input:
                continue

            response = client.process_user_request(user_input)
            assistant_label = f"{BOLD}{BG_CYAN}{FG_WHITE} 恋 {RESET}{BOLD}{FG_CYAN}: {RESET}"
            client.lo.lput('\n')
            client.lo.lput(f"{assistant_label}{response}")

        except KeyboardInterrupt:
            client.lo.lput("再见 ~", font_color="yellow")
            break
        except Exception as e:
            print('\n')
            client.lo.lput(f"错误 {e}")

if __name__ == "__main__":
    main()
