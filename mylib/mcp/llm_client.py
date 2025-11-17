import json
import requests
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

# ANSI 颜色/样式常量
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
UNDERLINE = "\033[4m"

FG_RED = "\033[31m"
FG_GREEN = "\033[32m"
FG_YELLOW = "\033[33m"
FG_BLUE = "\033[34m"
FG_MAGENTA = "\033[35m"
FG_CYAN = "\033[36m"
FG_WHITE = "\033[37m"

BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"

class ModelProvider(Enum):
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ZHIPU = "zhipu"
    MOONSHOT = "moonshot"

class MCPClient:
    def __init__(self, mcp_server_url: str = "http://localhost:8080", provider: ModelProvider = ModelProvider.DEEPSEEK):
        self.mcp_server_url = mcp_server_url
        self.provider = provider
        self.available_tools = self._load_tools()
        self._setup_client()
    
    def _setup_client(self):
        """根据提供商设置客户端"""
        if self.provider == ModelProvider.DEEPSEEK:
            self.api_key = os.getenv("DEEPSEEK_API_KEY")
            self.base_url = "https://api.deepseek.com/v1"
        elif self.provider == ModelProvider.OPENAI:
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = "https://api.openai.com/v1"
        elif self.provider == ModelProvider.ZHIPU:
            self.api_key = os.getenv("ZHIPU_API_KEY")
            self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        elif self.provider == ModelProvider.MOONSHOT:
            self.api_key = os.getenv("MOONSHOT_API_KEY")
            self.base_url = "https://api.moonshot.cn/v1"
    
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
                f"{self.mcp_server_url}/tools/{tool_name}",
                json=arguments
            )
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                return {"error": f"HTTP错误: {response.status_code}"}
        except Exception as e:
            return {"error": f"调用工具错误: {str(e)}"}
    
    def get_model_name(self) -> str:
        """根据提供商返回模型名称"""
        model_map = {
            ModelProvider.DEEPSEEK: "deepseek-chat",
            ModelProvider.OPENAI: "gpt-3.5-turbo",
            ModelProvider.ZHIPU: "glm-4",
            ModelProvider.MOONSHOT: "moonshot-v1-8k"
        }
        return model_map.get(self.provider, "deepseek-chat")
    
    def chat_with_llm(self, message: str) -> str:
        """与LLM对话，支持工具调用"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        messages = [
            {
                "role": "system",
                "content": f"""你是一个AI助手，可以调用各种工具来帮助用户完成任务。
                
                可用工具:
                {json.dumps(self.available_tools, indent=2, ensure_ascii=False)}
                
                请根据用户需求选择合适的工具，如果需要调用工具，请按照以下格式响应：
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
                
                工具调用完成后，我会给你结果，然后请你基于结果继续回答用户问题。"""
            },
            {
                "role": "user",
                "content": message
            }
        ]
        
        payload = {
            "model": self.get_model_name(),
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        
        # 智谱AI的API格式略有不同
        if self.provider == ModelProvider.ZHIPU:
            # 可能需要调整payload格式
            pass
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"API调用错误: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"LLM调用错误: {str(e)}"
    
    def process_user_request(self, user_input: str) -> str:
        """处理用户请求，包括工具调用"""
        
        # 第一步：获取LLM的响应
        llm_response = self.chat_with_llm(user_input)
        print(f"LLM初始响应: {llm_response}")
        
        # 检查是否需要工具调用
        if llm_response and "TOOL_CALL:" in llm_response:
            try:
                # 提取工具调用信息
                tool_call_json = llm_response.split("TOOL_CALL:")[1].strip()
                tool_call_data = json.loads(tool_call_json)
                
                # 执行工具调用
                tool_results = []
                for tool_call in tool_call_data["tool_calls"]:
                    print(f"调用工具: {tool_call['name']} 参数: {tool_call['arguments']}")
                    result = self.call_tool(tool_call["name"], tool_call["arguments"])
                    tool_results.append({
                        "tool": tool_call["name"],
                        "result": result
                    })
                
                # 将工具结果发送给LLM进行进一步处理
                follow_up_message = f"""
                用户原始请求: {user_input}
                
                工具调用结果:
                {json.dumps(tool_results, indent=2, ensure_ascii=False)}
                
                请基于以上工具执行结果来回答用户的问题。
                """
                
                final_response = self.chat_with_llm(follow_up_message)
                return final_response
                
            except json.JSONDecodeError as e:
                return f"工具调用格式错误: {e}"
            except Exception as e:
                return f"工具调用过程错误: {e}"
        else:
            # 不需要工具调用，直接返回LLM响应
            return llm_response

def main():
    """主对话循环"""
    # 使用DeepSeek
    client = MCPClient(provider=ModelProvider.DEEPSEEK)
    # 欢迎横幅（简洁、带色）
    print(BOLD + FG_GREEN + "=" * 50 + RESET)
    print(FG_YELLOW + f"MCP 客户端已启动 ({client.provider.value})!" + RESET)
    print(FG_WHITE + "可用工具:" + RESET)
    for tool in client.available_tools:
        # 工具列表保持普通样式（不强调）
        print(f"  - {tool['name']}: {tool['description']}")
    print(BOLD + FG_GREEN + "=" * 50 + RESET)
    
    while True:
        try:
            # 每轮都显示退出提示（低亮）
            print(DIM + "(提示) 输入 'quit' 或 '退出' 来结束对话" + RESET)
            # 带颜色的输入提示：高亮显示名称 Sakurine
            prompt = f"\n{BOLD}{BG_MAGENTA}{FG_WHITE} Sakurine {RESET}{BOLD}{FG_MAGENTA}: {RESET}"
            user_input = input(prompt).strip()

            if user_input.lower() in ['quit', '退出', 'exit']:
                print(FG_YELLOW + "再见!" + RESET)
                break

            if not user_input:
                continue

            # 处理用户请求
            response = client.process_user_request(user_input)
            # 输出助手回复，强调名字“恋”并使用不同配色
            assistant_label = f"{BOLD}{BG_CYAN}{FG_WHITE} 恋 {RESET}{BOLD}{FG_CYAN}: {RESET}"
            print(f"\n{assistant_label}{response}")

        except KeyboardInterrupt:
            print("\n\n" + FG_YELLOW + "再见!" + RESET)
            break
        except Exception as e:
            # 错误信息保持普通样式以便阅读
            print(f"\n错误: {e}")

if __name__ == "__main__":
    main()
