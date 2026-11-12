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


if __name__ == "__main__":
    unittest.main()
