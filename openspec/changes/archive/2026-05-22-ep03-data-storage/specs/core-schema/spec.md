## ADDED Requirements

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
