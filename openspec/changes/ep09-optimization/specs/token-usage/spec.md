# token-usage Specification

## Purpose

Token metering and per-user daily quotas for LLM chat completions (EP09 Story 9.3).

## Requirements

### Requirement: Persist token usage on completion

The API SHALL record `prompt_tokens`, `completion_tokens`, and `total_tokens` for each successful chat completion, associated with `user_id` and `conversation_id`, via a **`UsageRecorder`** abstraction so embedded and future remote graph modes share the same persistence path.

#### Scenario: Usage stored after stream completes

- **WHEN** a chat completion stream finishes with provider usage metadata
- **THEN** a row is written to persistent storage with token counts and timestamp

#### Scenario: Regenerate counts as new assistant usage

- **WHEN** client completes with `regenerate=true`
- **THEN** usage for the new assistant generation is recorded without duplicating user message token attribution

### Requirement: Daily user quota enforcement

The API SHALL enforce a configurable per-user daily token quota and reject new completions when exceeded.

#### Scenario: Under quota allowed

- **WHEN** user's aggregated usage for the current UTC day is below `USER_DAILY_TOKEN_QUOTA`
- **THEN** chat completion proceeds normally

#### Scenario: Over quota rejected

- **WHEN** user's daily aggregated tokens would exceed quota on a new completion request
- **THEN** API returns HTTP 429 with envelope `code=42902` and `message=token_quota_exceeded` before streaming starts

### Requirement: Optional usage summary endpoint

The API MAY expose `GET /api/v1/usage/me` returning today's aggregated token usage for the authenticated user.

#### Scenario: Authenticated usage read

- **WHEN** authenticated user requests usage summary
- **THEN** response envelope `code=0` includes `prompt_tokens`, `completion_tokens`, and `total_tokens` for the current day
