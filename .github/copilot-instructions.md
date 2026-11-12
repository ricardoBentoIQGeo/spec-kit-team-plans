# Shared planning experiment

This repository hosts a private, planning-first adaptation of the existing core
Spec Kit workflow. Core's installation remains authoritative for standalone use
and must not be changed by this experiment.

- Write artifacts only inside this repository. Read core/apps for evidence;
  do not edit their files, indexes, dependencies, or running environments.
  The only code-repository mutation allowed here is the shared CLI's `branch`
  command after explicit approval for that repository and branch.
- Do not run core's `.ai` scripts: they can create branches or write context.
- Never push. Commit only when explicitly authorized by the user. Do not
  create PRs or mutate Jira in this experiment.
- Use the uniquely named `speckit.workspace.*` prompts for this experiment,
  not the existing `speckit.*` workflows from core.
- Select a feature explicitly and require core/apps ownership for every task.
  Never infer the feature or target repository from the terminal directory.
- Run this repository's `.ai/specify/scripts/bash/workspace-plan.sh` using its
  absolute path, resolved from the shared workspace folder.
- `.ai/workspace.json` maps repository paths relative to this repository.
  `feature.json` captures baseline context; the context command reads current
  state without rewriting the baseline.
- Core contains server AND web-client code. Apps contains native applications,
  Electron, and Capacitor plugins. Load only relevant repository-local
  instructions, manifests, and source files.
- Templates are scaffolds, not completed or accepted specifications/plans.
  Cite actual source evidence, leave unknowns explicit, and request review.
- Plan exact validation commands and environments, but do not execute builds,
  tests, containers, or application CLIs against core/apps.
- Feature artifacts are the handoff between chats; do not load unrelated specs.
- Branch creation is separate from specify/plan/tasks. Preview one repository
  with `branch --feature <id> --repo <core|apps> --branch <full-name> --json`.
  Show the checkout path, current branch/HEAD, and proposed name. Ask for
  explicit approval before repeating the command with `--apply`.
- Prefer core's `enh/<TICKET>-<description>` naming when a Jira ID is supplied;
  pass the full name literally, without deriving repository scope from it.
  Do not auto-run core scripts, overwrite feature baselines, stash changes,
  reset, reuse an existing branch, or switch an unexpected checkout.
- Applying checks out a local branch at the feature's captured baseline HEAD.
  It requires a clean checkout, matching baseline path/branch/HEAD, and no
  operation in progress. Never auto-refresh a stale baseline to bypass a guard.
  Each repository requires its own preview/approval; there is no cross-repo
  transaction or automatic rollback. Branch changes are visible in other
  windows/devcontainers sharing the same checkout.
