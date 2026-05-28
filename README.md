# Learn-Agent

基于 LangChain + DeepSeek 的 AI 编码助手 Agent，具备工具调用、文件操作、命令执行和任务跟踪能力。

## 功能特性

- **智能对话** — 基于 DeepSeek 大模型的多轮对话与推理
- **Bash 命令执行** — 安全执行 Shell 命令，内置危险命令拦截
- **文件操作** — 读取、创建、编辑文件，支持路径安全校验
- **任务管理** — 多步骤任务自动拆分与进度跟踪
- **安全防护** — 路径遍历攻击防护、危险命令黑名单、输出长度限制

## 架构

```
src/
├── main.py              # 交互式命令行入口
├── agent.py             # Agent 核心逻辑（工具调用循环）
├── config.py            # 全局配置管理
└── tools/
    ├── base.py          # safe_path 路径安全 + TodoManager
    ├── bash.py          # Shell 命令执行工具
    ├── file_read.py     # 文件读取工具
    ├── file_write.py    # 文件写入工具
    ├── file_edit.py     # 文件编辑工具（精确替换）
    └── todo.py          # 待办事项管理工具
```

## 工具清单

| 工具 | 功能 | 安全机制 |
|------|------|----------|
| `run_bash` | 执行 Shell 命令 | 危险命令黑名单、超时 120s、输出截断 |
| `read_file` | 读取文件内容 | 路径逃逸防护、行数限制 |
| `write_file` | 创建/覆盖文件 | 路径逃逸防护、自动创建父目录 |
| `edit_file` | 精确替换文本 | 路径逃逸防护、仅替换首次匹配 |
| `update_todo` | 更新任务列表 | 限制仅一个进行中任务 |

## 快速开始

### 1. 环境要求

- Python 3.11+
- DeepSeek API Key

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
💡 Type 'exit' or 'q' to quit
📝 Type 'todo' to view current tasks

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

- **LangChain** — LLM 应用框架与工具调用
- **LangGraph** — Agent 执行引擎
- **DeepSeek** — 大语言模型
- **Pydantic** — 数据校验
- **tiktoken** — Token 计数

## License

[MIT](LICENSE)
