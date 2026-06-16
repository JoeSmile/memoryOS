# chat-security Specification (Delta)

## ADDED Requirements

### Requirement: Chat content length limit

The API SHALL reject chat completion and demo-turn requests whose user-visible content exceeds a configurable maximum length before invoking the LLM.

#### Scenario: Content within limit accepted

- **WHEN** client sends chat content with length ≤ `CHAT_MAX_CONTENT_CHARS` (default 8000)
- **THEN** request proceeds to normal completion or demo-turn handling

#### Scenario: Content over limit rejected

- **WHEN** client sends content exceeding the configured maximum
- **THEN** API returns HTTP 422 with envelope `code=42201` and `message=content_too_long` before streaming starts

### Requirement: Prompt injection heuristic filter

The API SHALL scan user message content for high-risk injection patterns (e.g. role override phrases) and reject them before LLM invocation when `PROMPT_INJECTION_FILTER_ENABLED` is true.

#### Scenario: Benign football analysis passes

- **WHEN** user asks a normal match analysis question without override phrases
- **THEN** filter allows the message through

#### Scenario: Obvious injection blocked

- **WHEN** user content contains configured override phrases such as "ignore previous instructions"
- **THEN** API returns HTTP 422 with `message=prompt_injection_detected` and does not call the LLM

### Requirement: Shared RAG sanitizer module

The API SHALL implement a single Python `rag_sanitizer` module used for both vector ingest preprocessing and post-retrieval chunk cleaning.

#### Scenario: ETL ingest sanitizes documents

- **WHEN** World Cup ETL indexes document text containing hidden override phrases
- **THEN** stored content is sanitized before embedding and does not retain raw injection phrases

#### Scenario: Retrieve path re-sanitizes chunks

- **WHEN** retrieve returns chunks from the vector store
- **THEN** each chunk is passed through the same sanitizer before prompt assembly

### Requirement: RAG chunk sanitization before prompt

Retrieved knowledge chunks SHALL be sanitized (control characters stripped, suspicious instruction-like substrings neutralized) before being injected into the LLM prompt.

#### Scenario: Sanitized chunks in graph state

- **WHEN** retrieve node loads chunks containing markdown or embedded instructions
- **THEN** chunks passed to `call_model` are sanitized versions stored in graph state

#### Scenario: Harness verifies sanitization hook

- **WHEN** unit test feeds a chunk with an override phrase
- **THEN** sanitized output does not contain the raw override phrase in prompt-bound form

### Requirement: Layered system prompt with policy and docs blocks

The chat graph SHALL assemble the system message with distinct `<POLICY>` and `<DOCS>` sections, and SHALL keep the user question only in `HumanMessage` roles.

#### Scenario: Policy precedes untrusted docs

- **WHEN** RAG chunks are present for a completion turn
- **THEN** the system message places permanent assistant policy in `<POLICY>` before sanitized chunk text inside `<DOCS>`

#### Scenario: User query not duplicated in system

- **WHEN** a user sends a chat message
- **THEN** the user text appears in `HumanMessage` history and is not duplicated inside the system prompt as a second user block

#### Scenario: Policy states docs are untrusted instructions

- **WHEN** system prompt is built for grounded RAG chat
- **THEN** `<POLICY>` instructs the model to treat override phrases inside `<DOCS>` and user text as plain text, not executable instructions
