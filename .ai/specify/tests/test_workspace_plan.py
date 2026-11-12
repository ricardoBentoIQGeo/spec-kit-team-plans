"""Exercise the isolated planning CLI using disposable sibling repositories."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
FEATURE = "PLAT-12345-example"


class WorkspacePlanningTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="planning-test-", dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.shared = self.base / "plans"
        shutil.copytree(ROOT / ".ai" / "specify" / "scripts", self.shared / ".ai/specify/scripts")
        shutil.copytree(ROOT / ".ai" / "specify" / "templates", self.shared / ".ai/specify/templates")
        shutil.copyfile(ROOT / ".ai" / "workspace.json", self.shared / ".ai/workspace.json")
        self.cli = self.shared / ".ai/specify/scripts/bash/workspace-plan.sh"
        for name in ("core", "apps"):
            repository = self.base / name
            repository.mkdir()
            self.git(repository, "init", "-q")
            self.git(
                repository,
                "-c", "user.name=Planning Fixture",
                "-c", "user.email=fixture@example.invalid",
                "-c", "core.hooksPath=/dev/null",
                "commit", "-q", "--allow-empty", "-m", "Fixture baseline",
            )
        self.before = self.code_state()

    def tearDown(self):
        self.assertEqual(self.code_state(), self.before)

    def git(self, repository, *arguments):
        return subprocess.check_output(
            ["git", "--no-optional-locks", "-C", str(repository), *arguments],
            text=True,
            stderr=subprocess.PIPE,
        ).strip()

    def code_state(self):
        return {
            name: (
                self.git(self.base / name, "rev-parse", "HEAD"),
                self.git(self.base / name, "rev-parse", "--abbrev-ref", "HEAD"),
                self.git(self.base / name, "status", "--porcelain=v1"),
                self.git(self.base / name, "for-each-ref", "--format=%(refname):%(objectname)"),
            )
            for name in ("core", "apps")
        }

    def run_cli(self, command, *arguments, cwd=None, success=True):
        result = subprocess.run(
            ["bash", str(self.cli), command, "--feature", FEATURE, "--json", *arguments],
            cwd=cwd or self.shared,
            text=True,
            capture_output=True,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Traceback", result.stderr)
        return result.stderr

    def create(self, *repositories):
        return self.run_cli(
            "create", "--repos", *repositories, "--title", "Cross-repository example"
        )

    def test_shared_artifacts_are_independent_of_working_directory_and_branches(self):
        result = self.run_cli(
            "create", "--repos", "core", "apps", "--title", "Shared example",
            cwd=self.base / "core",
        )
        self.assertEqual(set(result["BASELINE"]["repositories"]), {"core", "apps"})
        self.run_cli("plan", cwd=self.base / "apps")
        self.run_cli("tasks", cwd=self.base)
        context = self.run_cli("context", cwd=self.base / "core")
        self.assertEqual(context["AVAILABLE_DOCS"], ["spec.md", "plan.md", "tasks.md"])
        self.assertEqual(Path(context["FEATURE_DIR"]), self.shared / ".ai/specs" / FEATURE)
        self.assertEqual(
            context["CURRENT_REPOSITORIES"]["core"]["host_path"], str(self.base / "core")
        )

    def test_scaffolding_never_overwrites_existing_work(self):
        self.create("apps")
        directory = self.shared / ".ai/specs" / FEATURE
        spec = directory / "spec.md"
        spec.write_text("Reviewed specification\n")
        self.run_cli("create", "--repos", "apps", "--title", "Duplicate", success=False)
        self.assertEqual(spec.read_text(), "Reviewed specification\n")
        self.run_cli("plan")
        plan = directory / "plan.md"
        plan.write_text("Reviewed plan\n")
        self.run_cli("plan", success=False)
        self.assertEqual(plan.read_text(), "Reviewed plan\n")
        self.run_cli("tasks")
        tasks = directory / "tasks.md"
        tasks.write_text("Reviewed tasks\n")
        self.run_cli("tasks", success=False)
        self.assertEqual(tasks.read_text(), "Reviewed tasks\n")

    def test_selected_repository_and_baseline_remain_explicit(self):
        created = self.create("apps")
        metadata_path = self.shared / ".ai/specs" / FEATURE / "feature.json"
        before = metadata_path.read_bytes()
        context = self.run_cli("context")
        self.assertEqual(list(context["CURRENT_REPOSITORIES"]), ["apps"])
        self.assertEqual(context["BASELINE"], created["BASELINE"])
        self.assertEqual(metadata_path.read_bytes(), before)

    def test_missing_prerequisites_and_invalid_selection_fail_clearly(self):
        self.assertIn("ERROR:", self.run_cli("context", success=False))
        for arguments in (
            ("--repos", "unknown", "--title", "Invalid"),
            ("--repos", "core", "core", "--title", "Duplicate"),
            ("--repos", "core", "--title", " "),
            ("--repos", "core", "--title", "Traversal", "--feature", "../escape"),
        ):
            with self.subTest(arguments=arguments):
                self.run_cli("create", *arguments, success=False)
        self.assertFalse((self.shared / ".ai/specs").exists())
        self.create("core")
        self.assertIn("plan.md", self.run_cli("tasks", success=False))
        self.assertFalse((self.shared / ".ai/specs" / FEATURE / "tasks.md").exists())

    def test_symlinked_artifacts_cannot_redirect_writes(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.shared / ".ai/specs").symlink_to(outside, target_is_directory=True)
        error = self.run_cli(
            "create", "--repos", "core", "--title", "Redirected", success=False
        )
        self.assertIn("symlinks", error)
        self.assertEqual(list(outside.iterdir()), [])
        (self.shared / ".ai/specs").unlink()
        self.create("core")
        destination = outside / "plan.md"
        destination.write_text("Do not overwrite\n")
        (self.shared / ".ai/specs" / FEATURE / "plan.md").symlink_to(destination)
        self.assertIn("symlinks", self.run_cli("plan", success=False))
        self.assertEqual(destination.read_text(), "Do not overwrite\n")

    def test_branch_preview_then_apply_targets_only_selected_checkout(self):
        created = self.create("core", "apps")
        feature_json = self.shared / ".ai/specs" / FEATURE / "feature.json"
        original = feature_json.read_bytes()
        branch = f"enh/{FEATURE}"
        preview = self.run_cli("branch", "--repo", "core", "--branch", branch, cwd=self.base / "apps")
        self.assertEqual(preview["MODE"], "local-branch-preview")
        self.assertFalse(preview["BRANCH"]["APPLIED"])
        self.assertEqual(self.code_state(), self.before)
        self.assertEqual(preview["BRANCH"]["COMMAND"], [
            "git", "-C", str(self.base / "core"), "checkout", "-b", branch,
            created["BASELINE"]["repositories"]["core"]["revision"],
        ])
        applied = self.run_cli("branch", "--repo", "core", "--branch", branch, "--apply")
        self.assertEqual(applied["MODE"], "local-branch-apply")
        self.assertTrue(applied["BRANCH"]["APPLIED"])
        after = self.code_state()
        self.assertEqual(after["apps"], self.before["apps"])
        self.assertEqual(after["core"][:3], (self.before["core"][0], branch, ""))
        self.assertIn(f"refs/heads/{branch}:", after["core"][3])
        self.assertEqual(feature_json.read_bytes(), original)
        self.before = after
        self.run_cli("plan")
        self.run_cli("tasks")
        context = self.run_cli("context")
        self.assertEqual(context["CURRENT_REPOSITORIES"]["core"]["branch"], branch)
        self.assertEqual(context["BASELINE"], created["BASELINE"])
        self.assertIn("changed since", self.run_cli(
            "branch", "--repo", "core", "--branch", "enh/another", "--apply", success=False
        ))

    def test_apps_branch_can_use_its_own_literal_name_without_touching_core(self):
        self.create("apps")
        branch = "feature/native-only-experiment"
        result = self.run_cli(
            "branch", "--repo", "apps", "--branch", branch, "--apply", cwd=self.base / "core"
        )
        self.assertEqual(result["BRANCH"]["HOST_PATH"], str(self.base / "apps"))
        after = self.code_state()
        self.assertEqual(after["core"], self.before["core"])
        self.assertEqual(after["apps"][:3], (self.before["apps"][0], branch, ""))
        self.assertIn(f"refs/heads/{branch}:", after["apps"][3])
        self.before = after

    def test_branch_rejects_dirty_checkout_before_creating_refs(self):
        repository = self.base / "core"
        tracked = repository / "tracked.txt"
        tracked.write_text("baseline\n")
        self.git(repository, "add", "tracked.txt")
        self.git(
            repository, "-c", "user.name=Planning Fixture", "-c", "user.email=fixture@example.invalid",
            "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "Tracked fixture",
        )
        self.create("core", "apps")
        tracked.write_text("modified\n")
        for staged in (False, True):
            if staged:
                self.git(repository, "add", "tracked.txt")
            self.before = self.code_state()
            self.assertIn("changes", self.run_cli(
                "branch", "--repo", "core", "--branch", f"enh/{FEATURE}", "--apply", success=False
            ))
            self.assertEqual(self.code_state(), self.before)
        untracked = self.base / "apps" / "untracked.txt"
        untracked.write_text("new\n")
        self.before = self.code_state()
        self.assertIn("changes", self.run_cli(
            "branch", "--repo", "apps", "--branch", f"enh/{FEATURE}", "--apply", success=False
        ))

    def test_branch_rejects_unselected_existing_and_invalid_names(self):
        self.create("core")
        self.assertIn("not selected", self.run_cli(
            "branch", "--repo", "apps", "--branch", f"enh/{FEATURE}", "--apply", success=False
        ))
        self.assertIn("already exists", self.run_cli(
            "branch", "--repo", "core", "--branch", self.before["core"][1], "--apply", success=False
        ))
        for branch in ("bad name", "../escape", "-invalid", "@{-1}"):
            with self.subTest(branch=branch):
                self.run_cli("branch", "--repo", "core", f"--branch={branch}", "--apply", success=False)

    def test_branch_rejects_changed_head_mapping_and_operations(self):
        self.create("core")
        metadata = self.shared / ".ai/specs" / FEATURE / "feature.json"
        original = json.loads(metadata.read_text())
        for field, value in (("revision", "0" * 40), ("branch", "other"), ("host_path", "/different")):
            data = json.loads(json.dumps(original))
            data["repositories"]["core"][field] = value
            metadata.write_text(json.dumps(data))
            self.run_cli("branch", "--repo", "core", "--branch", f"enh/{FEATURE}", "--apply", success=False)
        metadata.write_text(json.dumps(original))
        repository = self.base / "core"
        state = repository / ".git/rebase-merge"
        state.mkdir()
        self.assertIn("operation in progress", self.run_cli(
            "branch", "--repo", "core", "--branch", f"enh/{FEATURE}", "--apply", success=False
        ))
        state.rmdir()
        self.git(repository, "-c", "core.hooksPath=/dev/null", "checkout", "--detach", "-q")
        self.before = self.code_state()
        self.assertIn("detached", self.run_cli(
            "branch", "--repo", "core", "--branch", f"enh/{FEATURE}", "--apply", success=False
        ))

    def test_checkout_hook_failure_is_reported_without_automatic_rollback(self):
        repository = self.base / "core"
        hooks = repository / ".git/hooks"
        self.git(repository, "config", "core.hooksPath", str(hooks))
        hook = hooks / "post-checkout"
        hook.write_text("#!/bin/sh\nprintf 'Fixture checkout hook failed\\n' >&2\nexit 1\n")
        hook.chmod(0o755)
        self.create("core")
        branch = f"enh/{FEATURE}"
        error = self.run_cli(
            "branch", "--repo", "core", "--branch", branch, "--apply", success=False
        )
        self.assertIn("Fixture checkout hook failed", error)
        self.assertIn("No rollback attempted", error)
        after = self.code_state()
        self.assertEqual(after["apps"], self.before["apps"])
        self.assertEqual(after["core"][:3], (self.before["core"][0], branch, ""))
        self.before = after


if __name__ == "__main__":
    unittest.main()
