## ADDED Requirements

### Requirement: SSE endpoints require Bearer JWT

Routes under chat completions and protected conversation message APIs SHALL require a valid Bearer access token using the same validation as `GET /api/v1/me`.

#### Scenario: Chat without token

- **WHEN** client calls `POST /api/v1/chat/completions` without Authorization
- **THEN** response returns HTTP 401 with `code` 40101 in unified envelope
