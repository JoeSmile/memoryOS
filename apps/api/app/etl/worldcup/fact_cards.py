"""Generate Gold fact cards from Silver World Cup tables."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

SPOTLIGHT_CARD_IDS = (
    "match:M-2022-64",
    "match:M-2018-64",
    "tournament:WC-2022",
    "tournament:WC-2018",
    "player:P-14758",
    "player:P-64077",
    "player:P-80404",
    "match:M-2022-01",
    "match:M-1986-51",
    "match:M-1970-12",
)


@dataclass(frozen=True)
class FactCard:
    id: str
    entity_type: str
    source_ids: list[str]
    text: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def format_minute(regulation: int, stoppage: int) -> str:
    if stoppage > 0:
        return f"{regulation}+{stoppage}'"
    return f"{regulation}'"


def format_match_score(
    home_score: int,
    away_score: int,
    *,
    extra_time: bool,
    penalty_shootout: bool,
    home_penalty_score: int | None,
    away_penalty_score: int | None,
) -> str:
    base = f"{home_score}-{away_score}"
    if extra_time and not penalty_shootout:
        return f"{base} (ET)"
    if penalty_shootout and home_penalty_score is not None and away_penalty_score is not None:
        return f"{base} (ET), penalties {home_penalty_score}-{away_penalty_score}"
    return base


def format_goal_summary(
    player_name: str,
    minute_regulation: int,
    minute_stoppage: int,
    *,
    own_goal: bool,
    penalty: bool,
) -> str:
    minute = format_minute(minute_regulation, minute_stoppage)
    label = player_name
    if own_goal:
        label = f"{player_name} (OG)"
    if penalty:
        label = f"{label} (pen)"
    return f"{label} ({minute})"


def build_match_card_text(
    *,
    tournament_name: str,
    home_team: str,
    away_team: str,
    stage_name: str,
    match_date: date,
    stadium: str,
    city: str,
    score_line: str,
    goals: list[str],
    is_replay: bool,
    replay_of_match_id: str | None,
) -> str:
    replay_note = ""
    if is_replay and replay_of_match_id:
        replay_note = f"\nReplay of {replay_of_match_id}."
    goals_line = "Goals: (none)"
    if goals:
        goals_line = "Goals: " + ", ".join(goals) + "."
    return (
        f"[Match] {tournament_name} · {home_team} vs {away_team} · "
        f"{stage_name} · {match_date.isoformat()}\n"
        f"Score: {score_line}. Stadium: {stadium}, {city}.{replay_note}\n"
        f"{goals_line}"
    )


def build_player_card_text(
    *,
    display_name: str,
    team_code: str | None,
    birth_date: date | None,
    primary_position: str | None,
    positions: list[str],
    tournament_years: list[int],
    squad_count: int,
    female: bool,
) -> str:
    gender = "Women's" if female else "Men's"
    born = birth_date.isoformat() if birth_date else "unknown"
    pos = primary_position or (positions[0] if positions else "unknown")
    years = ", ".join(str(y) for y in sorted(tournament_years)) or "none"
    code_part = f" ({team_code})" if team_code else ""
    return (
        f"[Player] {display_name}{code_part} · {gender}\n"
        f"Born: {born}. Primary position: {pos}. "
        f"World Cup years ({len(tournament_years)}): {years}.\n"
        f"Squad listings: {squad_count}."
    )


def build_tournament_card_text(
    *,
    tournament_id: str,
    name: str,
    year: int,
    start_date: date,
    end_date: date,
    host_country: str | None,
    winner: str | None,
    count_teams: int | None,
    has_final: bool,
) -> str:
    host = host_country or "unknown"
    champ = winner or "unknown"
    teams = str(count_teams) if count_teams is not None else "unknown"
    final_note = "Includes final." if has_final else "No final recorded."
    return (
        f"[Tournament] {name} ({tournament_id})\n"
        f"Year: {year}. Dates: {start_date.isoformat()} to {end_date.isoformat()}.\n"
        f"Host: {host}. Winner: {champ}. Teams: {teams}. {final_note}"
    )


async def _fetch_rows(session: AsyncSession, sql: str, params: dict | None = None) -> list[dict[str, Any]]:
    result = await session.execute(text(sql), params or {})
    return [dict(row) for row in result.mappings().all()]


async def generate_match_cards(
    session: AsyncSession,
    tournament_id: str | None = None,
) -> list[FactCard]:
    where = "WHERE m.tournament_id = :tid" if tournament_id else ""
    params = {"tid": tournament_id} if tournament_id else {}
    matches = await _fetch_rows(
        session,
        f"""
        SELECT m.id, m.tournament_id, m.stage_name, m.match_date,
               m.home_score, m.away_score, m.extra_time, m.penalty_shootout,
               m.home_penalty_score, m.away_penalty_score,
               m.is_replay, m.replay_of_match_id,
               ht.name AS home_team, at.name AS away_team,
               s.name AS stadium, s.city_name AS city,
               t.name AS tournament_name
        FROM wc_matches m
        JOIN wc_teams ht ON m.home_team_id = ht.id
        JOIN wc_teams at ON m.away_team_id = at.id
        JOIN wc_stadiums s ON m.stadium_id = s.id
        JOIN wc_tournaments t ON m.tournament_id = t.id
        {where}
        ORDER BY m.match_date, m.id
        """,
        params,
    )
    if not matches:
        return []

    match_ids = [row["id"] for row in matches]
    goals = await _fetch_rows(
        session,
        """
        SELECT g.match_id, p.display_name, g.minute_regulation, g.minute_stoppage,
               g.own_goal, g.penalty
        FROM wc_goals g
        JOIN wc_players p ON g.player_id = p.id
        WHERE g.match_id = ANY(:match_ids)
        ORDER BY g.match_id, g.minute_regulation, g.minute_stoppage, g.id
        """,
        {"match_ids": match_ids},
    )
    goals_by_match: dict[str, list[str]] = {}
    for goal in goals:
        summary = format_goal_summary(
            goal["display_name"],
            goal["minute_regulation"],
            goal["minute_stoppage"],
            own_goal=goal["own_goal"],
            penalty=goal["penalty"],
        )
        goals_by_match.setdefault(goal["match_id"], []).append(summary)

    cards: list[FactCard] = []
    for row in matches:
        score_line = format_match_score(
            row["home_score"],
            row["away_score"],
            extra_time=row["extra_time"],
            penalty_shootout=row["penalty_shootout"],
            home_penalty_score=row["home_penalty_score"],
            away_penalty_score=row["away_penalty_score"],
        )
        text_body = build_match_card_text(
            tournament_name=row["tournament_name"],
            home_team=row["home_team"],
            away_team=row["away_team"],
            stage_name=row["stage_name"],
            match_date=row["match_date"],
            stadium=row["stadium"],
            city=row["city"],
            score_line=score_line,
            goals=goals_by_match.get(row["id"], []),
            is_replay=row["is_replay"],
            replay_of_match_id=row["replay_of_match_id"],
        )
        cards.append(
            FactCard(
                id=f"match:{row['id']}",
                entity_type="match",
                source_ids=[row["id"], row["tournament_id"]],
                text=text_body,
            )
        )
    return cards


async def generate_player_cards(
    session: AsyncSession,
    tournament_id: str | None = None,
) -> list[FactCard]:
    if tournament_id:
        players = await _fetch_rows(
            session,
            """
            SELECT DISTINCT p.id, p.display_name, p.birth_date, p.female,
                   p.primary_position, p.positions,
                   sq.team_id
            FROM wc_players p
            JOIN wc_squads sq ON p.id = sq.player_id
            WHERE sq.tournament_id = :tid
            ORDER BY p.display_name
            """,
            {"tid": tournament_id},
        )
    else:
        players = await _fetch_rows(
            session,
            """
            SELECT p.id, p.display_name, p.birth_date, p.female,
                   p.primary_position, p.positions, NULL AS team_id
            FROM wc_players p
            ORDER BY p.display_name
            """,
        )

    if not players:
        return []

    player_ids = [row["id"] for row in players]
    years_rows = await _fetch_rows(
        session,
        """
        SELECT player_id, year
        FROM wc_player_tournament_years
        WHERE player_id = ANY(:player_ids)
        ORDER BY player_id, year
        """,
        {"player_ids": player_ids},
    )
    years_by_player: dict[str, list[int]] = {}
    for row in years_rows:
        years_by_player.setdefault(row["player_id"], []).append(row["year"])

    squad_rows = await _fetch_rows(
        session,
        """
        SELECT player_id, COUNT(*) AS squad_count
        FROM wc_squads
        WHERE player_id = ANY(:player_ids)
        GROUP BY player_id
        """,
        {"player_ids": player_ids},
    )
    squad_counts = {row["player_id"]: row["squad_count"] for row in squad_rows}

    team_codes: dict[str, str] = {}
    if tournament_id:
        code_rows = await _fetch_rows(
            session,
            """
            SELECT sq.player_id, t.code
            FROM wc_squads sq
            JOIN wc_teams t ON sq.team_id = t.id
            WHERE sq.tournament_id = :tid
            """,
            {"tid": tournament_id},
        )
        team_codes = {row["player_id"]: row["code"] for row in code_rows}

    cards: list[FactCard] = []
    for row in players:
        text_body = build_player_card_text(
            display_name=row["display_name"],
            team_code=team_codes.get(row["id"]),
            birth_date=row["birth_date"],
            primary_position=row["primary_position"],
            positions=list(row["positions"] or []),
            tournament_years=years_by_player.get(row["id"], []),
            squad_count=squad_counts.get(row["id"], 0),
            female=row["female"],
        )
        source_ids = [row["id"]]
        if tournament_id:
            source_ids.append(tournament_id)
        cards.append(
            FactCard(
                id=f"player:{row['id']}",
                entity_type="player",
                source_ids=source_ids,
                text=text_body,
            )
        )
    return cards


async def generate_tournament_cards(
    session: AsyncSession,
    tournament_id: str | None = None,
) -> list[FactCard]:
    where = "WHERE id = :tid" if tournament_id else ""
    params = {"tid": tournament_id} if tournament_id else {}
    tournaments = await _fetch_rows(
        session,
        f"""
        SELECT id, name, year, start_date, end_date,
               host_country, winner, count_teams, final
        FROM wc_tournaments
        {where}
        ORDER BY year
        """,
        params,
    )
    cards: list[FactCard] = []
    for row in tournaments:
        text_body = build_tournament_card_text(
            tournament_id=row["id"],
            name=row["name"],
            year=row["year"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            host_country=row["host_country"],
            winner=row["winner"],
            count_teams=row["count_teams"],
            has_final=row["final"],
        )
        cards.append(
            FactCard(
                id=f"tournament:{row['id']}",
                entity_type="tournament",
                source_ids=[row["id"]],
                text=text_body,
            )
        )
    return cards


def write_jsonl(path: Path, cards: list[FactCard]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for card in cards:
            handle.write(card.to_json())
            handle.write("\n")


def build_spotlight_samples(all_cards: dict[str, list[FactCard]]) -> list[FactCard]:
    index = {card.id: card for cards in all_cards.values() for card in cards}
    samples: list[FactCard] = []
    for card_id in SPOTLIGHT_CARD_IDS:
        card = index.get(card_id)
        if card is not None:
            samples.append(card)
    return samples


async def export_fact_cards(
    session: AsyncSession,
    output_dir: Path,
    tournament_id: str | None = None,
) -> dict[str, int]:
    match_cards = await generate_match_cards(session, tournament_id)
    player_cards = await generate_player_cards(session, tournament_id)
    tournament_cards = await generate_tournament_cards(session, tournament_id)

    write_jsonl(output_dir / "matches.jsonl", match_cards)
    write_jsonl(output_dir / "players.jsonl", player_cards)
    write_jsonl(output_dir / "tournaments.jsonl", tournament_cards)

    samples = build_spotlight_samples(
        {
            "matches": match_cards,
            "players": player_cards,
            "tournaments": tournament_cards,
        }
    )
    write_jsonl(output_dir / "samples.jsonl", samples)

    return {
        "matches": len(match_cards),
        "players": len(player_cards),
        "tournaments": len(tournament_cards),
        "samples": len(samples),
    }
