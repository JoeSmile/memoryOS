## ADDED Requirements

### Requirement: Chat layout with session sidebar

The web application SHALL provide a chat page with a sidebar listing conversations and a main message area.

#### Scenario: Switch conversation

- **WHEN** user selects a conversation in the sidebar
- **THEN** main area loads that conversation history and subsequent messages use its id

### Requirement: Markdown rendering for assistant messages

Assistant messages SHALL be rendered with Markdown including GFM features after streaming completes.

#### Scenario: Render completed message

- **WHEN** assistant message streaming completes
- **THEN** message content is rendered as Markdown with readable code blocks

### Requirement: Client state with Zustand

Chat session and message UI state SHALL be managed with Zustand stores separate from presentational components.

#### Scenario: Stream updates store

- **WHEN** SSE token events arrive
- **THEN** current assistant message content updates in store without full page reload
