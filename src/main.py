#!/usr/bin/env python3
"""DeepSeek Coding Agent - 主入口"""

from agent import CodingAgent
from config import WORKDIR


def main():
    """主函数"""
    print("\033[32m🤖 DeepSeek Coding Agent Started\033[0m")
    print(f"📁 Working directory: {WORKDIR}")
    print("💡 Type 'exit' or 'q' to quit")
    print("📝 Type 'todo' to view current tasks\n")

    # 初始化 agent
    agent = CodingAgent(verbose=False)
    # 交互循环
    while True:
        try:
            query = input("\033[36muser >> \033[0m").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Goodbye!")
            break
        # 退出命令
        if query.lower() in ("q", "exit", "quit"):
            print("👋 Goodbye!")
            break
        # 查看待办
        if query.lower() == "todo":
            from tools.base import TODO
            print(f"\n📋 Current tasks:\n{TODO.render()}\n")
            continue
        # 跳过空输入
        if not query:
            continue
        # 执行 agent
        print()
        response = agent.run(query)
        print(f"\n\033[32massistant >>\033[0m {response}\n")

if __name__ == "__main__":
    main()
