#!/usr/bin/env python3
"""Create planning artifacts in the shared repository, never in code repositories."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
SPECS = ROOT / ".ai" / "specs"
TEMPLATES = ROOT / ".ai" / "specify" / "templates"


def git_read(root, *arguments):
    """Read Git metadata without optional index writes."""
    return subprocess.check_output(
        ["git", "--no-optional-locks", "-C", str(root), *arguments],
        text=True,
        stderr=subprocess.PIPE,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    ).strip()


def artifact_path(path):
    """Reject symlinked artifact paths before any read or write."""
    path.relative_to(SPECS)
    for candidate in (path, *path.parents):
        if candidate == ROOT:
            break
        if candidate.is_symlink():
            raise ValueError(f"Planning artifact paths cannot be symlinks: {candidate}")
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError(f"Planning artifact is outside the shared repository: {path}")
    return path


def repository_context(names):
    """Resolve selected sibling checkouts and capture read-only baseline metadata."""
    config = json.loads((ROOT / ".ai" / "workspace.json").read_text())
    repositories = {}
    for name in names:
        entry = config["repositories"][name]
        root = (ROOT / entry["path"]).resolve()
        if root == ROOT or ROOT.is_relative_to(root) or root.is_relative_to(ROOT):
            raise ValueError(f"{name} must be a separate code repository: {root}")
        if Path(git_read(root, "rev-parse", "--show-toplevel")).resolve() != root:
            raise ValueError(f"{name} is not a repository root: {root}")
        repositories[name] = {
            **entry,
            "host_path": str(root),
            "branch": git_read(root, "rev-parse", "--abbrev-ref", "HEAD"),
            "revision": git_read(root, "rev-parse", "HEAD"),
            "status": git_read(root, "status", "--porcelain=v1"),
        }
    return repositories


def load_feature(directory, feature):
    """Load an explicitly selected feature rather than deriving it from a branch."""
    metadata = json.loads(artifact_path(directory / "feature.json").read_text())
    if metadata["feature"] != feature or metadata["mode"] != "planning-only":
        raise ValueError("Feature metadata does not match this planning-only request")
    repositories = metadata["repositories"]
    if not repositories or any(name not in ("core", "apps") for name in repositories):
        raise ValueError("Feature must select core, apps, or both")
    return metadata


def template(name, metadata):
    """Render a neutral template using the selected feature's repository scope."""
    return (
        (TEMPLATES / f"{name}-template.md")
        .read_text()
        .replace("{{TITLE}}", metadata["title"])
        .replace("{{FEATURE}}", metadata["feature"])
        .replace("{{REPOSITORIES}}", ", ".join(metadata["repositories"]))
    )


def create_feature(directory, arguments):
    """Create a new shared feature without creating or changing any Git branch."""
    metadata = {
        "feature": arguments.feature,
        "title": arguments.title,
        "mode": "planning-only",
        "created": datetime.now(timezone.utc).isoformat(),
        "repositories": repository_context(arguments.repos),
    }
    content = template("spec", metadata)
    artifact_path(directory.parent).mkdir(parents=True, exist_ok=True)
    directory.mkdir()
    with artifact_path(directory / "feature.json").open("x") as output:
        output.write(json.dumps(metadata, indent=2) + "\n")
    with artifact_path(directory / "spec.md").open("x") as output:
        output.write(content)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("create", "plan", "tasks", "context"):
        command = commands.add_parser(name)
        command.add_argument("--feature", required=True)
        command.add_argument("--json", action="store_true")
        if name == "create":
            command.add_argument("--repos", nargs="+", choices=("core", "apps"), required=True)
            command.add_argument("--title", required=True)
    arguments = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,119}", arguments.feature):
        parser.error("--feature must be 1-120 letters, digits, hyphens, or underscores")
    if arguments.command == "create":
        if not arguments.title.strip():
            parser.error("--title must not be blank")
        if len(set(arguments.repos)) != len(arguments.repos):
            parser.error("--repos must not contain duplicates")

    try:
        directory = artifact_path(SPECS / arguments.feature)
        if arguments.command == "create":
            metadata = create_feature(directory, arguments)
        else:
            metadata = load_feature(directory, arguments.feature)
            if arguments.command in ("plan", "tasks"):
                required = ["spec.md"]
                if arguments.command == "tasks":
                    required.append("plan.md")
                for name in required:
                    if not artifact_path(directory / name).is_file():
                        raise ValueError(f"Required planning document missing: {name}")
                content = template(arguments.command, metadata)
                with artifact_path(directory / f"{arguments.command}.md").open("x") as output:
                    output.write(content)

        result = {
            "MODE": "planning-only",
            "TOOLKIT_ROOT": str(ROOT / ".ai" / "specify"),
            "FEATURE_DIR": str(directory),
            "FEATURE_SPEC": str(artifact_path(directory / "spec.md")),
            "IMPL_PLAN": str(artifact_path(directory / "plan.md")),
            "TASKS": str(artifact_path(directory / "tasks.md")),
            "AVAILABLE_DOCS": [
                name
                for name in ("spec.md", "plan.md", "tasks.md")
                if artifact_path(directory / name).is_file()
            ],
            "BASELINE": metadata,
        }
        if arguments.command == "context":
            result["CURRENT_REPOSITORIES"] = repository_context(metadata["repositories"])
        print(
            json.dumps(result, indent=2)
            if arguments.json
            else "\n".join(f"{key}: {value}" for key, value in result.items())
        )
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        detail = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) else str(error)
        print(f"ERROR: {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
