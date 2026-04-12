def get_task() -> dict:
    return {
        "task_type": "medium",
        "ticket": {
            "id": "medium-001",
            "text": "The app shows an upload error every time I try to add my profile picture. Please help.",
            "customer_tier": "standard",
            "channel": "chat",
        },
        "expected_outputs": {
            "required_keywords": ["sorry", "upload", "error", "retry", "screenshot"],
            "tone_keywords": ["sorry", "help"],
            "action_keywords": ["retry", "refresh", "check"],
            "follow_up_keywords": ["screenshot", "version", "details"],
        },
        "grader": "graders.medium_grader:grade_medium",
        "reward_range": [0.0, 1.0],
        "max_steps": 1,
        "required_action_types": ["respond"],
        "success_threshold": 0.8,
        "instructions": "Generate a helpful support response with clear next steps.",
    }
