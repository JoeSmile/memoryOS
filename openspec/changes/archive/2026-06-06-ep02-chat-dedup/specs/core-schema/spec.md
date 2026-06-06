## ADDED Requirements

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
