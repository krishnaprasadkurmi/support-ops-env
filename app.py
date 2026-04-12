from __future__ import annotations

import os
from enum import Enum
from typing import Optional

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from openai import OpenAI
from pydantic import BaseModel, ConfigDict

from env.environment import SupportEnv
from models.schemas import Action, State, StepResult


API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN", "")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=os.getenv("OPENAI_API_KEY", "dummy_key"),
)


class TaskType(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class ResetRequest(BaseModel):
    task_type: Optional[TaskType] = TaskType.easy
    model_config = ConfigDict(json_schema_extra={"example": {"task_type": "easy"}})


app = FastAPI(
    title="SupportOpsEnv",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# FORCE OPENAPI SCHEMA (CRITICAL FOR HF COMPATIBILITY)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title="SupportOpsEnv",
        version="1.0.0",
        description="Support Operations Environment API",
        routes=app.routes,
    )
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
def root():
    """Root endpoint - always returns 200 OK"""
    return {
        "status": "ok",
        "message": "SupportOpsEnv running",
        "docs": "/docs",
        "version": "1.0.0"
    }


environment = SupportEnv()
environment.reset("easy")


@app.post("/reset", response_model=State)
def reset_environment(request: Optional[ResetRequest] = None) -> State:
    """Reset environment - accepts empty body or JSON body"""
    task_type = "easy"
    if request and request.task_type:
        task_type = request.task_type.value
    return environment.reset(task_type)


@app.post("/step", response_model=StepResult)
def step_environment(action: Action) -> StepResult:
    """Execute one step in the environment"""
    return environment.step(action)


@app.get("/state", response_model=State)
def get_state() -> State:
    """Get current environment state"""
    return environment.state()


@app.get("/{full_path:path}")
def catch_all(full_path: str):
    """Fallback route to prevent 404s - HF stability requirement"""
    return {
        "status": "ok",
        "message": f"Fallback route hit: {full_path}",
        "docs": "/docs"
    }
