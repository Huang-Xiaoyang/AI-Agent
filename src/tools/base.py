from pathlib import Path
from config import WORKDIR

def safe_path(p: str) -> Path:
    """确保路径不会逃逸出工作目录"""
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path

class TodoManager:
    """待办事项管理器"""
    
    def __init__(self):
        self.items = []
    
    def render(self) -> str:
        """渲染当前待办列表"""
        if not self.items:
            return "No todos."
        
        lines = []
        for item in self.items:
            marker = {
                "pending": "[ ]", 
                "in_progress": "[>]", 
                "completed": "[x]"
            }[item["status"]]
            lines.append(f"{marker} #{item['id']}: {item['text']}")
        
        done = sum(1 for t in self.items if t["status"] == "completed")
        lines.append(f"\n({done}/{len(self.items)} completed)")
        return "\n".join(lines)
    
    def update(self, items: list) -> str:
        """更新待办列表"""
        validated, in_progress_count = [], 0
        
        for item in items:
            status = item.get("status", "pending")
            if status == "in_progress":
                in_progress_count += 1
            validated.append({
                "id": item["id"], 
                "text": item["text"], 
                "status": status
            })
        
        if in_progress_count > 1:
            raise ValueError("Only one task can be in progress!")
        
        self.items = validated
        return self.render()

TODO = TodoManager()