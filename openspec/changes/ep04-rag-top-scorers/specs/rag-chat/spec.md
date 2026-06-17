# rag-chat Delta — ranking query sufficiency

## ADDED Requirements

### Requirement: Ranking queries require aggregate scorer context

When the user query expresses a **ranking or leaderboard intent** (e.g. 射手榜, 进球榜, 金靴, top N, 前 N 名), `compute_rag_sufficient` SHALL return false unless at least one retrieved chunk provides aggregate ranking content.

Aggregate ranking content is satisfied when a chunk's `external_id` starts with `tournament_scorers:` OR its text contains the marker `[Top Scorers]`.

Match-only or single-player career chunks MUST NOT alone satisfy sufficiency for ranking-intent queries, even when similarity scores exceed `RAG_CHAT_MIN_SCORE` and tournament year matches.

#### Scenario: Match chunks insufficient for scorers leaderboard query

- **WHEN** user asks `2022世界杯射手榜前10名`
- **AND** retrieved chunks are only `match:*` cards from WC-2022 with scores above threshold
- **THEN** `compute_rag_sufficient` returns false

#### Scenario: Tournament scorers chunk sufficient

- **WHEN** user asks `2022世界杯射手榜前10名`
- **AND** retrieved chunks include `tournament_scorers:WC-2022` above threshold
- **THEN** `compute_rag_sufficient` returns true

#### Scenario: Non-ranking query unchanged

- **WHEN** user asks `2022世界杯决赛比分`
- **AND** retrieved chunks include the WC-2022 final `match:*` card above threshold
- **THEN** `compute_rag_sufficient` returns true (existing score + year rules apply)
