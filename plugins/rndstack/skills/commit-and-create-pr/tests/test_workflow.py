"""End-to-end CLI tests using isolated Git repositories and a fake gh command."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "workflow.py"


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        (self.repo / "app.txt").write_text("initial\n")
        self.git("add", "app.txt")
        self.git("commit", "-m", "chore: initial")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, text=True).strip()

    def cli(self, *args, env=None):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.repo,
                              env=env, text=True, capture_output=True)

    def commit(self):
        (self.repo / "app.txt").write_text("changed\n")
        result = self.cli("commit", "--task-id", "TASK-42", "--task-name", "update-app",
                          "--message", "fix: update app", "--", "app.txt")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_commit_creates_branch_and_reuses_it(self):
        self.commit()
        self.assertEqual(self.git("branch", "--show-current"), "feature/TASK-42-update-app")
        self.assertEqual(self.git("log", "-1", "--format=%s"), "fix: update app")
        self.assertEqual(self.git("status", "--porcelain"), "")
        (self.repo / "app.txt").write_text("second change\n")
        result = self.cli("commit", "--task-id", "TASK-42", "--task-name", "update-app",
                          "--message", "fix: follow up", "--", "app.txt")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unrelated_staged_file_blocks_commit(self):
        (self.repo / "other.txt").write_text("unrelated")
        self.git("add", "other.txt")
        result = self.cli("commit", "--task-id", "42", "--task-name", "app",
                          "--message", "fix: app", "--", "app.txt")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("branch", "--show-current"), "main")

    def test_check_failure_stops_remaining_commands(self):
        marker = self.root / "tests-ran"
        plan = self.root / "plan.json"
        plan.write_text(json.dumps({"quality": [[sys.executable, "-c", "raise SystemExit(2)"]],
                                    "tests": [[sys.executable, "-c",
                                               f"open({str(marker)!r}, 'w').close()"]]}))
        result = self.cli("check", "--plan", str(plan))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())
        plan.write_text(json.dumps({"quality": [[sys.executable, "-c", "pass"]],
                                    "tests": [[sys.executable, "-c", "pass"]]}))
        self.assertEqual(self.cli("check", "--plan", str(plan)).returncode, 0)

    def test_push_and_pr_and_summary(self):
        self.commit()
        remote = self.root / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        self.git("remote", "add", "origin", str(remote))
        gh = self.root / "gh"
        log = self.root / "gh.log"
        state = self.root / "created"
        gh.write_text(f"#!{sys.executable}\n" +
                      "import json, pathlib, sys\n" +
                      f"state = pathlib.Path({str(state)!r})\n" +
                      f"with open({str(log)!r}, 'a') as f: f.write(json.dumps(sys.argv[1:]) + '\\n')\n" +
                      "if sys.argv[1:3] == ['pr', 'create']: state.touch()\n" +
                      "if sys.argv[1:3] == ['pr', 'list']:\n" +
                      " print(json.dumps([{'title': 'fix: update app', 'url': 'https://example.invalid/pull/1'}] if state.exists() else []))\n")
        gh.chmod(0o755)
        env = dict(os.environ, PATH=str(self.root) + os.pathsep + os.environ["PATH"])
        body = self.root / "body.md"
        body.write_text("Change and validation details.")
        for _ in range(2):
            result = self.cli("pr", "--title", "fix: update app", "--body-file", str(body), env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        creates = [call for call in calls if call[:2] == ["pr", "create"]]
        self.assertEqual(len(creates), 1)
        self.assertEqual(creates[0][creates[0].index("--base") + 1], "main")
        self.assertEqual(self.git("rev-parse", "HEAD"), subprocess.check_output(
            ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/feature/TASK-42-update-app"], text=True).strip())
        values = dict(quality_checks="Passed", tests="Passed", branch_name="feature/TASK-42-update-app",
                      commit_sha=self.git("rev-parse", "HEAD"), commit_message="fix: update app",
                      pr_name="fix: update app", pr_url="https://example.invalid/pull/1", notes="None")
        data = self.root / "results.json"
        data.write_text(json.dumps(values))
        result = self.cli("summary", "--values", str(data))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("{{", result.stdout)
        self.assertIn(values["pr_url"], result.stdout)


if __name__ == "__main__":
    unittest.main()
