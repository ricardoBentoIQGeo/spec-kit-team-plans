---
agent: speckit.workspace
description: Preview one repository's local feature branch; apply only after explicit approval.
---

Run the Branch stage of the workspace workflow for:

$ARGUMENTS

Require an existing feature ID, one selected repository, and a complete branch
name. Preview first, then ask for approval of the exact repository and branch
before applying. Never push, stash, reset, or run standalone core scripts.
