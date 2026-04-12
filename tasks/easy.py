def get_task() -> dict:
    return {
        "task_type": "easy",
        "ticket": {
            "id": "easy-001",
            "text": "I was charged twice for my subscription this month and need a refund for the extra charge.",
            "customer_tier": "standard",
            "channel": "email",
        },
        "expected_outputs": {
            "classification": "billing",
            "similar_labels": ["payment", "refund", "charge"],
        },
        "grader": "graders.easy_grader:grade_easy",
        "reward_range": [0.0, 1.0],
        "max_steps": 1,
        "required_action_types": ["classify"],
        "success_threshold": 1.0,
        "instructions": "Classify the ticket as billing, technical, or general.",
    }
