from langchain_core.messages import AIMessage, HumanMessage

from app.services.memory.token_counter import (
    count_messages_tokens,
    count_text_tokens,
    encoding_for_model,
)


def test_count_text_tokens_empty():
    assert count_text_tokens("", model="qwen-turbo") == 0


def test_count_text_tokens_non_empty():
    count = count_text_tokens("Hello, world!", model="qwen-turbo")
    assert count > 0


def test_encoding_fallback_for_qwen():
    encoding = encoding_for_model("qwen-turbo")
    assert encoding.name == "cl100k_base"


def test_encoding_fallback_for_unknown_model():
    encoding = encoding_for_model("not-a-real-model-xyz")
    assert encoding.name == "cl100k_base"


def test_count_messages_tokens_sums_messages():
    messages = [
        HumanMessage(content="用户问题"),
        AIMessage(content="助手回答"),
    ]
    total = count_messages_tokens(messages, model="qwen-turbo")
    assert total == (
        count_text_tokens("用户问题", model="qwen-turbo")
        + count_text_tokens("助手回答", model="qwen-turbo")
    )
