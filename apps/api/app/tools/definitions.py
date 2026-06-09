from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from pydantic import BaseModel, Field

ToolHandler = Callable[[dict[str, Any], "ToolContext"], Awaitable[Any]]


class ToolContext(BaseModel):
    """Runtime context passed to every tool handler."""

    model_config = {"arbitrary_types_allowed": True}

    user_id: str
    db: Any | None = None


class ToolDefinition(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "properties": {}},
    )
    handler: ToolHandler = Field(exclude=True)

    def to_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolExecutionResult(BaseModel):
    success: bool
    summary: str
    duration_ms: int
    output: Any | None = None
    error: str | None = None


def validate_tool_arguments(
    arguments: Mapping[str, Any],
    parameters_schema: Mapping[str, Any],
) -> str | None:
    """Return an error message when arguments fail JSON Schema subset validation."""
    if parameters_schema.get("type", "object") != "object":
        return None

    if not isinstance(arguments, dict):
        return "arguments must be an object"

    properties = parameters_schema.get("properties")
    if not isinstance(properties, dict):
        properties = {}

    required = parameters_schema.get("required", [])
    if not isinstance(required, list):
        required = []

    for key in required:
        if not isinstance(key, str) or key not in arguments:
            return f"missing required argument: {key}"

    for key, value in arguments.items():
        if key not in properties:
            continue
        prop = properties[key]
        if not isinstance(prop, dict):
            continue
        expected = prop.get("type")
        if expected == "boolean":
            if not isinstance(value, bool):
                return f"argument {key} must be a boolean"
            continue
        if expected == "integer":
            if type(value) is not int:
                return f"argument {key} must be an integer"
            continue
        if expected == "number":
            if type(value) not in (int, float) or isinstance(value, bool):
                return f"argument {key} must be a number"
            continue
        if expected == "string" and not isinstance(value, str):
            return f"argument {key} must be a string"

    return None
