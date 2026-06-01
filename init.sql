-- 用户记忆表
CREATE TABLE IF NOT EXISTS user_memories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    memory_type VARCHAR(50) DEFAULT 'fact',
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
);

-- 会话存档表
CREATE TABLE IF NOT EXISTS conversation_archive (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id)
);

-- 知识库表
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_name VARCHAR(255) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- FAISS 映射表
CREATE TABLE IF NOT EXISTS faiss_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    faiss_position INT NOT NULL,
    text TEXT NOT NULL,
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_faiss_pos (faiss_position),
    INDEX idx_user_id (user_id)
);