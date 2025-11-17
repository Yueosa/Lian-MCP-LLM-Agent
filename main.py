import argparse
from mylib import mcp


def main():
    parser = argparse.ArgumentParser(description="Run MCP server or LLM client for testing")
    parser.add_argument("mode", choices=["server", "client"], help="运行模式: server 或 client")
    parser.add_argument("--host", help="server host", default=None)
    parser.add_argument("--port", type=int, help="server port", default=None)
    parser.add_argument("--provider", help="llm provider (openai/zhipu/deepseek/moonshot)", default=None)
    args = parser.parse_args()

    if args.mode == "server":
        mcp.start_mcp_server(host=args.host, port=args.port, reload=True)
    elif args.mode == "client":
        mcp.run_llm_client(provider=args.provider)


if __name__ == "__main__":
    main()
