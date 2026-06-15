# core-schema Specification

## Purpose
TBD - created by archiving change ep03-data-storage. Update Purpose after archive.
## Requirements
### Requirement: Core business tables exist

The database schema SHALL include tables `users`, `conversations`, and `messages` with relationships supporting multi-turn chat per user.

#### Scenario: User owns conversations

- **WHEN** a row exists in `conversations` with `user_id` referencing `users.id`
- **THEN** deleting the user cascades or is restricted per migration definition (cascade delete configured)

#### Scenario: Conversation contains messages

- **WHEN** a row exists in `messages` with `conversation_id` referencing `conversations.id`
- **THEN** messages are ordered by `created_at` for history retrieval

### Requirement: ER documentation matches schema

The project SHALL maintain `docs/database.md` describing tables, columns, types, and foreign keys consistent with the Alembic migration.

#### Scenario: Developer reviews schema

- **WHEN** developer opens `docs/database.md`
- **THEN** they see definitions for `users`, `conversations`, and `messages` aligned with ORM models

### Requirement: Message role field

The `messages` table SHALL store a `role` field distinguishing participant types (e.g. `user`, `assistant`, `system`) for EP02 streaming integration.

#### Scenario: Store assistant reply

- **WHEN** system inserts a message with `role` assistant
- **THEN** the row is persisted with `content` text and `conversation_id` set

### Requirement: Client message id on messages table

The `messages` table SHALL include an optional `client_message_id` UUID column for client-supplied idempotency keys.

#### Scenario: Unique client id per conversation

- **WHEN** two rows in the same conversation share the same non-null `client_message_id`
- **THEN** the database constraint prevents duplicate insertion

#### Scenario: Legacy rows without client id

- **WHEN** historical messages have NULL `client_message_id`
- **THEN** history retrieval and ordering remain unchanged

### Requirement: Assistant completion status

The `messages` table SHALL support an optional `completion_status` for assistant rows (e.g. `complete`, `interrupted`).

#### Scenario: Completed stream

- **WHEN** assistant stream finishes normally
- **THEN** persisted assistant has `completion_status` complete

#### Scenario: Interrupted stream

- **WHEN** client disconnects mid-stream with partial content
- **THEN** persisted assistant has `completion_status` interrupted

### Requirement: Composite indexes for list queries

Schema migration SHALL add indexes optimized for listing conversations by user ordered by recency and messages by conversation ordered by time.

#### Scenario: Migration applies indexes

- **WHEN** developer runs `alembic upgrade head` after revision 002
- **THEN** PostgreSQL contains composite indexes documented in `docs/database.md` for conversation and message list patterns

### Requirement: Message metadata JSONB column

The schema SHALL provide a nullable `metadata` JSONB column on `messages` for extensible per-message attributes such as RAG source citations.

#### Scenario: Migration adds metadata

- **WHEN** developer runs `alembic upgrade head` after the metadata revision
- **THEN** the `messages` table contains a nullable `metadata` JSONB column

#### Scenario: Legacy messages unchanged

- **WHEN** messages existed before the metadata migration
- **THEN** their `metadata` column is null and APIs remain backward compatible

### Requirement: Memories table exists

The database schema SHALL include a `memories` table owned by `users` with fields for memory type, text content, importance score, optional embedding vector, optional expiry, and timestamps.

#### Scenario: User owns memories

- **WHEN** a row exists in `memories` with `user_id` referencing `users.id`
- **THEN** deleting the user cascades or removes dependent rows per migration definition

#### Scenario: Memory vector dimension

- **WHEN** migration applies the `memories` table
- **THEN** the embedding column dimension matches the project's RAG embedding dimension

### Requirement: Conversation context summary column

The `conversations` table SHALL include a nullable text column `context_summary` and a nullable `summary_updated_at` timestamp for rolling session compression.

#### Scenario: New conversation without summary

- **WHEN** a conversation is created
- **THEN** `context_summary` is NULL until an asynchronous summary job writes it

#### Scenario: Summary persisted

- **WHEN** summary job completes
- **THEN** `context_summary` and `summary_updated_at` are updated on the conversation row

