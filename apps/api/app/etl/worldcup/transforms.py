"""Pure transforms for World Cup Bronze → Silver ETL."""

from __future__ import annotations

from datetime import date


def clean_url(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "not applicable":
        return None
    return text


def parse_bool(value: str | int | None) -> bool:
    if value is None:
        return False
    return str(value).strip() == "1"


def parse_int(value: str | int | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return int(text)


def parse_date(value: str) -> date:
    return date.fromisoformat(value.strip())


def parse_optional_date(value: str | None) -> date | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "not available":
        return None
    return date.fromisoformat(text)


def tournament_slug(tournament_id: str) -> str:
    suffix = tournament_id.removeprefix("WC-").lower()
    return f"wc{suffix}"


POSITION_SOURCE_COLUMNS = (
    ("goal_keeper", "GK"),
    ("defender", "DF"),
    ("midfielder", "MF"),
    ("forward", "FW"),
)


def parse_positions(row: dict[str, str]) -> tuple[list[str], str | None]:
    positions: list[str] = []
    primary: str | None = None
    for column, code in POSITION_SOURCE_COLUMNS:
        if parse_bool(row.get(column)):
            positions.append(code)
            if primary is None:
                primary = code
    return positions, primary


def split_tournament_years(list_tournaments: str | None) -> list[int]:
    if not list_tournaments or not str(list_tournaments).strip():
        return []
    return [int(part.strip()) for part in str(list_tournaments).split(",") if part.strip()]


def player_display_name(given_name: str, family_name: str) -> str:
    return f"{given_name.strip()} {family_name.strip()}".strip()


def parse_shirt_number(value: str | int | None) -> int | None:
    number = parse_int(value)
    if number is None or number == 0:
        return None
    return number
