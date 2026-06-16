# rag-retrieval Specification (Delta)

## ADDED Requirements

### Requirement: Ingest-time sanitization before embedding

World Cup and knowledge ingest pipelines SHALL run document text through the shared `rag_sanitizer` module before chunking and embedding.

#### Scenario: Poisoned source neutralized at ingest

- **WHEN** ingest receives text with indirect injection phrases
- **THEN** embedded chunks do not contain the raw injection phrase in retrievable form

### Requirement: Retrieved chunks sanitized before LLM prompt

Chunks loaded by the chat graph retrieve node SHALL pass through the shared `rag_sanitizer` module before being formatted into the model prompt.

#### Scenario: Sanitized chunks used in call_model

- **WHEN** retrieve returns chunks from vector search
- **THEN** `call_model` receives sanitized chunk text only

#### Scenario: Empty after sanitization still safe

- **WHEN** sanitization removes all content from a chunk
- **THEN** chunk is omitted from prompt rather than injecting empty override markers
