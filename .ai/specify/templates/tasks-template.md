# Tasks: {{TITLE}}

**Feature ID**: {{FEATURE}}
**Repositories**: {{REPOSITORIES}}
**Input**: [spec.md](./spec.md), [plan.md](./plan.md)
**Mode**: Planning only - these are proposed implementation tasks, not executable authorization
**Status**: Draft scaffold - populate from the reviewed specification and plan

## Task format

Use an unchecked item per task:

`- [ ] T001 [repo:core|apps|shared] [environment:host|devcontainer] Description`

Replace alternatives with exactly one repository and environment. Each task
must state repository-relative paths, acceptance criteria, validation commands,
and explicit prerequisite task IDs (or "none"). Only use selected repositories;
shared means planning/contract artifacts in this repository.

## Proposed implementation tasks

[Group by user story and dependency order. Include focused validation for
introduced/fixed behavior. Do not perform or mark implementation tasks complete.]

## Cross-repository dependencies

[List producer/consumer dependencies and what can run independently.]

## Future execution gate

Implementation, branch creation, commits, pushes, builds/tests against code
repositories, and Jira mutations require a separate user-approved workflow.
