## ADDED Requirements

### Requirement: Seven-phase EP02 delivery order

The project SHALL complete EP02 work in seven ordered phases documented in `openspec/changes/ep02-program/tasks.md` before starting EP04 or later feature epics.

#### Scenario: Phase gate

- **WHEN** phases 1 through 7 are not all marked complete in ep02-program tasks
- **THEN** team does not begin OpenSpec apply for EP04+ feature changes

#### Scenario: Phase completion

- **WHEN** a phase is marked complete
- **THEN** its listed child change(s) are archived and verification commands in tasks.md have passed
