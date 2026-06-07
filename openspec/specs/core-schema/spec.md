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

