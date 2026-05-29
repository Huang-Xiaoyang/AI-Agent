import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

# DeepSeek 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 工作目录
WORKDIR = Path.cwd()

# Agent 配置
MAX_TOOL_OUTPUT_LENGTH = 50000
BASH_TIMEOUT = 120
MAX_AGENT_ITERATIONS = 15
SKILL_DIR = WORKDIR/"src"/"skills"