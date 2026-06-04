from app.core.config import settings
from app.graphs.chat_state import ChatState
from app.graphs.nodes.mock_model import mock_invoke


def _build_chat_openai():
    from langchain_openai import ChatOpenAI

    kwargs: dict = {"model": settings.openai_model}
    if settings.openai_api_key:
        kwargs["api_key"] = settings.openai_api_key
    if settings.openai_api_base:
        kwargs["base_url"] = settings.openai_api_base
    return ChatOpenAI(**kwargs)


async def call_model(state: ChatState) -> dict:
    messages = state["messages"]
    if settings.use_mock_llm:
        response = await mock_invoke(messages)
    else:
        llm = _build_chat_openai()
        response = await llm.ainvoke(messages)
    return {"messages": [response]}
