from langchain.tools import tool
from tools.base import safe_path

@tool
def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace exact text in file."""
    try:
        fp = safe_path(path)
        content = fp.read_text(encoding='utf-8', errors='replace')
        
        if old_text not in content:
            return f"Error: Text not found in {path}"
        
        # 只替换第一次出现
        fp.write_text(content.replace(old_text, new_text, 1), encoding='utf-8')
        return f"Edited {path}"
    except FileNotFoundError:
        return f"Error: File not found - {path}"
    except Exception as e:
        return f"Error: {e}"