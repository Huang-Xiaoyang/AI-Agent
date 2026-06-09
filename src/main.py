#!/usr/bin/env python3
"""DeepSeek Coding Agent - 主入口 with FAISS"""
import os
from dotenv import load_dotenv
from langsmith import traceable
from agent import CodingAgent
from config import WORKDIR

load_dotenv()

os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING", "false")
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGSMITH_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "default-project")

def main():
    """主函数"""
    print("\033[32m🤖 DeepSeek Coding Agent Started\033[0m")
    print(f"📁 Working directory: {WORKDIR}")
    
    user_id = "NaN"
    print(f"👤 User: {user_id}")
    
    print("💡 Type 'exit' or 'q' to quit")
    print("📝 Type 'todo' to view current tasks")
    print("🧠 Type 'memories' to see FAISS memories")
    print("🗑️  Type 'clear' to clear current session\n")

    agent = CodingAgent(user_id=user_id, verbose=False)
    
    try:
        while True:
            try:
                query = input("\033[36muser >> \033[0m").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 Goodbye!")
                break
            
            if query.lower() in ("q", "exit", "quit"):
                print("👋 Goodbye!")
                break
            
            if query.lower() == "todo":
                from tools.base import TODO
                print(f"\n📋 Current tasks:\n{TODO.render()}\n")
                continue
            
            if query.lower() == "memories":
                memories = agent.faiss_manager.get_all_memories(agent.user_id, limit=20)
                if memories:
                    print("\n📝 FAISS 记忆:")
                    for i, m in enumerate(memories, 1):
                        print(f"  {i}. {m['text'][:100]}")
                else:
                    print("\n📝 暂无记忆\n")
                continue
            
            if query.lower() == "clear":
                agent.memory.clear_session(agent.session_id)
                print("🗑️ 当前会话已清空\n")
                continue
            
            if not query:
                continue
            
            print()
            response = agent.run(query)
            print(f"\n\033[32massistant >>\033[0m {response}\n")
    finally:
        agent.close()


if __name__ == "__main__":
    main()