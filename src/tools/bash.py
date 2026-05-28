import subprocess
from langchain.tools import tool
from config import BASH_TIMEOUT, MAX_TOOL_OUTPUT_LENGTH

@tool
def run_bash(command: str) -> str:
    """Run a shell command."""
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    
    try:
        r = subprocess.run(
            command, 
            shell=True, 
            cwd=None,
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            errors='replace',  # 替换无法解码的字符
            timeout=BASH_TIMEOUT
        )
        
        # 处理 None 值
        stdout = r.stdout if r.stdout is not None else ""
        stderr = r.stderr if r.stderr is not None else ""
        out = (stdout + stderr).strip()
        
        return out[:MAX_TOOL_OUTPUT_LENGTH] if out else "(no output)"
        
    except subprocess.TimeoutExpired:
        return f"Error: Timeout ({BASH_TIMEOUT}s)"
    except (FileNotFoundError, OSError) as e:
        return f"Error: {e}"