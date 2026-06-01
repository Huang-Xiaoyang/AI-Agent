# Learn-Agent

基于 LangChain + DeepSeek 的 AI Agent，具备工具调用、文件操作、命令执行、任务跟踪、长期记忆（FAISS + MySQL + Redis）能力。

## 功能特性

- **智能对话** — 基于 DeepSeek 大模型的多轮对话与推理
- **Bash 命令执行** — 安全执行 Shell 命令，内置危险命令拦截
- **文件操作** — 读取、创建、编辑文件，支持路径安全校验
- **任务管理** — 多步骤任务自动拆分与进度跟踪
- **技能系统** — 按需加载专业领域知识（Skill Loader）
- **长期记忆** — FAISS + MySQL + Redis 三层记忆架构
- **语义检索** — 基于 Embedding 的历史对话语义搜索
- **安全防护** — 路径遍历攻击防护、危险命令黑名单、输出长度限制

## 架构

```
Learn-Agent/
    ├── docker-compose.yml # Docker 编排配置
    ├── init.sql # 数据库初始化脚本
    ├── .env.example # 环境变量模板
    ├── requirements.txt # Python 依赖
    ├── README.md # 项目文档
    └── src/
        ├── main.py
        ├── agent.py
        ├── config.py
        └── tools/
            ├── init.py
            ├── base.py
            ├── bash.py
            ├── file_read.py
            ├── file_write.py
            ├── file_edit.py
            ├── todo.py
            ├── load_skill.py
            ├── memory.py
            └── faiss_manager.py
```

## 记忆架构

| 层级 | 存储 | 用途 | 时效 |
|------|------|------|------|
| L1 | Redis | 当前会话上下文 | 1小时 |
| L2 | FAISS | 语义记忆（相似话题检索） | 持久 |
| L3 | MySQL | 结构化记忆（事实、偏好、对话存档） | 持久 |

## 工具清单

| 工具 | 功能 | 安全机制 |
|------|------|----------|
| `run_bash` | 执行 Shell 命令 | 危险命令黑名单、超时 120s、输出截断 |
| `read_file` | 读取文件内容 | 路径逃逸防护、行数限制 |
| `write_file` | 创建/覆盖文件 | 路径逃逸防护、自动创建父目录 |
| `edit_file` | 精确替换文本 | 路径逃逸防护、仅替换首次匹配 |
| `update_todo` | 更新任务列表 | 限制仅一个进行中任务 |
| `load_skill` | 加载专业技能 | 按需加载 SKILL.md 文档 |

## 快速开始

### 1. 环境要求

- Python 3.11+
- DeepSeek API Key
- Docker（用于 MySQL + Redis）


### 2. 安装

```bash
git clone git@github.com:Huang-Xiaoyang/Learn-Agent.git
cd Learn-Agent
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 配置

复制环境变量模板并填入你的 API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 4. 运行

```bash
cd src
python main.py
```

交互示例：

```
🤖 DeepSeek Coding Agent Started
📁 Working directory: /path/to/project
👤 User: username
💡 Type 'exit' or 'q' to quit
📝 Type 'todo' to view current tasks
🧠 Type 'memories' to see FAISS memories
🗑️  Type 'clear' to clear current session

user >> 在当前目录创建一个 Python 快速排序实现
assistant >> 已创建 quicksort.py，包含快速排序函数及测试用例...

user >> todo
📋 Current tasks:
[ ] #1: 创建 quicksort.py
[x] #2: 编写测试用例

(1/2 completed)
```

## 配置项

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEEPSEEK_API_KEY` | — | DeepSeek API 密钥（必填） |
| `DEEPSEEK_BASE_URL` | — | DeepSeek API 地址 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 使用的模型名称 |
| `MAX_TOOL_OUTPUT_LENGTH` | `50000` | 工具输出最大字符数 |
| `BASH_TIMEOUT` | `120` | Bash 命令超时时间（秒） |
| `MAX_AGENT_ITERATIONS` | `15` | Agent 最大迭代轮数 |

## 安全设计

- **路径安全**：所有文件操作通过 `safe_path()` 校验，确保不会逃逸出工作目录
- **命令拦截**：`run_bash` 内置黑名单，阻止 `rm -rf /`、`sudo`、`shutdown`、`reboot` 等危险命令
- **输出截断**：工具输出超过 `MAX_TOOL_OUTPUT_LENGTH` 自动截断，防止上下文溢出
- **任务约束**：同一时刻仅允许一个任务处于 `in_progress` 状态

## 技术栈
- **LangChain / LangGraph** — LLM 应用框架与 Agent 执行引擎
- **DeepSeek** — 大语言模型
- **FAISS** — 向量检索引擎
- **Sentence Transformers** — Embedding 模型（BAAI/bge-small-zh）
- **Redis** — 短期记忆缓存
- **MySQL** — 长期结构化存储
- **tiktoken** — Token 计数
- **Pydantic** — 数据校验

## 使用说明

克隆项目后，只需要：

```bash
# 1. 启动所有依赖（MySQL + Redis + 可视化工具）
docker-compose up -d

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env 填入 API Key

# 4. 运行
cd src && python main.py

## License

[MIT](LICENSE)
