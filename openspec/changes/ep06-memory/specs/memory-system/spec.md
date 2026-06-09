## ADDED Requirements

### Requirement: Token budget configuration

The API SHALL expose configuration for maximum context tokens sent to the LLM and reserved tokens for the assistant reply.

#### Scenario: Defaults applied

- **WHEN** `MEMORY_ENABLED` is true and env vars are unset
- **THEN** the system uses documented defaults for `MAX_CONTEXT_TOKENS` and `RESERVE_FOR_REPLY`

#### Scenario: Memory disabled rollback

- **WHEN** `MEMORY_ENABLED` is false
- **THEN** chat completions behave as EP05 (full DB history in graph state, no memory nodes)

### Requirement: Short-term message trimming

Before retrieval and model invocation, the chat graph SHALL trim conversation messages to fit the token budget while preserving system instructions, injected memory blocks, and RAG grounding content.

#### Scenario: Long conversation completes

- **WHEN** a conversation has more turns than fit in `MAX_CONTEXT_TOKENS` minus `RESERVE_FOR_REPLY`
- **THEN** the graph still produces a successful completion without provider context-length errors

#### Scenario: Recent turns preserved

- **WHEN** trimming removes older turns
- **THEN** the most recent user message and its adjacent assistant/tool messages remain in graph state

#### Scenario: Full history in database unchanged

- **WHEN** trimming occurs for a completion
- **THEN** all messages remain stored in `messages` and list APIs return the full history

### Requirement: Conversation rolling summary

The system SHALL maintain an optional rolling text summary per conversation and inject it into the LLM context when present. Summary LLM jobs SHALL be throttled so long single-conversation usage does not run a summary on every turn after the first trigger.

#### Scenario: First summary when history grows long

- **WHEN** `context_summary` is empty and full conversation history token count exceeds `SUMMARY_TRIGGER_TOKENS` after a completed turn
- **THEN** the system schedules an asynchronous first summary update without blocking the SSE stream

#### Scenario: Subsequent summary throttled

- **WHEN** `context_summary` is already set and a turn finalizes within `SUMMARY_COOLDOWN_SECONDS` of `summary_updated_at`
- **THEN** the system does not schedule another summary job for that turn

#### Scenario: Subsequent summary on incremental growth

- **WHEN** `context_summary` is set, cooldown has elapsed, and tokens in messages created after `summary_updated_at` are at least `SUMMARY_INCREMENT_TOKENS`
- **THEN** the system schedules a rolling summary merge using the existing summary plus only new messages

#### Scenario: Summary injected on next turn

- **WHEN** `conversations.context_summary` is non-empty
- **THEN** the next completion includes the summary in a dedicated system context block before recent turns

#### Scenario: New conversation resets summary state

- **WHEN** user starts a new conversation row
- **THEN** `context_summary` and `summary_updated_at` are empty until that conversation's first summary trigger fires

### Requirement: Long-term user memories

The system SHALL store per-user long-term memories with type, content, importance, embedding, and optional expiry; retrieve TopK relevant memories per turn; and extract new memories asynchronously after completed turns.

#### Scenario: Memory extraction after completion

- **WHEN** a chat turn finalizes with `MEMORY_LONG_TERM_ENABLED` true
- **THEN** the system schedules asynchronous memory extraction for that user

#### Scenario: Relevant memories injected

- **WHEN** long-term memory is enabled and matching memories exist for the user
- **THEN** the model system context includes a bounded list of memory snippets for that user only

#### Scenario: Memory isolated from RAG corpus

- **WHEN** RAG retrieval runs for world-cup knowledge
- **THEN** long-term user memories are not written into the RAG knowledge collections

### Requirement: Memory lifecycle HTTP API

Authenticated users SHALL list and delete their own long-term memories via REST API.

#### Scenario: List own memories

- **WHEN** authenticated user calls `GET /api/v1/memories`
- **THEN** response contains only that user's memories without raw embedding vectors

#### Scenario: Delete own memory

- **WHEN** user deletes a memory row they own
- **THEN** the row is removed and subsequent turns no longer retrieve it

#### Scenario: Cross-user delete forbidden

- **WHEN** user attempts to delete another user's memory id
- **THEN** API returns 404 or 403 per project envelope convention

### Requirement: Expired memories pruned

The system SHALL remove memories past `expires_at` or below configured importance during maintenance or extraction tasks.

#### Scenario: Expired row removed

- **WHEN** a memory row has `expires_at` in the past
- **THEN** pruning removes it before or during the next extraction cycle

### Requirement: Memories management UI

The web app SHALL provide an authenticated page to view and delete the current user's memories.

#### Scenario: Navigate to memories page

- **WHEN** logged-in user opens `/memories`
- **THEN** the page lists memories from `GET /api/v1/memories`

#### Scenario: Delete from UI

- **WHEN** user confirms delete on a memory row
- **THEN** the client calls `DELETE /api/v1/memories/{id}` and refreshes the list
