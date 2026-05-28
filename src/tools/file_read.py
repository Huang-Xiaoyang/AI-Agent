from langchain.tools import tool
from tools.base import safe_path
from config import MAX_TOOL_OUTPUT_LENGTH

@tool
def read_file(path: str, limit: int = None) -> str:
    """Read file contents."""
    try:
        fp = safe_path(path)
        text = fp.read_text(encoding='utf-8', errors='replace')
        lines = text.splitlines()
        
        if limit and limit < len(lines):
            lines = lines[:limit]
        
        return "\n".join(lines)[:MAX_TOOL_OUTPUT_LENGTH]
    except FileNotFoundError:
        return f"Error: File not found - {path}"
    except Exception as e:
        return f"Error: {e}"