from pathlib import Path
import re

from langchain.tools import tool
import yaml


class SkillLoader:
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills = {}
        self._load_all()

    def _load_all(self):
        if not self.skills_dir.exists():
            print(f"无skill, {self.skills_dir}")
            return
        for f in sorted(self.skills_dir.rglob("SKILL.md")):
            text = f.read_text(encoding="UTF-8")
            meta, body = self._parse_frontmatter(text)
            name = meta.get("name", f.parent.name)
            self.skills[name] = {"meta": meta, "body": body, "path": str(f)}

    def _parse_frontmatter(self, text: str) -> tuple:
        """Parse YAML frontmatter between --- delimiters."""
        match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
        if not match:
            return {}, text
        try:
            meta = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            meta = {}
        return meta, match.group(2).strip()

    def get_descriptions(self) -> str:
        """Layer 1: short descriptions for the system prompt."""
        if not self.skills:
            return "(no skills available)"
        lines = []
        for name, skill in self.skills.items():
            desc = skill["meta"].get("description", "No description")
            tags = skill["meta"].get("tags", "")
            line = f"  - {name}: {desc}"
            if tags:
                line += f" [{tags}]"
            lines.append(line)
        return "\n".join(lines)

    def get_content(self, name: str) -> str:
        """Layer 2: full skill body."""
        skill = self.skills.get(name)
        if not skill:
            return f"Error: Unknown skill '{name}'. Available: {', '.join(self.skills.keys())}"
        return f"<skill name=\"{name}\">\n{skill['body']}\n</skill>"

def create_load_skill_tool(skill_loader: SkillLoader):
    """创建一个绑定特定 SkillLoader 实例的 load_skill 工具"""
    
    @tool
    def load_skill(skill_name: str) -> str:
        """
        Load a skill's full documentation. Use this when:
        - The user asks to build/create/design an agent (load "agent-builder")
        - You need specialized domain knowledge for a task
        - The user mentions "agent", "assistant", "AI system", "agentic pattern"
        - You're uncertain about best practices in a specific area
        
        Available skills are listed in the system prompt.
        
        Args:
            skill_name: The name of the skill to load (e.g., 'agent-builder', 'python-debugging')
        
        Returns:
            Full skill documentation as a string
        """
        return skill_loader.get_content(skill_name)
    
    return load_skill