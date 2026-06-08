## ADDED Requirements

### Requirement: RAG reference section in assistant Markdown

The chat UI SHALL render assistant messages that include a `## 参考来源` Markdown section with readable styling distinct from the main answer body.

#### Scenario: Reference section visible after stream

- **WHEN** assistant streaming completes and content includes `## 参考来源`
- **THEN** the reference block is displayed below the main answer with subdued typography or collapsible presentation

#### Scenario: Messages without references unchanged

- **WHEN** assistant content has no reference heading
- **THEN** message layout matches pre-RAG chat rendering
