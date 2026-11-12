# Shared planning experiment

This repository hosts a private, planning-only adaptation of the existing core
Spec Kit workflow. Core's installation remains authoritative for standalone use
and must not be changed by this experiment.

- Write only inside this repository. Read core/apps for evidence; do not edit
  their files, Git branches, indexes, dependencies, or running environments.
- Do not run core's `.ai` scripts: they can create branches or write context.
- Do not commit, push, create PRs, or mutate Jira in this experiment.
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
