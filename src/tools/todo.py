from langchain.tools import tool

from tools.base import TODO


@tool
def update_todo(items: list) -> str:
    """Update task list. Track progress on multi-step tasks.

    Args:
        items: List of tasks with id, text, and status (pending/in_progress/completed)
               Example: [
                   {"id": "1", "text": "Read file", "status": "pending"},
                   {"id": "2", "text": "Edit file", "status": "in_progress"}
               ]
    """
    try:
        return TODO.update(items)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"
