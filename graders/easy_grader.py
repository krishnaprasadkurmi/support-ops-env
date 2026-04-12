from __future__ import annotations

from models.schemas import State


SIMILAR_LABELS = {
    "billing": {"payment", "refund", "charge", "invoice"},
    "technical": {"technical", "tech", "bug", "issue", "problem", "support"},
    "general": {"general", "question", "account", "other"},
}


def _normalize(value: str) -> str:
    return value.strip().lower()


def grade_easy(state: State, expected_outputs: dict) -> tuple[float, dict]:
    classification_actions = [
        item for item in state.history if item.action_type == "classify"
    ]
    if not classification_actions:
        return 0.0, {"match": "missing", "done": False}

    predicted = _normalize(classification_actions[-1].content)
    expected = _normalize(expected_outputs["classification"])
    similar = {_normalize(label) for label in expected_outputs.get("similar_labels", [])}
    similar.update(SIMILAR_LABELS.get(expected, set()))

    if predicted == expected:
        score = 1.0
        match = "exact"
    elif predicted in similar:
        score = 0.5
        match = "similar"
    else:
        score = 0.0
        match = "wrong"

    return score, {"match": match, "done": True, "expected_classification": expected}
