## ADDED Requirements

### Requirement: Minimal chat StateGraph

The API layer SHALL provide a LangGraph-based chat graph with explicit state containing conversation messages and user identity.

#### Scenario: Graph invokes model node

- **WHEN** graph is executed with valid initial state containing user messages
- **THEN** execution reaches model node and produces assistant message content

### Requirement: Streaming token output

The graph runner SHALL expose an async stream of text tokens suitable for SSE forwarding.

#### Scenario: Stream tokens

- **WHEN** runner streams for a valid state
- **THEN** consumer receives one or more non-empty token strings before stream completion

### Requirement: Mock execution without API key

When OpenAI credentials are not configured, the system SHALL use a mock model path that completes without external network calls.

#### Scenario: Mock stream in tests

- **WHEN** unit or harness tests run without OpenAI API key
- **THEN** token stream completes with deterministic content

### Requirement: LangSmith tracing when enabled

When LangSmith environment variables are set, graph and model runs SHALL be traced to the configured project.

#### Scenario: Trace present

- **WHEN** `LANGCHAIN_TRACING_V2` is true and API key is valid
- **THEN** a trace run is created for graph execution (verified manually or via test double)
