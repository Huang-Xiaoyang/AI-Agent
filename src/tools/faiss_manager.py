"""FAISS 管理器 - 使用 MySQL 存储映射"""
import os
import faiss
import numpy as np
from typing import List, Dict, Optional


class FAISSManager:
    """FAISS 索引 + MySQL 映射管理器"""
    def __init__(self, mysql_conn, dimension: int = 512, index_file: str = "faiss_index.bin"):
        self.mysql_conn = mysql_conn
        self.dimension = dimension
        self.index_file = index_file
        
        # 加载或创建 FAISS 索引
        if os.path.exists(index_file):
            self.index = faiss.read_index(index_file)
            print(f"✅ 加载 FAISS 索引，共 {self.index.ntotal} 条")
        else:
            self.index = faiss.IndexFlatL2(dimension)
            print("✅ 创建新的 FAISS 索引")
        
        self._init_table()
    
    def _init_table(self):
        """初始化映射表"""
        cursor = self.mysql_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS faiss_mapping (
                id INT AUTO_INCREMENT PRIMARY KEY,
                faiss_position INT NOT NULL,
                text TEXT NOT NULL,
                user_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_faiss_pos (faiss_position),
                INDEX idx_user_id (user_id)
            )
        """)
        self.mysql_conn.commit()
        cursor.close()
    
    def add(self, text: str, embedding: np.ndarray, user_id: str = "NaN") -> int:
        """添加文本和向量"""
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        embedding = embedding.astype(np.float32)
        
        position = self.index.ntotal
        self.index.add(embedding)
        
        cursor = self.mysql_conn.cursor()
        cursor.execute(
            "INSERT INTO faiss_mapping (faiss_position, text, user_id) VALUES (%s, %s, %s)",
            (position, text, user_id)
        )
        self.mysql_conn.commit()
        cursor.close()
        
        return position
    
    def search(self, query_vec: np.ndarray, user_id: str = "NaN", k: int = 5) -> List[Dict]:
        """搜索相关记忆"""
        if query_vec.ndim == 1:
            query_vec = query_vec.reshape(1, -1)
        query_vec = query_vec.astype(np.float32)
        
        distances, positions = self.index.search(query_vec, k)
        
        results = []
        cursor = self.mysql_conn.cursor()
        
        for pos, dist in zip(positions[0], distances[0]):
            if pos != -1:
                cursor.execute(
                    "SELECT text FROM faiss_mapping WHERE faiss_position = %s AND user_id = %s",
                    (int(pos), user_id)
                )
                row = cursor.fetchone()
                if row:
                    results.append({
                        "text": row[0],
                        "position": int(pos),
                        "distance": float(dist),
                        "similarity": 1 / (1 + float(dist))
                    })
        
        cursor.close()
        return results
    
    def get_all_memories(self, user_id: str = "NaN", limit: int = 100) -> List[Dict]:
        """获取用户所有记忆"""
        cursor = self.mysql_conn.cursor()
        cursor.execute(
            "SELECT faiss_position, text, created_at FROM faiss_mapping WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        cursor.close()
        return [{"position": r[0], "text": r[1], "created_at": r[2]} for r in rows]
    
    def save(self, filepath: str = None):
        """保存 FAISS 索引"""
        if filepath is None:
            filepath = self.index_file
        faiss.write_index(self.index, filepath)
        print(f"💾 已保存 FAISS 索引到 {filepath}，共 {self.index.ntotal} 条")
    
    @property
    def total(self) -> int:
        return self.index.ntotal