"""
Utility functions for AI Scheduling Automation
Author: Arunava
"""

import random


def estimate_energy_usage(duration_minutes, task_type):
    """
    Simulates energy usage estimation based on task type and duration.
    """
    base_consumption = {
        "Backup": 1.5,
        "Report Generation": 2.0,
        "System Update": 2.5,
        "AI Model Training": 5.0,
        "Data Cleaning": 3.0,
        "Client Notification": 0.5
    }

    multiplier = base_consumption.get(task_type, 1.0)
    estimated_kwh = (duration_minutes / 60) * multiplier

    return round(estimated_kwh, 2)


def predict_task_delay(task_priority):
    """
    Simulates task delay prediction based on priority.
    """
    delay_chance = {
        "Very High": 0.05,
        "High": 0.10,
        "Medium": 0.20,
        "Low": 0.30
    }

    chance = delay_chance.get(task_priority, 0.20)
    delayed = random.random() < chance

    return delayed


# Example usage test
if __name__ == "__main__":
    print("Energy Estimate Example:")
    print(estimate_energy_usage(120, "AI Model Training"), "kWh")

    print("Task Delay Prediction Example:")
    for priority in ["Very High", "High", "Medium", "Low"]:
        print(f"{priority}: {'Delayed' if predict_task_delay(priority) else 'On Time'}")
