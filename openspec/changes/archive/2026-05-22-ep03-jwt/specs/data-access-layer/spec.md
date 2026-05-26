## ADDED Requirements

### Requirement: Authenticated dependency injection

The API SHALL expose `Depends(get_current_user)` resolving the user from Bearer JWT for protected routes.

#### Scenario: Protected route receives user

- **WHEN** a route declares `user: User = Depends(get_current_user)` and token is valid
- **THEN** the handler receives the ORM user or DTO for the token subject
