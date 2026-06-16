# rate-limit-audit Specification

## Purpose

Redis sliding-window rate limits and structured audit logging (EP09 Story 9.4).

## Requirements

### Requirement: Sliding window rate limits

When `RATE_LIMIT_ENABLED` is true, the API SHALL apply Redis sliding-window rate limits per route class using user id when authenticated and client IP otherwise.

#### Scenario: Chat completions within limit

- **WHEN** authenticated user stays under configured chat completion rate
- **THEN** requests succeed normally

#### Scenario: Chat completions over limit

- **WHEN** authenticated user exceeds chat completion rate within the window
- **THEN** API returns HTTP 429 with envelope `code=42901` and `message=rate_limit_exceeded`

#### Scenario: Login rate limit by IP

- **WHEN** client exceeds login attempts from the same IP within the window
- **THEN** login returns HTTP 429 before credential check completes

### Requirement: Audit log for sensitive operations

The API SHALL append audit log entries for configured sensitive actions including conversation deletion (if exposed), demo-turn, and authentication failures above threshold.

#### Scenario: Demo turn audited

- **WHEN** user successfully appends a demo analysis turn
- **THEN** an audit record is persisted with `user_id`, action `demo_turn`, and resource id

#### Scenario: Audit query requires auth

- **WHEN** unauthenticated client requests audit logs
- **THEN** API returns HTTP 401

### Requirement: Rate limit bypass when Redis unavailable

When Redis is unreachable and `RATE_LIMIT_FAIL_OPEN` is true, the API SHALL log a warning and allow the request without rate limiting.

#### Scenario: Fail open with warning

- **WHEN** Redis connection fails during rate limit check and fail-open is enabled
- **THEN** request proceeds and a structured warning is logged
