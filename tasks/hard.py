def get_task() -> dict:
    return {
        "task_type": "hard",
        "ticket": {
            "id": "hard-001",
            "text": "The dashboard shows an access error after the latest update, and payroll for 200 employees is blocked. We need urgent help.",
            "customer_tier": "enterprise",
            "channel": "email",
        },
        "expected_outputs": {
            "classification": "technical",
            "similar_labels": ["bug", "issue", "support"],
            "required_keywords": ["sorry", "dashboard", "error", "payroll", "update"],
            "tone_keywords": ["sorry", "priority"],
            "action_keywords": ["investigating", "share", "update"],
            "follow_up_keywords": ["screenshot", "timestamp", "engineering"],
            "escalation_required": True,
            "escalation_keywords": ["urgent", "engineering", "payroll", "incident"],
        },
        "grader": "graders.hard_grader:grade_hard",
        "reward_range": [0.0, 1.0],
        "max_steps": 3,
        "required_action_types": ["classify", "respond", "escalate"],
        "success_threshold": 0.85,
        "instructions": "Classify the ticket, write a support response, and escalate because the issue is urgent.",
    }
