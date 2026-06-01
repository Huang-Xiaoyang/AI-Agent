"""Agent 长期记忆模块 - Redis + MySQL"""

import json
import redis
import mysql.connector
from typing import List, Dict, Optional
from datetime import datetime


class AgentMemory:
    """Agent 记忆管理器"""
    
    def __init__(self):
        # Redis 连接
        self.redis_client = redis.Redis(
            host='127.0.0.1',
            port=6380,
            password='agent_memory',
            decode_responses=True
        )
        
        # MySQL 连接
        self.mysql_conn = mysql.connector.connect(
            host='127.0.0.1',
            port=3307,
            user='root',
            password='agent_memory',
            database='agent_memory',
            autocommit=True,
            charset='utf8mb4',
            use_unicode=True
        )
        
        self._check_connection()
    
    def _check_connection(self):
        """测试连接"""
        try:
            self.redis_client.ping()
            print("✅ Redis 连接成功")
        except Exception as e:
            print(f"❌ Redis 连接失败: {e}")
        
        try:
            cursor = self.mysql_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchall()
            cursor.close()
            print("✅ MySQL 连接成功")
        except Exception as e:
            print(f"❌ MySQL 连接失败: {e}")
    
    # ========== Redis 操作 ==========
    
    def get_session_context(self, session_id: str, limit: int = 20) -> List[Dict]:
        """获取当前会话历史"""
        history = self.redis_client.lrange(f"session:{session_id}", -limit, -1)
        messages = []
        for h in history:
            try:
                msg = json.loads(h)
                messages.append(msg)
            except:
                pass
        return messages
    
    def add_to_session(self, session_id: str, role: str, content: str):
        """添加消息到当前会话"""
        msg = {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        self.redis_client.rpush(f"session:{session_id}", json.dumps(msg))
        self.redis_client.expire(f"session:{session_id}", 3600)
    
    def clear_session(self, session_id: str):
        """清空会话"""
        self.redis_client.delete(f"session:{session_id}")
    
    # ========== MySQL 操作 ==========
    
    def save_user_memory(self, user_id: str, memory_type: str, content: str):
        """保存用户长期记忆"""
        cursor = self.mysql_conn.cursor()
        cursor.execute(
            "INSERT INTO user_memories (user_id, memory_type, content) VALUES (%s, %s, %s)",
            (user_id, memory_type, content)
        )
        cursor.close()
    
    def get_user_memories(self, user_id: str, memory_type: str = None) -> List[str]:
        """获取用户记忆"""
        cursor = self.mysql_conn.cursor()
        if memory_type:
            cursor.execute(
                "SELECT content FROM user_memories WHERE user_id = %s AND memory_type = %s",
                (user_id, memory_type)
            )
        else:
            cursor.execute(
                "SELECT content FROM user_memories WHERE user_id = %s",
                (user_id,)
            )
        results = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return results
    
    def archive_conversation(self, session_id: str, user_id: str, role: str, content: str):
        """存档对话到 MySQL"""
        cursor = self.mysql_conn.cursor()
        cursor.execute(
            "INSERT INTO conversation_archive (session_id, user_id, role, content) VALUES (%s, %s, %s, %s)",
            (session_id, user_id, role, content)
        )
        cursor.close()
    
    def build_context_prompt(self, user_id: str, session_id: str) -> str:
        """构建记忆上下文 Prompt"""
        context_parts = []
        memories = self.get_user_memories(user_id)
        if memories:
            context_parts.append("## 关于用户的信息")
            for mem in memories[-5:]:
                context_parts.append(f"- {mem}")
        return "\n".join(context_parts) if context_parts else ""
    
    def close(self):
        """关闭连接"""
        try:
            self.redis_client.close()
        except:
            pass
        try:
            self.mysql_conn.close()
        except:
            pass