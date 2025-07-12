"""
AI Scheduling Automation Model
Author: Arunava
Description: This module simulates AI-assisted scheduling automation logic.
"""

import time
from datetime import datetime, timedelta


class Task:
    def __init__(self, name, duration_minutes):
        self.name = name
        self.duration = timedelta(minutes=duration_minutes)
        self.start_time = None
        self.end_time = None

    def schedule(self, start_time):
        self.start_time = start_time
        self.end_time = start_time + self.duration

    def __str__(self):
        return f"Task: {self.name}, Start: {self.start_time}, End: {self.end_time}"


class Scheduler:
    def __init__(self):
        self.tasks = []

    def add_task(self, task_name, duration_minutes):
        task = Task(task_name, duration_minutes)
        self.tasks.append(task)

    def auto_schedule(self):
        print("Starting AI Auto-Scheduling Process...\n")
        current_time = datetime.now()

        for task in self.tasks:
            task.schedule(current_time)
            current_time = task.end_time + timedelta(minutes=5)  # 5-minute gap between tasks
            print(task)

    def get_schedule(self):
        return [str(task) for task in self.tasks]


def ai_suggest_task_improvement(task_name):
    """
    Simulated AI suggestion engine.
    """
    suggestions = {
        "backup": "Schedule backups during off-peak hours to reduce server load.",
        "report generation": "Consider running reports at midnight to avoid data inconsistency.",
        "system update": "System updates should be scheduled on weekends to minimize downtime.",
    }

    return suggestions.get(task_name.lower(), "No specific suggestions for this task.")


# Example usage
if __name__ == "__main__":
    scheduler = Scheduler()

    scheduler.add_task("Backup", 30)
    scheduler.add_task("Report Generation", 45)
    scheduler.add_task("System Update", 60)

    scheduler.auto_schedule()

    print("\nAI Suggestions:")
    for task in scheduler.tasks:
        suggestion = ai_suggest_task_improvement(task.name)
        print(f"{task.name}: {suggestion}")
