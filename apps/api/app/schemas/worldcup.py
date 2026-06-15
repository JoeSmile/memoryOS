from datetime import date

from pydantic import BaseModel, Field


class WcMatchBrief(BaseModel):
    id: str
    name: str
    stage_name: str
    group_name: str | None = None
    match_date: date
    home_team_name: str
    away_team_name: str
    home_score: int
    away_score: int
    extra_time: bool = False
    penalty_shootout: bool = False
    home_penalty_score: int | None = None
    away_penalty_score: int | None = None


class WcMatchStageGroup(BaseModel):
    stage_name: str
    stage_label: str
    matches: list[WcMatchBrief]


class WcTournamentMatchesRead(BaseModel):
    tournament_id: str
    tournament_name: str
    stages: list[WcMatchStageGroup] = Field(default_factory=list)
