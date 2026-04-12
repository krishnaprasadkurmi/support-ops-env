from __future__ import annotations

from models.schemas import State


def _normalize(value: str) -> str:
    return value.strip().lower()


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def grade_medium(state: State, expected_outputs: dict) -> tuple[float, dict]:
    response_actions = [item for item in state.history if item.action_type == "respond"]
    if not response_actions:
        return 0.0, {"components": {"keywords": 0.0, "tone": 0.0, "completeness": 0.0}, "done": False}

    response_text = _normalize(response_actions[-1].content)
    required_keywords = [_normalize(keyword) for keyword in expected_outputs.get("required_keywords", [])]
    tone_keywords = [_normalize(keyword) for keyword in expected_outputs.get("tone_keywords", [])]
    action_keywords = [_normalize(keyword) for keyword in expected_outputs.get("action_keywords", [])]
    follow_up_keywords = [_normalize(keyword) for keyword in expected_outputs.get("follow_up_keywords", [])]

    keyword_matches = sum(1 for keyword in required_keywords if keyword in response_text)
    keyword_score = 0.5 * (keyword_matches / len(required_keywords)) if required_keywords else 0.5

    apology_score = 0.1 if "sorry" in response_text or "apologize" in response_text else 0.0
    helpful_score = 0.1 if _contains_any(response_text, tone_keywords) else 0.0
    tone_score = apology_score + helpful_score

    action_score = 0.15 if _contains_any(response_text, action_keywords) else 0.0
    follow_up_score = 0.15 if _contains_any(response_text, follow_up_keywords) else 0.0
    completeness_score = action_score + follow_up_score

    total = min(1.0, round(keyword_score + tone_score + completeness_score, 4))
    return total, {
        "components": {
            "keywords": round(keyword_score, 4),
            "tone": round(tone_score, 4),
            "completeness": round(completeness_score, 4),
        },
        "done": True,
    }
