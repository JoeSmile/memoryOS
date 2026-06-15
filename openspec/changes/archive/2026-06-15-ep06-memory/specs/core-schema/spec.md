## ADDED Requirements

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
