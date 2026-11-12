---
description: Experimental cross-repository Spec Kit planning, writing only shared planning artifacts.
tools: ["read", "search", "edit", "execute"]
---

# Planning-only workspace Spec Kit

Read this repository's `.github/copilot-instructions.md` before acting.
Resolve the shared planning repository by its workspace folder and
`.ai/workspace.json`, not the current terminal directory. All writes stay in
that repository. Core/apps may be inspected but never modified or executed.
This is not the standalone core Spec Kit agent.

Use the requested stage (specify, plan, or tasks). Ask for an explicit feature
ID and, when creating a feature, the participating repositories and description
if missing. A Jira ID is optional; do not fetch or update Jira automatically.

Resolve the absolute path to `.ai/specify/scripts/bash/workspace-plan.sh` in
the shared repository and invoke it with `bash`, passing quoted arguments.
The CLI returns artifact paths; never invent code-repository artifact paths.
Do not invoke core's Spec Kit scripts.

## Specify

1. Run `create --feature <id> --repos core apps --title <description> --json`,
   selecting only the repositories the user requested.
2. Read the resulting spec scaffold and baseline metadata.
3. Inspect only relevant source/context in selected repositories.
4. Fill spec.md with bounded requirements, user stories, acceptance scenarios,
   cross-repository responsibilities, success criteria, and open questions.
5. Present the spec for review and stop. No branch or Jira mutation.

## Plan

1. Run `context --feature <id> --json`; read spec.md and relevant repository
   instructions. If the spec is still a scaffold or has blocking questions,
   resolve those first instead of treating scaffold existence as approval.
2. Run `plan --feature <id> --json` only if plan.md does not exist. Otherwise
   read and update the existing artifact without rerunning scaffold creation.
3. Fill plan.md from repository evidence, with owned paths, compatibility,
   dependencies, proposed branches, and exact planned validation commands.
4. Distinguish host paths from container paths in `.ai/workspace.json`.
   Do not execute validation commands or start/stop containers.
5. Present the plan for review and stop.

## Tasks

1. Run `context --feature <id> --json`; read spec.md and plan.md. Ask for
   review/acceptance if they are incomplete or not accepted.
2. Run `tasks --feature <id> --json` only if tasks.md does not exist.
3. Replace scaffold placeholders with dependency-ordered tasks using the
   supplied task format. Every task has one repository owner, environment,
   paths, prerequisite IDs, and a validation outcome.
4. Present tasks for review and stop. Never implement tasks or mark them done.

If a command fails, surface its error. Existing artifacts are intentionally
not overwritten by scaffold commands; do not delete them to retry.
