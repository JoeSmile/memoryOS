from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import AppException
from app.services.demo_analysis_service import DemoAnalysisService


def _match_row():
    match = MagicMock()
    match.id = "M-2022-64"
    match.name = "Argentina vs France"
    match.stage_name = "final"
    match.group_name = None
    match.match_date = date(2022, 12, 18)
    match.home_score = 3
    match.away_score = 3
    match.extra_time = True
    match.penalty_shootout = True
    match.home_penalty_score = 4
    match.away_penalty_score = 2
    return match, "Argentina", "France", "2022 FIFA Men's World Cup"


@pytest.mark.asyncio
async def test_append_demo_turn_writes_user_and_assistant():
    conversations = MagicMock()
    conversations.get_owned_conversation = AsyncMock()
    conversations.touch_activity = AsyncMock()
    conversations.invalidate_list_cache = AsyncMock()

    messages = MagicMock()
    user_msg = MagicMock(id="user-id")
    assistant_msg = MagicMock(id="assistant-id")
    messages.create = AsyncMock(side_effect=[user_msg, assistant_msg])

    matches = MagicMock()
    matches.get_for_tournament = AsyncMock(return_value=_match_row())

    service = DemoAnalysisService(conversations, messages, matches)
    user_message, assistant_message = await service.append_demo_turn(
        conversation_id="conv-id",
        user_id="user-id",
        match_id="M-2022-64",
        template_id="flank_attack",
    )

    assert user_message is user_msg
    assert assistant_message is assistant_msg
    assert messages.create.await_count == 2
    assistant_call = messages.create.await_args_list[1]
    assert assistant_call.args[1] == "assistant"
    assert "边路进攻" in assistant_call.args[2]
    assert assistant_call.kwargs["metadata_"]["rag_sources"][0]["external_id"] == "M-2022-64"


@pytest.mark.asyncio
async def test_append_demo_turn_rejects_unknown_template():
    conversations = MagicMock()
    conversations.get_owned_conversation = AsyncMock()
    matches = MagicMock()
    messages = MagicMock()
    service = DemoAnalysisService(conversations, messages, matches)

    with pytest.raises(AppException) as exc:
        await service.append_demo_turn(
            conversation_id="conv-id",
            user_id="user-id",
            match_id="M-2022-64",
            template_id="unknown",
        )
    assert exc.value.message == "demo_template_not_found"
