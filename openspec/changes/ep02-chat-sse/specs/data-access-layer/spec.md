## ADDED Requirements

### Requirement: List messages for conversation

The API SHALL expose `GET /api/v1/conversations/{conversation_id}/messages` returning messages ordered by `created_at` ascending.

#### Scenario: List messages success

- **WHEN** authenticated user requests messages for a conversation they own
- **THEN** response returns `code` 0 and `data` as a list of message objects with `id`, `role`, `content`, `created_at`

#### Scenario: List messages forbidden

- **WHEN** conversation belongs to another user
- **THEN** response returns non-2xx with unified error envelope

### Requirement: Chat routes use authenticated user

Chat and message list routes SHALL resolve the current user via `Depends(get_current_user)` and SHALL NOT trust `user_id` from query or body for authorization.

#### Scenario: Ownership from token subject

- **WHEN** user calls chat completions with valid Bearer token
- **THEN** conversation ownership is checked against JWT subject user id only
