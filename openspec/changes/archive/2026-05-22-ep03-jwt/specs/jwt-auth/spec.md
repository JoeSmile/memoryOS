## ADDED Requirements

### Requirement: User registration with password hashing

The API SHALL provide `POST /api/v1/auth/register` accepting email and password, storing bcrypt hash in `users.password_hash`.

#### Scenario: Register success

- **WHEN** client posts valid unique email and password meeting minimum length
- **THEN** response returns `code` 0 and `data` containing user id and email without password fields

#### Scenario: Register duplicate email

- **WHEN** email already exists
- **THEN** response returns appropriate business error with non-2xx HTTP status

### Requirement: User login issues JWT

The API SHALL provide `POST /api/v1/auth/login` returning access token on valid credentials.

#### Scenario: Login success

- **WHEN** email and password match stored hash
- **THEN** response `data` includes `access_token` and `token_type` bearer

#### Scenario: Login invalid credentials

- **WHEN** email or password is wrong
- **THEN** response returns 401 with unified error envelope

### Requirement: Current user endpoint

The API SHALL provide `GET /api/v1/me` requiring valid Bearer JWT.

#### Scenario: Me with valid token

- **WHEN** request includes valid non-expired Bearer token
- **THEN** response returns `code` 0 and current user profile in `data`

#### Scenario: Me without token

- **WHEN** Authorization header is missing or invalid
- **THEN** response returns 401

### Requirement: JWT configuration from environment

`JWT_SECRET` and token expiry settings SHALL be loaded via pydantic-settings with documented `.env.example` entries.

#### Scenario: Secret configured

- **WHEN** `JWT_SECRET` is set at startup
- **THEN** issued tokens can be validated by the application
