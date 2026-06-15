import uuid

from app.core.exceptions import AppException
from app.demo.wc2022_analysis_presets import (
    DEMO_ANALYSIS_TEMPLATES,
    TEMPLATE_BY_ID,
)
from app.models import Message
from app.repositories.message_repository import MessageRepository
from app.repositories.wc_match_repository import WcMatchRepository
from app.schemas.demo_analysis import DemoAnalysisTemplateRead, DemoTurnResponse
from app.schemas.worldcup import WcMatchBrief
from app.services.conversation_service import ConversationService
from app.services.worldcup_match_service import WC_2022_TOURNAMENT_ID

from app.models.message import COMPLETION_COMPLETE

WORLD_CUP_MATCHES_COLLECTION = "worldcup-matches"


class DemoAnalysisService:
    def __init__(
        self,
        conversations: ConversationService,
        messages: MessageRepository,
        matches: WcMatchRepository,
    ) -> None:
        self._conversations = conversations
        self._messages = messages
        self._matches = matches

    def list_templates(self) -> list[DemoAnalysisTemplateRead]:
        return [
            DemoAnalysisTemplateRead(
                id=item.id,
                label=item.label,
                description=item.description,
            )
            for item in DEMO_ANALYSIS_TEMPLATES
        ]

    async def append_demo_turn(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        match_id: str,
        template_id: str,
    ) -> tuple[Message, Message]:
        await self._conversations.get_owned_conversation(conversation_id, user_id)

        template = TEMPLATE_BY_ID.get(template_id)
        if template is None:
            raise AppException(
                code=42201,
                message="demo_template_not_found",
                status_code=422,
            )

        row = await self._matches.get_for_tournament(WC_2022_TOURNAMENT_ID, match_id)
        if row is None:
            raise AppException(
                code=40401,
                message="match_not_found",
                status_code=404,
            )

        match, home_name, away_name, _ = row
        brief = WcMatchBrief(
            id=match.id,
            name=match.name,
            stage_name=match.stage_name,
            group_name=match.group_name,
            match_date=match.match_date,
            home_team_name=home_name,
            away_team_name=away_name,
            home_score=match.home_score,
            away_score=match.away_score,
            extra_time=match.extra_time,
            penalty_shootout=match.penalty_shootout,
            home_penalty_score=match.home_penalty_score,
            away_penalty_score=match.away_penalty_score,
        )

        user_content = template.build_user_prompt(brief)
        assistant_content = template.build_assistant_reply(brief)
        preview = brief.name[:120]
        rag_metadata = {
            "rag_sources": [
                {
                    "external_id": brief.id,
                    "collection": WORLD_CUP_MATCHES_COLLECTION,
                    "entity_type": "match",
                    "score": 0.91,
                    "content_preview": preview,
                },
            ],
            "demo": {
                "match_id": brief.id,
                "template_id": template.id,
            },
        }

        user_message = await self._messages.create(
            conversation_id,
            "user",
            user_content,
        )
        assistant_message = await self._messages.create(
            conversation_id,
            "assistant",
            assistant_content,
            completion_status=COMPLETION_COMPLETE,
            metadata_=rag_metadata,
        )
        await self._conversations.touch_activity(conversation_id)
        await self._conversations.invalidate_list_cache(user_id)

        return user_message, assistant_message

    @staticmethod
    def to_turn_response(
        user_message: Message,
        assistant_message: Message,
    ) -> DemoTurnResponse:
        return DemoTurnResponse(
            user_message_id=str(user_message.id),
            assistant_message_id=str(assistant_message.id),
        )
