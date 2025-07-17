import json
import os
from typing import List


class TaskModel:
    """Model handling task data and persistence."""

    SAVE_FILE = os.path.expanduser("~/.micromanager_tasks.json")

    def __init__(self) -> None:
        self.task: str = ""
        self.steps: List[str] = []
        self.current_index: int = 0
        self.load()

    def load(self) -> None:
        """Load task data from JSON file if it exists."""
        if os.path.exists(self.SAVE_FILE):
            try:
                with open(self.SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.task = data.get("task", "")
                self.steps = data.get("steps", [])
                self.current_index = data.get("current_index", 0)
            except (OSError, json.JSONDecodeError):
                pass

    def save(self) -> None:
        """Save current task data to JSON file."""
        data = {
            "task": self.task,
            "steps": self.steps,
            "current_index": self.current_index,
        }
        try:
            with open(self.SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass

    def reset(self, task: str, steps: List[str]) -> None:
        """Reset to a new task and micro steps."""
        self.task = task
        self.steps = steps
        self.current_index = 0
        self.save()

    @property
    def current_step(self) -> str:
        """Return current step text."""
        if 0 <= self.current_index < len(self.steps):
            return self.steps[self.current_index]
        return ""

    def mark_done(self) -> None:
        """Mark current step as done and advance."""
        if self.current_index < len(self.steps) - 1:
            self.current_index += 1
        else:
            self.current_index = len(self.steps)
        self.save()

