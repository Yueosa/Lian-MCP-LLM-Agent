import argparse
import subprocess
import sys
from pathlib import Path
from mylib.mcp import MCPServer
from mylib.llm import llm_client


def main():
    parser = argparse.ArgumentParser(description="Run MCP server or LLM client for testing")
    parser.add_argument("mode", choices=["server", "client", "web"], help="运行模式: server / client / web")
    parser.add_argument("--host", help="server host", default=None)
    parser.add_argument("--port", type=int, help="server port", default=None)
    # 当前 LLM 客户端基于配置文件，不使用 provider 参数；保留占位以兼容旧命令
    parser.add_argument("--provider", help="llm provider (deprecated, 使用配置文件)", default=None)
    args = parser.parse_args()

    if args.mode == "server":
        server = MCPServer()
        # 注意: reload 参数在直接运行时不支持，建议使用 uvicorn 命令启用热重载
        server.run(host=args.host, port=args.port)
    elif args.mode == "client":
        # 直接运行交互式 LLM 客户端（读取 mylib/llm/llm_config.toml 配置）
        llm_client.main()
    elif args.mode == "web":
        # 启动 Streamlit Web UI
        web_client_path = Path(__file__).parent / "mylib" / "llm" / "llm_client_web.py"
        print(f"🚀 启动 Web UI: {web_client_path}")
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(web_client_path)])


if __name__ == "__main__":
    main()
