from pydantic import BaseModel, ConfigDict

from dependencies.auth.policy.auth_function_policy import AuthFunctionPolicy


class AuthPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    functions: dict[str, AuthFunctionPolicy]
    users: list[str]
    roles: list[int]
    cooldown_seconds: float = 2.0
