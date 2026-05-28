from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_deepseek import ChatDeepSeek

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, WORKDIR
from tools import edit_file, read_file, run_bash, update_todo, write_file
from tools.base import TODO


class CodingAgent:
    """编码助手 Agent"""

    def __init__(self, verbose: bool = True):
        # 初始化模型
        self.model = ChatDeepSeek(
            model=DEEPSEEK_MODEL,
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            temperature=0.7
        )

        self.round_since_todo = 0
        # 工具列表
        self.tools = [run_bash, read_file, write_file, edit_file, update_todo]
        self.verbose = verbose
        self.messages = []
        self.tool_map = {
            "run_bash": run_bash,
            "read_file": read_file,
            "write_file": write_file,
            "edit_file": edit_file,
            "update_todo": update_todo
        }
        self.system_prompt = f"""You are a coding agent at {WORKDIR}. \
Use the available tools to solve tasks. Act, don't explain excessively.

                You have access to these tools:
                - run_bash: Execute shell commands
                - read_file: Read file contents
                - write_file: Create or overwrite files
                - edit_file: Replace text in files
                - update_todo: Track your progress on multi-step tasks

                Always follow these rules:
                1. For multi-step tasks, use update_todo to track your progress
                2. Only one task can be marked as "in_progress" at a time
                3. After completing a task, mark it as "completed" and move to the next
                4. Be efficient - don't over-explain, just act
                5. Verify your work by reading files after writing/editing them

                Current todo list:
                {TODO.render()}
                """
        # 创建 agent
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt
        )

    def _execute_tool_calls(self, tool_calls: list) -> list:
        """执行工具调用并返回结果"""
        results = []
        used_todo = False

        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", "")

            if self.verbose:
                print(f"\n🔧 Calling tool: {tool_name}")
                print(f"📝 Arguments: {tool_args}")

            # 执行工具
            handler = self.tool_map.get(tool_name)
            if handler:
                try:
                    output = handler(**tool_args)
                    if self.verbose:
                        print(f"Result: {str(output)[:200]}")
                except Exception as e:
                    output = f"Error executing {tool_name}: {str(e)}"
                    if self.verbose:
                        print(f"Error: {output}")
            else:
                output = f"Unknown tool: {tool_name}"
                if self.verbose:
                    print(f"Unknown tool: {tool_name}")

            # 记录结果
            results.append(ToolMessage(
                content=str(output),
                tool_call_id=tool_id
            ))

            # 检查是否更新了 todo
            if tool_name == "update_todo":
                used_todo = True

        return results, used_todo

    def run(self, query: str) -> str:
        """执行用户查询"""
        try:
            # 确保 query 不为空
            if not query or not query.strip():
                return "Please provide a valid query."

            self.messages.append(HumanMessage(content=query))
            self.round_since_todo = 0

            while True:
                # 构建完整的消息列表（系统消息 + 历史 + 当前）
                full_messages = [SystemMessage(content=self.system_prompt)] + self.messages

                """
                if self.verbose:
                    print(f"\n[DEBUG] Total messages: {len(full_messages)}")
                    print(f"[DEBUG] History length: {len(self.messages)}")
                """

                # 调用 agent，传递完整消息
                result = self.agent.invoke({
                    "messages": full_messages
                })

                tool_calls = []
                # 提取输出 - 处理 AIMessage 对象
                if "messages" in result:
                    last_msg = result["messages"][-1]

                    if isinstance(last_msg, AIMessage):
                        response_content = last_msg.content
                        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                            tool_calls = last_msg.tool_calls
                    elif isinstance(last_msg, dict):
                        if last_msg.get("role") == "assistant":
                            response_content = last_msg.get("content")
                            tool_calls = last_msg.get("tool_calls", [])
                if not tool_calls:
                    if response_content:
                        # 添加助手回复到历史
                        self.messages.append(AIMessage(content=response_content))
                        return response_content
                    else:
                        return "Task completed."

                # 执行工具调用
                tool_results, used_todo = self._execute_tool_calls(tool_calls)
                # 更新 todo 计数器
                self.round_since_todo = 0 if used_todo else self.round_since_todo + 1
                # 添加工具结果到消息历史
                self.messages.extend(tool_results)
                # 检查是否需要提醒更新 todo
                if self.round_since_todo >= 3:
                    reminder = ToolMessage(
                        content="<reminder>Update your todos to track progress.</reminder>",
                        tool_call_id="reminder"
                    )
                    self.messages.append(reminder)
                    self.round_since_todo = 0
                # 如果有响应内容，也添加到历史
                if response_content:
                    self.messages.append(AIMessage(content=response_content))



        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Error in agent execution: {str(e)}"
