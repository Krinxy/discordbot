from pydantic import BaseModel, ConfigDict


class AuthFunctionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auth_required: bool
