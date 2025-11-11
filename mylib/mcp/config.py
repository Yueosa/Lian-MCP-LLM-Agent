import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MCP 服务器配置
    MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8000"))
    
    # OpenAI 配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # 工具配置
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    REQUEST_TIMEOUT = 30
