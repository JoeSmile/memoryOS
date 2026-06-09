# rag-chat Specification

## Purpose

RAG-augmented chat completions (EP04) extended with Unified ReAct (EP05): retrieve before agent loop, citation sources, and optional `tavily_search` via model-driven tool rounds.
## Requirements
### Requirement: LangGraph retrieve before generation

The chat graph SHALL run a `retrieve_knowledge` step before the ReAct agent loop, querying ingested knowledge with the latest user message text and injecting results into agent state and system prompt context.

#### Scenario: Retrieve runs before first model call

- **WHEN** chat completion starts for a unified ReAct request
- **THEN** `retrieve_knowledge` executes before the first `call_model` node in the ReAct loop

#### Scenario: Qualifying hits emit sources SSE

- **WHEN** retrieval returns qualifying chunks at or above the minimum score threshold
- **THEN** the stream emits RAG `sources` events and persists `metadata.rag_sources` as today

#### Scenario: Model may invoke web search after weak retrieval

- **WHEN** retrieval is insufficient for the user question
- **THEN** the model MAY invoke `tavily_search` through the ReAct tool loop rather than relying on a fixed no-hit-only response

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

### Requirement: Unified ReAct agent loop after retrieval

After retrieval, the chat graph SHALL enter a ReAct loop where the model may request tools, observe ToolMessage results, and iterate until producing a final assistant answer without tool_calls.

#### Scenario: Sufficient retrieval answered without tools

- **WHEN** retrieval provides adequate context and the model responds without tool_calls
- **THEN** the graph completes after one model pass with RAG sources only and no tool SSE events

#### Scenario: Insufficient retrieval triggers model tool use

- **WHEN** retrieval is weak and the model determines external search is needed
- **THEN** the graph executes `tavily_search` through the ReAct loop and incorporates results before final answer

#### Scenario: Tools disabled rolls back to legacy path

- **WHEN** agent tools are disabled via configuration
- **THEN** the graph behaves as pre-ReAct retrieve-then-generate without tool loop

### Requirement: Tool steps persisted on assistant message

When a unified ReAct completion executes one or more tool rounds, the system SHALL persist structured tool step items on the assistant message metadata before the stream ends.

#### Scenario: Metadata written on finalize with tools

- **WHEN** chat completion completes after at least one tool round
- **THEN** the persisted assistant message has `metadata.tool_steps` equal to the executed tool step array

#### Scenario: No tool_steps when no tools run

- **WHEN** chat completion completes without any tool invocations
- **THEN** the assistant message metadata omits `tool_steps` or leaves it empty

#### Scenario: List messages returns tool_steps

- **WHEN** client lists messages for a conversation
- **THEN** each assistant message includes `metadata.tool_steps` when present for UI timeline rendering

#### Scenario: Interrupted stream preserves completed tool steps

- **WHEN** user stops streaming after one or more tool_result events were emitted
- **THEN** the interrupted assistant message metadata includes tool steps completed before stop

