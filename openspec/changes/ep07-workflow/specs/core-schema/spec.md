## ADDED Requirements

### Requirement: Workflow run persistence

The database schema SHALL include `workflow_runs` and `workflow_run_steps` tables owned by `users`, storing run status, input payload, result payload, and ordered step logs.

#### Scenario: Run created for authenticated user

- **WHEN** an authenticated user starts a workflow run
- **THEN** a `workflow_runs` row is created with `user_id`, `workflow_slug`, and `status` pending or running

#### Scenario: Steps recorded in order

- **WHEN** a workflow executor advances through LangGraph nodes
- **THEN** corresponding `workflow_run_steps` rows are created or updated with stable `step_key` and monotonic `order_index`

#### Scenario: User isolation

- **WHEN** user A requests workflow run owned by user B
- **THEN** API returns not found per project envelope convention

### Requirement: Workflow run step lifecycle columns

Each `workflow_run_steps` row SHALL track `status`, optional input/output summaries, and start/finish timestamps suitable for UI step bars.

#### Scenario: Step transitions on node start

- **WHEN** a LangGraph node begins execution for a run
- **THEN** the matching step row status becomes running and `started_at` is set

#### Scenario: Step completes with summary

- **WHEN** a LangGraph node finishes successfully
- **THEN** the step row status becomes succeeded and `output_summary` captures a bounded text summary for UI display
