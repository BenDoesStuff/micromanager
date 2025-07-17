# Micromanager

Micromanager is a simple desktop application that helps you break down large tasks into micro steps and focus on them one at a time.

## Features
- Enter a large task and automatically generate smaller steps (uses OpenAI API if `OPENAI_API_KEY` is set, otherwise uses placeholder steps).
- View one step at a time and mark it as done to move forward.
- Progress bar showing completed steps.
- Toggle to display the full history of steps.
- Optional dark mode.
- Saves your progress between sessions in `~/.micromanager_tasks.json`.

## Requirements
- Python 3.8+
- PyQt5
- `openai` package (optional for AI breakdown)

Install dependencies with:
```bash
pip install -r requirements.txt
```

Run the application with:
```bash
python main.py
```

Set the `OPENAI_API_KEY` environment variable if you want to use OpenAI for automatic task breakdown.

