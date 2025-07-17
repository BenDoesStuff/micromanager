from __future__ import annotations

import os
from typing import List

import openai

from .model import TaskModel
from .view import TaskView


class TaskController:
    """Controller connecting the model and the view."""

    def __init__(self, model: TaskModel, view: TaskView) -> None:
        self.model = model
        self.view = view

        # Connect view signals
        self.view.submit_task.connect(self.on_submit_task)
        self.view.mark_done.connect(self.on_mark_done)
        self.view.toggle_history.connect(self.on_toggle_history)

        self.refresh()

    def on_submit_task(self, task: str) -> None:
        steps = self.generate_microsteps(task)
        self.model.reset(task, steps)
        self.refresh()

    def on_mark_done(self) -> None:
        self.model.mark_done()
        self.refresh()

    def on_toggle_history(self) -> None:
        self.view.toggle_history_view()
        self.refresh_history()

    def refresh(self) -> None:
        self.view.update_step(self.model.current_step)
        self.view.update_progress(self.model.current_index, len(self.model.steps))
        self.refresh_history()

    def refresh_history(self) -> None:
        self.view.update_history(self.model.steps, self.model.current_index)

    def generate_microsteps(self, task: str) -> List[str]:
        """Generate microsteps using OpenAI API or fallback."""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                openai.api_key = api_key
                prompt = (
                    "Break the following task into 5-8 short steps.\n" f"Task: {task}\n" "Steps:")
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                )
                text = response.choices[0].message["content"]
                steps = [line.strip("- ") for line in text.splitlines() if line.strip()]
                if steps:
                    return steps
            except Exception:
                pass
        # Fallback simple steps
        return [f"Step {i + 1} for: {task}" for i in range(5)]


