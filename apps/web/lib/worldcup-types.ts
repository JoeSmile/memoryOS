export type WcMatchBrief = {
  id: string;
  name: string;
  stage_name: string;
  group_name: string | null;
  match_date: string;
  home_team_name: string;
  away_team_name: string;
  home_score: number;
  away_score: number;
  extra_time: boolean;
  penalty_shootout: boolean;
  home_penalty_score: number | null;
  away_penalty_score: number | null;
};

export type WcMatchStageGroup = {
  stage_name: string;
  stage_label: string;
  matches: WcMatchBrief[];
};

export type WcTournamentMatchesRead = {
  tournament_id: string;
  tournament_name: string;
  stages: WcMatchStageGroup[];
};

export function formatMatchScore(match: WcMatchBrief): string {
  let label = `${match.home_score}-${match.away_score}`;
  if (match.extra_time) {
    label += " (ET)";
  }
  if (
    match.penalty_shootout &&
    match.home_penalty_score != null &&
    match.away_penalty_score != null
  ) {
    label += ` · 点球 ${match.home_penalty_score}-${match.away_penalty_score}`;
  }
  return label;
}

export function formatMatchLabel(match: WcMatchBrief): string {
  const group =
    match.group_name && match.stage_name === "group stage"
      ? ` · ${match.group_name}`
      : "";
  return `${match.home_team_name} vs ${match.away_team_name} (${formatMatchScore(match)})${group}`;
}
