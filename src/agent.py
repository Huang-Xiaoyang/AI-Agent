from pathlib import Path
import re
from langsmith import traceable
import tiktoken
import uuid
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_deepseek import ChatDeepSeek
import yaml
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, WORKDIR, MAX_AGENT_ITERATIONS, SKILL_DIR
from tools import edit_file, read_file, run_bash, update_todo, write_file
from tools.base import TODO
from tools.load_skill import SkillLoader, create_load_skill_tool
from tools.memory import AgentMemory
from tools.faiss_manager import FAISSManager


class CodingAgent:
    """Agent with FAISS + MySQL - 使用流式模式"""

    def __init__(self, user_id: str = "NaN", verbose: bool = True):
        # 用户标识
        self.user_id = user_id
        self.session_id = str(uuid.uuid4())[:8]
        
        # 初始化 LLM
        self.model = ChatDeepSeek(
            model=DEEPSEEK_MODEL,
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            temperature=0.7
        )
        
        # 初始化 Embedding 模型
        self.embed_model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
        
        # 初始化记忆模块
        self.memory = AgentMemory()
        
        # 初始化 FAISS 管理器
        self.faiss_manager = FAISSManager(
            mysql_conn=self.memory.mysql_conn,
            dimension=512,
            index_file=f"faiss_{user_id}.bin"
        )
        
        self.SKILL_LOADER = SkillLoader(SKILL_DIR)
        load_skill_tool = create_load_skill_tool(self.SKILL_LOADER)
        self.round_since_todo = 0
        
        # 工具列表
        self.tools = [run_bash, read_file, write_file, edit_file, update_todo, load_skill_tool]
        self.verbose = verbose
        self.messages = []
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # 加载长期记忆
        memory_context = self.memory.build_context_prompt(self.user_id, self.session_id)
        
        self.system_prompt = f"""You are a coding agent at {WORKDIR}. \
                Use the available tools to solve tasks. Act, don't explain excessively.

                {memory_context}

                You have access to these tools:
                - run_bash: Execute shell commands
                - read_file: Read file contents
                - write_file: Create or overwrite files
                - edit_file: Replace text in files
                - update_todo: Track your progress on multi-step tasks
                - load_skill: Use load_skill to access specialized knowledge before tackling unfamiliar topics.
                    Skills available:
                    {self.SKILL_LOADER.get_descriptions()}

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
    
    @staticmethod
    def split_by_tokens(text: str, max_tokens: int = 200) -> list:
        """按 Token 数拆分文本"""
        encoder = tiktoken.get_encoding("cl100k_base")
        tokens = encoder.encode(text)
        
        chunks = []
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = encoder.decode(chunk_tokens)
            chunks.append(chunk_text)
        
        return chunks
    
    def should_remember(self, query: str) -> bool:
        """用 LLM 判断是否需要记住"""
        prompt = f"""判断这句话是否包含用户的重要信息（偏好、事实、个人信息）。

        规则：
        - 用户明确说出"我喜欢/习惯/在/叫..." → 保存
        - 包含个人身份、工作、学习信息 → 保存  
        - 包含技术偏好、工具习惯 → 保存
        - 普通问答、闲聊、测试 → 不保存

        文本："{query}"

        只回答"是"或"否"："""
        response = self.model.invoke(prompt)
        return "是" in response.content
    
    @staticmethod
    def should_save_to_faiss(response: str, min_tokens: int = 30) -> bool:
        """基于 Token 数判断"""
        encoder = tiktoken.get_encoding("cl100k_base")
        token_count = len(encoder.encode(response))
        return token_count > min_tokens
    
    def search_and_format_memories(self, query: str, k: int = 5) -> str:
        """搜索相关记忆并格式化为字符串"""
        query_vec = self.embed_model.encode(query)
        results = self.faiss_manager.search(query_vec, self.user_id, k)
        
        if not results:
            return ""
        
        memory_text = "\n## 相关历史记忆\n"
        for i, r in enumerate(results, 1):
            memory_text += f"{i}. {r['text']}\n"
        
        return memory_text
    
    def _remember_fact(self, query: str, response: str):
        """自动保存重要信息"""
        keywords = ["我喜欢", "我偏好", "我习惯", "请记住", "记住", "我叫", "我的名字", "我在", "我实习", "我的岗位"]
        for keyword in keywords:
            if keyword in query:
                self.memory.save_user_memory(self.user_id, "fact", query.strip())
                if self.verbose:
                    print(f"💾 记住: {query[:50]}...")
                break

    @traceable 
    def run_streaming(self, query: str):
        """流式执行用户查询 - 实时显示每个步骤"""
        try:
            if not query or not query.strip():
                return "Please provide a valid query."
            
            # 保存用户消息到会话
            self.memory.add_to_session(self.session_id, "user", query)
            self.memory.archive_conversation(self.session_id, self.user_id, "user", query)
            
            # 1. 拆分用户消息并存入 FAISS
            chunks = self.split_by_tokens(query)
            vectors = self.embed_model.encode(chunks)
            
            for i, chunk in enumerate(chunks):
                if self.should_remember(chunk):
                    self.faiss_manager.add(chunk, vectors[i], self.user_id)
                    if self.verbose:
                        print(f"💾 已记忆: {chunk[:50]}...")
            
            # 2. 检索相关记忆
            memory_context = self.search_and_format_memories(query)
            
            # 3. 更新 system prompt 中的记忆上下文
            current_prompt = self.system_prompt
            if memory_context:
                if "## 相关历史记忆" in current_prompt:
                    import re
                    current_prompt = re.sub(r'## 相关历史记忆\n.*?(?=\n##|$)', memory_context, current_prompt, flags=re.DOTALL)
                else:
                    current_prompt = memory_context + "\n" + current_prompt
            
            # 4. 构建初始消息
            messages = [HumanMessage(content=query)]
            
            # 5. 流式执行 Agent
            final_answer = None
            
            for chunk in self.agent.stream(
                {"messages": messages},
                stream_mode="updates"
            ):
                for step_name, step_data in chunk.items():
                    if self.verbose:
                        print(f"\n{'='*50}")
                        print(f"📡 Step: {step_name}")
                        print(f"{'='*50}")
                    
                    # 获取最新的消息
                    if "messages" in step_data and step_data["messages"]:
                        last_msg = step_data["messages"][-1]
                        
                        # 根据步骤类型处理输出
                        if step_name == "model":
                            # 模型输出（可能是工具调用或最终答案）
                            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                                # 工具调用请求
                                for tool_call in last_msg.tool_calls:
                                    tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", "")
                                    tool_args = tool_call.get("args") if isinstance(tool_call, dict) else getattr(tool_call, "args", {})
                                    
                                    yield f"🤔 思考: 需要调用 {tool_name}\n"
                                    yield f"📝 参数: {tool_args}\n"
                            else:
                                # 最终答案
                                content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
                                if content:
                                    final_answer = content
                                    yield f"💡 {content}\n"
                        
                        elif step_name == "tools":
                            # 工具执行结果
                            if isinstance(last_msg, ToolMessage):
                                tool_name = getattr(last_msg, 'name', 'unknown')
                                content = last_msg.content
                                yield f"✅ 工具 {tool_name} 执行完成\n"
                                # 显示结果的前200个字符
                                result_preview = content[:200] + '...' if len(content) > 200 else content
                                yield f"📊 结果: {result_preview}\n"
                        
                        elif step_name == "agent":
                            # Agent 整体输出
                            content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
                            if content:
                                yield f"🤖 {content}\n"
            
            # 保存最终答案到记忆
            if final_answer:
                self.memory.add_to_session(self.session_id, "assistant", final_answer)
                self.memory.archive_conversation(self.session_id, self.user_id, "assistant", final_answer)
                
                # 保存到 FAISS
                chunks = self.split_by_tokens(final_answer)
                vectors = self.embed_model.encode(chunks)
                for i, chunk in enumerate(chunks):
                    if self.should_save_to_faiss(chunk):
                        self.faiss_manager.add(chunk, vectors[i], self.user_id)
                
                self._remember_fact(query, final_answer)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"Error: {str(e)}"
    
    @traceable 
    def run(self, query: str) -> str:
        """非流式执行（兼容旧接口）"""
        result_parts = []
        for chunk in self.run_streaming(query):
            result_parts.append(chunk)
            if self.verbose:
                print(chunk, end="", flush=True)
        return "".join(result_parts)
    
    def close(self):
        """关闭连接"""
        self.faiss_manager.save()
        self.memory.close()