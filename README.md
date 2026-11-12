# spec-kit-team-plans

Private, planning-first multi-repository Spec Kit experiment. The standalone
installation in `../core/.ai` is unchanged. This is a lightweight adaptation,
not a full upstream Spec Kit installation or a replacement for core's workflow.

## Boundaries

- All experimental files and generated artifacts live in this repository.
- Core and apps are read-only sources of context except for explicitly approved
  local branch creation using the separate `branch` command.
- No code builds/tests, dependency installs, automatic commits, or Jira updates
  are performed by the workflow. Commit only if authorized. Never push.
- Core includes both server and web-client code; apps owns native applications,
  Electron, and Capacitor plugins.
- AI instructions guide behavior, not an operating-system sandbox. The helper
  CLI has one opt-in mutation: local branch creation/checkout. The AI
  editor/terminal still requires normal permission review.

## Layout

- [Repository mapping](.ai/workspace.json): sibling checkout paths and execution
  environments. Paths resolve from this repository, not the current directory.
- [Workspace CLI](.ai/specify/scripts/bash/workspace-plan.sh): scaffold/inspect
  features and separately preview/apply a local branch.
- [Templates](.ai/specify/templates/): neutral spec, plan, and task scaffolds.
- [Experimental agent](.github/agents/speckit.workspace.agent.md) and
  [prompts](.github/prompts/): distinct names avoid collisions with core.
- `.ai/specs/<feature-id>/`: generated spec, plan, tasks, and baseline metadata.

## From Copilot Chat

In the existing multi-root workspace, check the Agent Customizations editor for
the `speckit.workspace` agent and the four `speckit.workspace.*` prompts. Reload
the window or start a fresh chat if needed. Discovery depends on the selected
harness; it must be verified in the UI, not inferred from file existence.

```text
/speckit.workspace.specify PLAT-12345-example repos=core,apps Describe the feature
/speckit.workspace.plan PLAT-12345-example
/speckit.workspace.tasks PLAT-12345-example
/speckit.workspace.branch PLAT-12345-example repo=core branch=enh/PLAT-12345-example
```

These are AI workflows: they fill the scaffolds from your requirements and
repository evidence, then stop for review. Existing core `/speckit.*` commands
are NOT redirected. Do not use those commands for this experiment.
The branch prompt previews first and asks for approval before applying; it
does not implement tasks or commit code.

If discovery is unavailable, explicitly attach the experimental agent and
instructions to a normal chat and request the relevant planning stage. Do not
change core/apps configuration to make the experiment work.

## From a host workspace terminal

These commands can run from any working directory:

```bash
PLANS="/Users/ricardowatanabebento/IQGeo/spec-kit-team-plans"
bash "$PLANS/.ai/specify/scripts/bash/workspace-plan.sh" create \
  --feature PLAT-12345-example --repos core apps --title "Example feature" --json
bash "$PLANS/.ai/specify/scripts/bash/workspace-plan.sh" context \
  --feature PLAT-12345-example --json
bash "$PLANS/.ai/specify/scripts/bash/workspace-plan.sh" plan \
  --feature PLAT-12345-example --json
bash "$PLANS/.ai/specify/scripts/bash/workspace-plan.sh" tasks \
  --feature PLAT-12345-example --json
```

Requires Python 3.9+ and Git on the host; no additional packages are needed.
The CLI only creates scaffolds, not finished AI-generated content. Edit/review
the spec before planning and the plan before drafting tasks. Scaffold commands
refuse to overwrite existing files; `context` is read-only and can be repeated.
Feature selection is explicit and independent of all repository branch names.

`feature.json` captures the selected repositories' current branch, revision,
and dirty status. `context` reports both that baseline and current state. Neither
operation changes an index or branch. Absolute host paths in generated metadata
are local to this pilot; review them before sharing planning artifacts.

## Devcontainer boundary

The existing core container mounts core at `/opt/iqgeo/platform` and apps at
`/opt/iqgeo/apps`. It does not mount this shared repository. This experiment runs
on the host and does not change mounts or require a container restart.

Plans may describe core CLI validation inside the existing devcontainer, or
native tooling on the host, but must label commands as **not run**. Application
execution routing and code edits are deliberately deferred. Local Git branch
operations run on the host and require no container mount changes.

## Local branch creation

Core's existing feature script accepts a complete branch name, validates it
with `git check-ref-format --branch`, then runs `git checkout -b` and creates
spec artifacts in that checkout. This experiment reuses the full-name validation
and checkout pattern, but leaves all artifacts here and makes branching separate.
It never invokes or modifies core's scripts.

Preview one selected repository from any host terminal:

```bash
bash "$PLANS/.ai/specify/scripts/bash/workspace-plan.sh" branch \
  --feature PLAT-12345-example --repo core \
  --branch enh/PLAT-12345-example --json
```

After reviewing and explicitly approving that repository/name, repeat with
`--apply` to create AND check out the local branch at the captured baseline HEAD.
`--apply` is the CLI's consent flag; the CLI does not maintain an approval token.
The AI workflow must obtain approval before supplying it.

- Use `enh/<TICKET>-<description>` when following core's Jira naming convention.
  Pass a literal full branch name; checkout shorthands are rejected.
- Only repositories selected in this feature can be targeted, one per invocation.
- Preview and apply both reject dirty checkouts (including untracked files),
  detached HEADs, in-progress Git operations, changed path/branch/HEAD since
  feature creation, and existing local branch names.
- No stash, reset, overwrite, branch reuse, fetch, commit, or push is performed.
- Baselines are immutable to the workflow. If a baseline guard fails, stop and
  review it; do not edit metadata automatically to make checkout succeed.
- Branch changes affect the same files seen by other VS Code windows and
  devcontainers. Avoid simultaneous Git operations on the same checkout.
- A second repository needs its own preview/approval. There is no cross-repo
  transaction or automatic rollback. Git failures are reported; inspect current
  state before retrying. Normal local Git hooks may run during checkout.
- `context` shows the original baseline and current state after checkout.
  Spec/plan/task commands still work independently of code branch names.

Implementation, application CLI execution, and container routing remain deferred.

## Validate this toolkit

```bash
python3 -B -m unittest discover -s .ai/specify/tests -p 'test_*.py' -v
```

Tests create disposable fixture repositories inside this repository and remove
them afterward. They do not execute core's scripts or write to core/apps.

Before proposing team adoption, verify customization discovery in a fresh chat
and pilot one real feature. Compare repeated context gathering, planning time,
usage where available, repository ownership accuracy, and fresh-chat resumption.
