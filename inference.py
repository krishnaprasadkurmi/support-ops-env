from __future__ import annotations

import os

from openai import OpenAI

from env.environment import SupportEnv
from models.schemas import Action


MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")

client = OpenAI(
    base_url=os.environ["API_BASE_URL"],
    api_key=os.environ["API_KEY"],
)

TASKS = ["easy", "medium", "hard"]


def call_llm(system_prompt: str, user_input: str) -> str:
    response = client.chat.completions.create(
        model=os.environ.get("MODEL_NAME", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=0,
    )
    output = response.choices[0].message.content
    if not output:
        raise ValueError("Empty LLM response")
    return output


def _action_task_label(task_name: str, completed_action_types: list[str]) -> str:
    if task_name == "easy":
        return "easy classification task"
    if task_name == "medium":
        return "medium response task"
    if "classify" not in completed_action_types:
        return "hard task before classification"
    if "respond" not in completed_action_types:
        return "hard task after classification before response"
    return "hard task after classification and response before escalation"


def _decide_action_type(task_type: str) -> str:
    response = client.chat.completions.create(
        model=os.environ.get("MODEL_NAME", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "You are a support agent deciding next action."},
            {"role": "user", "content": f"Task: {task_type}. Decide next action: classify, respond, or escalate."},
        ],
        temperature=0,
    )
    action = (response.choices[0].message.content or "").strip().lower()
    if "classify" in action:
        action = "classify"
    elif "respond" in action:
        action = "respond"
    else:
        action = "escalate"
    return action


def _normalize_classification(output: str) -> str:
    normalized = output.strip().lower()
    if "billing" in normalized:
        return "billing"
    if "technical" in normalized or "tech" in normalized:
        return "technical"
    return "general"


def _generate_action_content(task_name: str, action_type: str, ticket_text: str) -> str:
    if action_type == "classify":
        output = call_llm(
            "You are a helpful support agent.",
            (
                "Classify this support ticket as exactly one label: billing, technical, or general.\n"
                f"Ticket: {ticket_text}"
            ),
        )
        return _normalize_classification(output)

    if action_type == "respond":
        if task_name == "hard":
            return call_llm(
                "You are a helpful support agent.",
                (
                    "Write one concise customer support response for this urgent ticket.\n"
                    "Include: sorry, dashboard error, update, payroll impact, screenshot or timestamp, and mention engineering is investigating.\n"
                    f"Ticket: {ticket_text}"
                ),
            ).strip()
        return call_llm(
            "You are a helpful support agent.",
            (
                "Write one concise customer support response.\n"
                "Include: sorry, the upload or error issue, a retry step, and a request for screenshot or app version/details.\n"
                f"Ticket: {ticket_text}"
            ),
        ).strip()

    return call_llm(
        "You are a helpful support agent.",
        (
            "Write a short escalation summary for engineering.\n"
            "Mention urgent engineering escalation for a payroll-blocking incident.\n"
            f"Ticket: {ticket_text}"
        ),
    ).strip()


def format_action(action: Action) -> str:
    return action.action_type


def format_rewards(rewards: list[float]) -> str:
    return ",".join(f"{reward:.2f}" for reward in rewards)


def clamp_score(score: float) -> float:
    return max(0.01, min(0.99, score))


def run_task(task_name: str) -> None:
    env = SupportEnv()
    state = env.reset(task_name)
    rewards: list[float] = []
    success = False
    error: str | None = None

    print(f"[START] task={task_name} env=support_ops model={MODEL_NAME}")

    try:
        max_steps = int(env.task_config.get("max_steps", 1)) if env.task_config else 1
        for step_number in range(1, max_steps + 1):
            completed_action_types = [item.action_type for item in env.state().history]
            task_type = _action_task_label(task_name, completed_action_types)
            action_type = _decide_action_type(task_type)
            action = Action(
                action_type=action_type,
                content=_generate_action_content(task_name, action_type, state.ticket.text),
            )
            result = env.step(action)
            rewards.append(result.reward)
            print(
                f"[STEP] step={step_number} action={format_action(action)} "
                f"reward={result.reward:.2f} done={str(result.done).lower()}"
            )
            if result.done:
                break

        raw_score = min(1.0, sum(rewards))
        final_score = clamp_score(raw_score)
        threshold = float(env.task_config.get("success_threshold", 0.8)) if env.task_config else 0.8
        success = raw_score >= threshold
        print(
            f"[END] success={str(success).lower()} steps={len(rewards)} "
            f"score={final_score:.2f} rewards={format_rewards(rewards)} error=null"
        )
    except Exception as exc:  # pragma: no cover - defensive logging path
        error = str(exc)
        final_score = clamp_score(sum(rewards))
        print(
            f"[END] success=false steps={len(rewards)} "
            f"score={final_score:.2f} rewards={format_rewards(rewards)} error={error}"
        )


def main() -> None:
    for task_name in TASKS:
        run_task(task_name)


if __name__ == "__main__":
    main()
