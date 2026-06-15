"""Canned WC-2022 demo analysis templates (no LLM)."""

from dataclasses import dataclass
from typing import Callable

from app.schemas.worldcup import WcMatchBrief


@dataclass(frozen=True)
class DemoAnalysisTemplate:
    id: str
    label: str
    description: str
    build_user_prompt: Callable[[WcMatchBrief], str]
    build_assistant_reply: Callable[[WcMatchBrief], str]


def _score_line(match: WcMatchBrief) -> str:
    line = f"{match.home_score}-{match.away_score}"
    if match.extra_time:
        line += "（加时）"
    if (
        match.penalty_shootout
        and match.home_penalty_score is not None
        and match.away_penalty_score is not None
    ):
        line += f"，点球 {match.home_penalty_score}-{match.away_penalty_score}"
    return line


def _match_heading(match: WcMatchBrief) -> str:
    group = f" · {match.group_name}" if match.group_name else ""
    return (
        f"{match.home_team_name} vs {match.away_team_name}"
        f"（{match.match_date}，{match.stage_name}{group}）"
    )


DEMO_ANALYSIS_TEMPLATES: tuple[DemoAnalysisTemplate, ...] = (
    DemoAnalysisTemplate(
        id="flank_attack",
        label="边路进攻成功率",
        description="两翼推进、传中与反击效率（演示数据）",
        build_user_prompt=lambda m: (
            f"请分析 {_match_heading(m)} 的边路进攻成功率与两翼反击效率。"
        ),
        build_assistant_reply=lambda m: (
            f"## 边路进攻与反击（演示结论）\n\n"
            f"**对阵**：{_match_heading(m)} · 比分 {_score_line(m)}\n\n"
            f"基于赛会统计与战术复盘（演示文案，非实时建模）：\n\n"
            f"- **左路进攻占比**约 38%，成功进入前场三区 12 次，其中 **5 次形成射门或造点**。\n"
            f"- **右路**更偏快速纵向推进，反击回合中 **边路参与率约 62%**。\n"
            f"- 对手在边路限制上偏保守，{m.away_team_name} 被反击时肋部空档较大。\n\n"
            f"> 演示模式：数值为剧本示例，用于展示分析维度而非真实 Opta 输出。"
        ),
    ),
    DemoAnalysisTemplate(
        id="midfield_control",
        label="中场控制与传球",
        description="控球、推进传球与节奏切换（演示数据）",
        build_user_prompt=lambda m: (
            f"请分析 {_match_heading(m)} 的中场控球、传球网络与节奏控制。"
        ),
        build_assistant_reply=lambda m: (
            f"## 中场控制（演示结论）\n\n"
            f"**对阵**：{_match_heading(m)} · 比分 {_score_line(m)}\n\n"
            f"- 控球率示意：**{m.home_team_name} 54% / {m.away_team_name} 46%**（演示值）。\n"
            f"- 关键推进传球多发自后腰至前场肋部，上半场节奏偏慢，下半场转换次数上升。\n"
            f"- 在比分僵持阶段，双方中场回撤加深，**纵向传球成功率下降约 8%**（示意）。\n\n"
            f"> 演示模式：用于说明「中场控制」分析模板，非真实传球网络图。"
        ),
    ),
    DemoAnalysisTemplate(
        id="set_pieces",
        label="定位球威胁",
        description="角球、任意球与二次进攻（演示数据）",
        build_user_prompt=lambda m: (
            f"请评估 {_match_heading(m)} 的定位球设计与角球威胁。"
        ),
        build_assistant_reply=lambda m: (
            f"## 定位球威胁（演示结论）\n\n"
            f"**对阵**：{_match_heading(m)} · 比分 {_score_line(m)}\n\n"
            f"- 全场角球合计 **11 个**（演示），其中 **3 次**形成禁区内第一点争顶。\n"
            f"- {m.home_team_name} 更倾向短角球变线，{m.away_team_name} 高空轰炸占比更高。\n"
            f"- 定位球进球占比约 **25%**（示意），符合淘汰赛高强度对抗特征。\n\n"
            f"> 演示模式：角球次数为示例，非官方统计表直出。"
        ),
    ),
    DemoAnalysisTemplate(
        id="pressing_transition",
        label="逼抢与转换",
        description="高位逼抢、抢断与快反（演示数据）",
        build_user_prompt=lambda m: (
            f"请分析 {_match_heading(m)} 的高位逼抢强度与攻防转换质量。"
        ),
        build_assistant_reply=lambda m: (
            f"## 逼抢与转换（演示结论）\n\n"
            f"**对阵**：{_match_heading(m)} · 比分 {_score_line(m)}\n\n"
            f"- 前场逼抢触发 **18 次**（示意），其中 **6 次**在 8 秒内完成射门。\n"
            f"- 丢球后 **5 秒内回防到位率**约 72%（演示），边路空档是主要风险点。\n"
            f"- 比分变化后逼抢强度波动明显，体能分配影响下半场转换效率。\n\n"
            f"> 演示模式：逼抢次数为剧本示例。"
        ),
    ),
    DemoAnalysisTemplate(
        id="keeper_penalties",
        label="门将 & 点球环节",
        description="扑救、点球大战与关键扑救（演示数据）",
        build_user_prompt=lambda m: (
            f"请点评 {_match_heading(m)} 的门将表现"
            f"{'与点球大战' if m.penalty_shootout else ''}。"
        ),
        build_assistant_reply=lambda m: (
            f"## 门将表现（演示结论）\n\n"
            f"**对阵**：{_match_heading(m)} · 比分 {_score_line(m)}\n\n"
            + (
                f"- 点球大战：主队点球 **{m.home_penalty_score}** 粒，客队 **{m.away_penalty_score}** 粒（演示解读）。\n"
                f"- 门将共 **2 次**关键扑救改变比分走势（示意）。\n"
                if m.penalty_shootout
                else f"- 常规时间门将扑救成功率示意 **78%**，高空球处理稳定。\n"
            )
            + f"- 定位球防守中门将指挥防线次数偏多，呼应前场压迫战术。\n\n"
            f"> 演示模式：扑救数据为示例，非 FIFA 官方门将统计。"
        ),
    ),
)

TEMPLATE_BY_ID = {item.id: item for item in DEMO_ANALYSIS_TEMPLATES}
