from __future__ import annotations

from models.schemas import State


SIMILAR_LABELS = {
    "billing": {"payment", "refund", "charge", "invoice"},
    "technical": {"technical", "tech", "bug", "issue", "problem", "support"},
    "general": {"general", "question", "account", "other"},
}


def _normalize(value: str) -> str:
    return value.strip().lower()


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _classification_score(state: State, expected_outputs: dict) -> float:
    classification_actions = [
        item for item in state.history if item.action_type == "classify"
    ]
    if not classification_actions:
        return 0.0

    predicted = _normalize(classification_actions[-1].content)
    expected = _normalize(expected_outputs["classification"])
    similar = {_normalize(label) for label in expected_outputs.get("similar_labels", [])}
    similar.update(SIMILAR_LABELS.get(expected, set()))

    if predicted == expected:
        return 0.3
    if predicted in similar:
        return 0.15
    return 0.0


def _response_score(state: State, expected_outputs: dict) -> float:
    response_actions = [item for item in state.history if item.action_type == "respond"]
    if not response_actions:
        return 0.0

    response_text = _normalize(response_actions[-1].content)
    required_keywords = [_normalize(keyword) for keyword in expected_outputs.get("required_keywords", [])]
    tone_keywords = [_normalize(keyword) for keyword in expected_outputs.get("tone_keywords", [])]
    action_keywords = [_normalize(keyword) for keyword in expected_outputs.get("action_keywords", [])]
    follow_up_keywords = [_normalize(keyword) for keyword in expected_outputs.get("follow_up_keywords", [])]

    keyword_matches = sum(1 for keyword in required_keywords if keyword in response_text)
    keyword_score = 0.2 * (keyword_matches / len(required_keywords)) if required_keywords else 0.2

    tone_score = 0.0
    if "sorry" in response_text or "apologize" in response_text:
        tone_score += 0.05
    if _contains_any(response_text, tone_keywords):
        tone_score += 0.05

    completeness_score = 0.0
    if _contains_any(response_text, action_keywords):
        completeness_score += 0.05
    if _contains_any(response_text, follow_up_keywords):
        completeness_score += 0.05

    return round(min(0.4, keyword_score + tone_score + completeness_score), 4)


def _escalation_score(state: State, expected_outputs: dict) -> float:
    escalation_required = expected_outputs.get("escalation_required", False)
    escalation_actions = [item for item in state.history if item.action_type == "escalate"]

    if not escalation_required:
        return 0.3 if not escalation_actions else 0.2
    if not escalation_actions:
        return 0.0

    escalation_text = _normalize(escalation_actions[-1].content)
    keywords = [_normalize(keyword) for keyword in expected_outputs.get("escalation_keywords", [])]
    matches = sum(1 for keyword in keywords if keyword in escalation_text)

    if matches >= 2 or "true" in escalation_text or "yes" in escalation_text:
        return 0.3
    if matches == 1:
        return 0.15
    return 0.0


def grade_hard(state: State, expected_outputs: dict) -> tuple[float, dict]:
    classification_score = _classification_score(state, expected_outputs)
    response_score = _response_score(state, expected_outputs)
    escalation_score = _escalation_score(state, expected_outputs)

    total = round(min(1.0, classification_score + response_score + escalation_score), 4)

    has_classification = any(item.action_type == "classify" for item in state.history)
    has_response = any(item.action_type == "respond" for item in state.history)
    needs_escalation = expected_outputs.get("escalation_required", False)
    has_escalation = any(item.action_type == "escalate" for item in state.history)

    return total, {
        "components": {
            "classification": round(classification_score, 4),
            "response": round(response_score, 4),
            "escalation": round(escalation_score, 4),
        },
        "done": has_classification and has_response and (has_escalation or not needs_escalation),
    }
