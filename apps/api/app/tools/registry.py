from app.tools.definitions import ToolDefinition


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_definitions(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def list_openai_schemas(self) -> list[dict]:
        return [tool.to_openai_schema() for tool in self._tools.values()]
