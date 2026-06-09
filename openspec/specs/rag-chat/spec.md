# rag-chat Specification

## Purpose
TBD - created by archiving change ep04-rag-chat. Update Purpose after archive.
## Requirements
### Requirement: LangGraph retrieve before generation

The chat graph SHALL run a `retrieve_knowledge` step before `call_model` when RAG chat is enabled, querying ingested knowledge with the latest user message text.

#### Scenario: Retrieve runs on user question

- **WHEN** authenticated user sends a chat completion and `RAG_CHAT_ENABLED` is true with ingested World Cup data
- **THEN** the graph executes retrieve before streaming assistant tokens

#### Scenario: RAG disabled skips retrieve

- **WHEN** `RAG_CHAT_ENABLED` is false
- **THEN** the graph streams assistant tokens without calling knowledge search

### Requirement: RAG system prompt with grounded context

The model invocation SHALL include a system message built from retrieved chunks that instructs the assistant to answer only from provided references and to append a Markdown `## 参考来源` section citing `external_id` values.

#### Scenario: Prompt includes top chunks

- **WHEN** retrieve returns chunks above `RAG_CHAT_MIN_SCORE`
- **THEN** the system message contains those chunk texts and citation instructions before user/assistant history

#### Scenario: No-hit fallback

- **WHEN** no chunks meet `RAG_CHAT_MIN_SCORE` after retrieve
- **THEN** the system message instructs the assistant to state that the knowledge base has no relevant facts and not to invent match or player statistics

### Requirement: Chat SSE sources event

Chat completions streaming SHALL emit a `sources` SSE event after retrieval completes and before the first `token` event when RAG is enabled and at least one chunk passes the score threshold.

#### Scenario: Sources event shape

- **WHEN** retrieve yields qualifying chunks
- **THEN** a line is sent as `{"event":"sources","data":{"items":[{"external_id":"...","collection":"...","score":0.0,"content_preview":"..."}]}}`

#### Scenario: No sources when below threshold

- **WHEN** all retrieved chunks are below `RAG_CHAT_MIN_SCORE`
- **THEN** no `sources` event is emitted and the no-hit fallback prompt applies

### Requirement: RAG chat harness without external API

When `OPENAI_API_KEY` is unset, the RAG chat path SHALL work end-to-end using mock embeddings and mock LLM after ingesting seeded fact cards.

#### Scenario: Mock RAG chat completion

- **WHEN** harness ingests `samples`, posts a chat question matching seeded content, and streams completion
- **THEN** response includes a `sources` event with at least one item and completes with `token` and `done` events

### Requirement: RAG sources persisted with assistant message

When RAG chat completes with qualifying retrieval hits, the system SHALL store structured source items on the assistant message for reload and audit.

#### Scenario: Sources in message metadata after stream

- **WHEN** harness completes a RAG chat stream with sources events
- **THEN** fetching the assistant message by conversation list returns `metadata.rag_sources` with matching `external_id` values

#### Scenario: Mock path without external API

- **WHEN** harness runs RAG chat without `OPENAI_API_KEY` after ingesting samples
- **THEN** persisted assistant message metadata includes at least one rag source item

