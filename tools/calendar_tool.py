import json
import os
import random

TASK_FILE = "tasks.json"

# Load tasks from file
def load_tasks():
    if not os.path.exists(TASK_FILE):
        return []
    with open(TASK_FILE, "r") as f:
        return json.load(f)

# Save tasks to file
def save_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

# Add a new task
def add_task(date, task, username):
    tasks = load_tasks()
    tasks.append({
        "username": username,
        "date": date,
        "task": task,
        "completed": False
    })
    save_tasks(tasks)

# Get tasks by date and username
def get_tasks(date, username):
    tasks = load_tasks()
    return [task for task in tasks if task["username"] == username and task["date"] == date]

# Mark a task as completed
def complete_task(date, index, username):
    tasks = load_tasks()
    filtered = [t for t in tasks if t["username"] == username and t["date"] == date]
    if 0 <= index < len(filtered):
        task_to_complete = filtered[index]
        for t in tasks:
            if (
                t["username"] == task_to_complete["username"] and
                t["date"] == task_to_complete["date"] and
                t["task"] == task_to_complete["task"]
            ):
                t["completed"] = True
                break
        save_tasks(tasks)

# Get a random motivational quote
def get_motivation():
    quotes = [
        "Keep going! You're doing great! 💪",
        "One task at a time. You're progressing! 🌱",
        "Success is the sum of small efforts repeated daily. ✨",
        "Celebrate every win, no matter how small. 🎉"
    ]
    return random.choice(quotes)
