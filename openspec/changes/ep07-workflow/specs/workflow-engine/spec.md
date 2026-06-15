## ADDED Requirements

### Requirement: Workflow feature flags

The API SHALL expose configuration to enable or disable workflow execution globally and for the World Cup match-analysis workflow.

#### Scenario: Workflows disabled

- **WHEN** `WORKFLOW_ENABLED` is false
- **THEN** workflow run endpoints reject requests without executing LangGraph

#### Scenario: Match-analysis disabled

- **WHEN** `WORKFLOW_MATCH_ANALYSIS_ENABLED` is false
- **THEN** match-analysis run creation is rejected while other future workflows may remain configurable separately

### Requirement: User-initiated workflow trigger

Match-analysis runs SHALL be started only by authenticated explicit API requests from the workflow UI, not by chat keywords or scheduled cron jobs in this change.

#### Scenario: Start via POST runs

- **WHEN** logged-in user submits the match-analysis form and client calls `POST /api/v1/workflows/match-analysis/runs`
- **THEN** the system creates a workflow run and schedules BackgroundTasks execution after the HTTP response

#### Scenario: Chat completions do not auto-start workflows

- **WHEN** user sends a normal chat message without calling workflow run endpoints
- **THEN** no match-analysis workflow run is created

### Requirement: World Cup match-analysis workflow execution

The system SHALL provide a code-defined LangGraph workflow that accepts a `match_id` referencing existing `wc_matches` Silver data, loads structured match facts from the database without LLM, retrieves related RAG knowledge without LLM generation, and produces a grounded analysis report in a dedicated LLM step.

#### Scenario: Start run with valid match id

- **WHEN** authenticated user posts a `match_id` that exists in `wc_matches`
- **THEN** the system creates a workflow run and schedules asynchronous LangGraph execution

#### Scenario: Load match context without LLM

- **WHEN** the load-match-context node completes successfully
- **THEN** run state contains structured facts derived from World Cup Silver tables for that match before any report LLM call

#### Scenario: RAG retrieval uses match context and optional focus

- **WHEN** the retrieve-match-knowledge node runs with optional `analysis_focus`
- **THEN** the retrieval query is built from structured match context and focus text rather than free-form chat user text

#### Scenario: Report LLM is grounded

- **WHEN** the generate-report node completes successfully
- **THEN** run `result_json` includes an analysis report and the prompt path requires use of loaded facts and retrieved chunks without inventing scores or statistics absent from inputs

#### Scenario: Invalid match rejected

- **WHEN** user posts an unknown `match_id`
- **THEN** API returns validation or not-found error without creating a run

### Requirement: Optional analysis focus

The workflow SHALL accept an optional `analysis_focus` string that adjusts RAG query wording and report emphasis without changing Silver-table SQL selection in the MVP.

#### Scenario: Focus adjusts retrieval and report angle

- **WHEN** user supplies `analysis_focus` such as wing attack or penalty shootout theme
- **THEN** retrieval and report prompts reflect that angle while still grounding on the same match facts

#### Scenario: Insufficient focus evidence

- **WHEN** facts and chunks lack detail for the requested focus
- **THEN** the report states insufficient evidence rather than fabricating unsupported statistics

### Requirement: Match picker HTTP API

The API SHALL expose a read-only list of World Cup matches suitable for launching the match-analysis workflow.

#### Scenario: List matches for workflow UI

- **WHEN** authenticated user calls `GET /api/v1/workflows/match-analysis/matches`
- **THEN** response includes match identifiers and display labels sourced from `wc_matches` and related team metadata

### Requirement: Workflow run HTTP API

Authenticated users SHALL create and inspect their own workflow runs via REST API using polling (no chat SSE).

#### Scenario: Create match-analysis run

- **WHEN** user calls `POST /api/v1/workflows/match-analysis/runs`
- **THEN** response includes run id and initial status

#### Scenario: Poll run status and steps

- **WHEN** user calls `GET /api/v1/workflow-runs/{id}` for their run
- **THEN** response includes run status, ordered steps with summaries, and final result when succeeded

#### Scenario: List recent runs

- **WHEN** user calls `GET /api/v1/workflow-runs` with optional workflow slug filter
- **THEN** response lists only that user's runs without exposing other users' data

### Requirement: Match-analysis workflow UI

The web app SHALL provide an authenticated page to select a World Cup match, optionally enter analysis focus, start analysis via an explicit button, poll run progress, and show the final report.

#### Scenario: Select match and start run

- **WHEN** logged-in user selects a match and clicks start analysis
- **THEN** client creates a run via API and polls until completion or failure

#### Scenario: Step bar reflects backend steps

- **WHEN** run steps update on the server
- **THEN** UI step bar and log panel reflect step keys and summaries in order

#### Scenario: View prior run

- **WHEN** user selects a run from recent history
- **THEN** UI displays stored steps and final report without requiring chat UI

### Requirement: Workflow isolated from chat graph

Workflow LangGraph execution SHALL NOT modify chat completion SSE behavior or reuse chat conversation rows for workflow runs.

#### Scenario: Chat completions unchanged

- **WHEN** workflow runs are enabled
- **THEN** existing `POST /chat/completions` contract and SSE event order remain unchanged

#### Scenario: Separate graph module

- **WHEN** match-analysis executes
- **THEN** it uses workflow-specific LangGraph state under `graphs/workflows/` rather than mutating `chat_graph.py` topology
