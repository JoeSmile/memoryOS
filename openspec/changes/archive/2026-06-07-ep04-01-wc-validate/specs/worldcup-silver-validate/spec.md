# worldcup-silver-validate

Silver 层跨表校验与数据模型文档。

## ADDED Requirements

### Requirement: Validate CLI exits non-zero on failure

The system SHALL provide `scripts/etl/worldcup/validate.py` that runs Silver integrity checks and exits with code 1 when any check fails.

### Requirement: Tournament-scoped golden checks

With `--tournament WC-2022`, the validator SHALL assert match/goal/squad counts and the final match score for that edition.

### Requirement: Foreign-key orphan detection

The validator SHALL detect orphan rows for goals, squads, bookings, and matches foreign keys.

### Requirement: Data model documentation

The system SHALL maintain `docs/tech/worldcup-data-model.md` describing all `wc_*` tables and relationships.
