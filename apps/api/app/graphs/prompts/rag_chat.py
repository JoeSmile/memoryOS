"""RAG system prompts for World Cup fact-card chat (ep04-rag-chat)."""

from __future__ import annotations

from collections.abc import Sequence

from langchain_core.messages import SystemMessage

from app.schemas.knowledge import KnowledgeChunkHit
from app.services.security.rag_sanitizer import sanitize_chunk

_REFERENCE_HEADING = "## 参考来源"


def build_rag_system_message(chunks: Sequence[KnowledgeChunkHit]) -> SystemMessage:
    """Build system message for grounded (hits) or no-hit fallback."""
    if not chunks:
        return SystemMessage(content=_NO_HIT_PROMPT)
    return SystemMessage(content=_build_grounded_prompt(chunks))


def _build_grounded_prompt(chunks: Sequence[KnowledgeChunkHit]) -> str:
    blocks: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        safe_content = sanitize_chunk(chunk.content).strip()
        blocks.append(
            "\n".join(
                [
                    f"[{index}] external_id={chunk.external_id} "
                    f"collection={chunk.collection} score={chunk.score:.4f}",
                    safe_content,
                    "---",
                ]
            )
        )
    references = "\n".join(blocks)
    return f"""你是 MemoryOS 世界杯事实助手。仅依据下方「参考资料」回答用户问题。
不得编造参考资料中未出现的比分、进球数、球员数据或赛果。

参考资料（按相关度排序）：
{references}

回答要求：
- 用简洁中文回答用户问题
- 用户未写明具体年份或日期时，默认按 **现在 / 今年 / 今日** 的最新语境理解（勿用往年资料冒充当前答案）
- 正文结束后另起一段，使用 Markdown 二级标题「{_REFERENCE_HEADING}」
- 列表项格式：- [external_id] 一句摘要（可截断）
- 仅引用上方参考资料中出现过的 external_id"""


_NO_HIT_PROMPT = """你是 MemoryOS 世界杯事实助手。知识库检索未找到与用户问题足够相关的事实卡。
请礼貌说明无法在知识库中找到相关信息，并建议用户换问法或缩小问题范围。
禁止编造任何比赛比分、进球数、球员统计、奖项或赛果。
不要输出「参考来源」章节，不要假装引用了资料。"""
