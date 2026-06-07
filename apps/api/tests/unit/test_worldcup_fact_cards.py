"""Unit tests for World Cup Gold fact card formatting."""

from __future__ import annotations

from datetime import date

from app.etl.worldcup.fact_cards import (
    FactCard,
    build_match_card_text,
    build_player_card_text,
    build_player_career_card_text,
    build_tournament_card_text,
    format_goal_summary,
    format_goals_by_year,
    format_match_score,
    format_minute,
)


def test_format_minute():
    assert format_minute(23, 0) == "23'"
    assert format_minute(90, 3) == "90+3'"


def test_format_match_score_penalties():
    line = format_match_score(
        3,
        3,
        extra_time=True,
        penalty_shootout=True,
        home_penalty_score=4,
        away_penalty_score=2,
    )
    assert line == "3-3 (ET), penalties 4-2"


def test_format_goal_summary_own_goal_penalty():
    summary = format_goal_summary(
        "John Doe",
        45,
        2,
        own_goal=True,
        penalty=True,
    )
    assert summary == "John Doe (OG) (pen) (45+2')"


def test_build_match_card_text():
    text = build_match_card_text(
        tournament_name="2022 FIFA World Cup",
        home_team="Argentina",
        away_team="France",
        stage_name="final",
        match_date=date(2022, 12, 18),
        stadium="Lusail Stadium",
        city="Lusail",
        score_line="3-3 (ET), penalties 4-2",
        goals=["Lionel Messi (23')", "Kylian Mbappé (80')"],
        is_replay=False,
        replay_of_match_id=None,
    )
    assert "[Match] 2022 FIFA World Cup · Argentina vs France · final" in text
    assert "Score: 3-3 (ET), penalties 4-2" in text
    assert "Lionel Messi (23')" in text


def test_format_goals_by_year():
    assert format_goals_by_year({}) == "0"
    assert format_goals_by_year({2022: 7, 2018: 1}) == "8 total (2018: 1, 2022: 7)"


def test_build_player_career_card_text():
    text = build_player_career_card_text(
        display_name="Lionel Messi",
        player_id="P-14758",
        birth_date=date(1987, 6, 24),
        primary_position="FW",
        positions=["FW"],
        tournament_years=[2006, 2010, 2014, 2018, 2022],
        squad_count=5,
        female=False,
        team_codes=["ARG"],
        goals_by_year={2006: 1, 2014: 4, 2018: 1, 2022: 7},
        own_goals=0,
        appearances=26,
        starts=19,
        substitutes=7,
        awards=["Golden Ball (2022)", "Silver Boot (2022)"],
        yellow_cards=2,
        red_cards=0,
    )
    assert "[Player Career] Lionel Messi" in text
    assert "Goals: 13 total" in text
    assert "2022: 7" in text
    assert "Appearances: 26 (19 starts, 7 substitute)" in text
    assert "Golden Ball (2022)" in text


def test_build_player_card_text():
    text = build_player_card_text(
        display_name="Lionel Messi",
        team_code="ARG",
        birth_date=date(1987, 6, 24),
        primary_position="FW",
        positions=["FW", "MF"],
        tournament_years=[2006, 2010, 2014, 2018, 2022],
        squad_count=5,
        female=False,
    )
    assert "[Player] Lionel Messi (ARG)" in text
    assert "World Cup years (5)" in text
    assert "Squad listings: 5" in text


def test_build_tournament_card_text():
    text = build_tournament_card_text(
        tournament_id="WC-2022",
        name="2022 FIFA World Cup",
        year=2022,
        start_date=date(2022, 11, 20),
        end_date=date(2022, 12, 18),
        host_country="Qatar",
        winner="Argentina",
        count_teams=32,
        has_final=True,
    )
    assert "[Tournament] 2022 FIFA World Cup (WC-2022)" in text
    assert "Winner: Argentina" in text


def test_fact_card_json_roundtrip():
    card = FactCard(
        id="match:M-2022-64",
        entity_type="match",
        source_ids=["M-2022-64", "WC-2022"],
        text="[Match] sample",
    )
    payload = card.to_json()
    assert '"id": "match:M-2022-64"' in payload
    assert '"source_ids"' in payload
