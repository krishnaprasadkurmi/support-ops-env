from __future__ import annotations

from typing import Callable

from graders.easy_grader import grade_easy
from graders.hard_grader import grade_hard
from graders.medium_grader import grade_medium
from models.schemas import Action, HistoryItem, State, StepResult, Ticket
from tasks.easy import get_task as get_easy_task
from tasks.hard import get_task as get_hard_task
from tasks.medium import get_task as get_medium_task


TaskLoader = Callable[[], dict]
Grader = Callable[[State, dict], tuple[float, dict]]


TASK_REGISTRY: dict[str, dict[str, TaskLoader | Grader]] = {
    "easy": {"loader": get_easy_task, "grader": grade_easy},
    "medium": {"loader": get_medium_task, "grader": grade_medium},
    "hard": {"loader": get_hard_task, "grader": grade_hard},
}


class SupportEnv:
    def __init__(self) -> None:
        self.task_type: str | None = None
        self.task_config: dict | None = None
        self.expected_outputs: dict = {}
        self.done: bool = False
        self.score: float = 0.0
        self._state: State | None = None

    def reset(self, task_type: str) -> State:
        task_key = task_type.strip().lower()
        if task_key not in TASK_REGISTRY:
            raise ValueError(f"Unknown task type: {task_type}")

        task_loader = TASK_REGISTRY[task_key]["loader"]
        assert callable(task_loader)
        task_config = task_loader()

        self.task_type = task_key
        self.task_config = task_config
        self.expected_outputs = task_config["expected_outputs"]
        self.done = False
        self.score = 0.0
        self._state = State(ticket=Ticket(**task_config["ticket"]), history=[], step_count=0)
        return self._state

    def step(self, action: Action | dict) -> StepResult:
        if self._state is None or self.task_config is None or self.task_type is None:
            raise RuntimeError("Environment must be reset before calling step().")

        if self.done:
            return StepResult(
                state=self._state,
                reward=0.0,
                done=True,
                info={"message": "Environment already completed.", "score": round(self.score, 4)},
            )

        action_model = action if isinstance(action, Action) else Action(**action)
        normalized_content = action_model.content.strip()

        previous_score = self.score
        history_item = HistoryItem(action_type=action_model.action_type, content=normalized_content)
        self._state.history.append(history_item)
        self._state.step_count += 1

        grader = TASK_REGISTRY[self.task_type]["grader"]
        assert callable(grader)
        total_score, info = grader(self._state, self.expected_outputs)
        total_score = max(0.0, min(1.0, total_score))

        reward = round(max(0.0, total_score - previous_score), 4)
        self.score = total_score
        self._state.history[-1].reward = reward

        max_steps = int(self.task_config.get("max_steps", 1))
        required_action_types = self.task_config.get("required_action_types", [])
        required_complete = all(
            any(item.action_type == action_type for item in self._state.history)
            for action_type in required_action_types
        )

        self.done = bool(info.get("done")) or required_complete or self._state.step_count >= max_steps

        return StepResult(
            state=self._state,
            reward=reward,
            done=self.done,
            info={
                "task_type": self.task_type,
                "score": round(self.score, 4),
                "expected_outputs": self.expected_outputs,
                **info,
            },
        )

    def state(self) -> State:
        if self._state is None:
            raise RuntimeError("Environment must be reset before calling state().")
        return self._state
