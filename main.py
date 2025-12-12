import sys
import argparse
import subprocess
from pathlib import Path

from mylib.mcp import MCPServer
from mylib.llm import llm_client

def main():
    parser = argparse.ArgumentParser(description="Run MCP server or LLM/Agent clients")
    parser.add_argument(
        "mode",
        choices=[
            "server",  # MCP server
            "client",  # 旧版交互式 LLM 客户端
            "web",     # 旧版 MCP Web UI
            "agent",   # 新版 Multi-Agent Web UI
        ],
        help="运行模式",
    )
    parser.add_argument("message", nargs="?", help="可选消息参数", default=None)
    parser.add_argument("--host", help="server host", default=None)
    parser.add_argument("--port", type=int, help="server port", default=None)
    args = parser.parse_args()

    if args.mode == "server":
        print("🚀 启动 MCP Server...")
        server = MCPServer()
        server.run(host=args.host, port=args.port)
        
    elif args.mode == "client":
        print("🚀 启动 LLM Client CLI...")
        llm_client.main()
        
    elif args.mode == "web":
        web_client_path = Path(__file__).parent / "mylib" / "llm" / "llm_client_web.py"
        print(f"🚀 启动旧版 MCP Web UI: {web_client_path}")
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(web_client_path)])
        
    elif args.mode == "agent":
        agent_web_path = Path(__file__).parent / "mylib" / "core" / "agent_web.py"
        print(f"🚀 启动新版 Multi-Agent Web UI: {agent_web_path}")
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(agent_web_path)])
        
    else:
        raise SystemExit(f"未知模式: {args.mode}")

if __name__ == "__main__":
    main()
