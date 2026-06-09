## MODIFIED Requirements

### Requirement: RAG retrieval before generation

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

## ADDED Requirements

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
