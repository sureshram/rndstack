#!/usr/bin/env python3
"""Small, fail-fast helpers for the commit-and-create-pr skill."""

import argparse
import json
import logging
from pathlib import Path
import re
import subprocess
import sys

LOG = logging.getLogger("commit-and-create-pr")


def run(*args, capture=False):
    LOG.info("Run %s", args[0])
    result = subprocess.run(args, check=True, text=True,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else ""


def branch():
    value = run("git", "branch", "--show-current", capture=True)
    if not value:
        raise ValueError("Detached HEAD: select a branch first.")
    return value


def is_feature(value):
    return bool(re.fullmatch(r"feature/[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+", value))


def check(args):
    plan = json.loads(Path(args.plan).read_text())
    for group in ("quality", "tests"):
        commands = plan.get(group)
        if not isinstance(commands, list) or not commands:
            raise ValueError(f"Missing {group} commands; ask the user how to proceed.")
        for command in commands:
            if not isinstance(command, list) or not command or not all(
                    isinstance(arg, str) and arg for arg in command):
                raise ValueError("Commands must be nonempty argument arrays.")
    for group in ("quality", "tests"):
        for command in plan[group]:
            LOG.info("%s: %s", group, command)
            run(*command)
    LOG.info("Quality checks and tests passed.")


def commit(args):
    current = branch()
    if run("git", "diff", "--name-only", "--diff-filter=U", capture=True):
        raise ValueError("Resolve merge conflicts first.")
    if not re.fullmatch(r"(?:feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(?:\([^()\n]+\))?!?: [^\n]+(?:\n[\s\S]*)?", args.message):
        raise ValueError("Use a Conventional Commit message.")
    if not re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", args.task_id):
        raise ValueError("Invalid task ID.")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.task_name):
        raise ValueError("Use a lowercase task-name slug.")
    paths = args.files
    if paths and paths[0] == "--":
        paths = paths[1:]
    if not paths:
        raise ValueError("Select task files explicitly.")
    root = Path(run("git", "rev-parse", "--show-toplevel", capture=True)).resolve()
    if Path.cwd().resolve() != root:
        raise ValueError("Run from the repository root.")
    selected = set()
    for value in paths:
        resolved = (root / value).resolve()
        if not resolved.is_relative_to(root) or resolved == root or resolved.is_dir():
            raise ValueError("Select individual files inside the repository.")
        selected.add(resolved.relative_to(root).as_posix())
    staged = run("git", "diff", "--cached", "--name-only", "-z", capture=True)
    if set(filter(None, staged.split("\0"))) - selected:
        raise ValueError("Unrelated staged files exist; resolve scope first.")
    if not is_feature(current):
        run("git", "switch", "-c", f"feature/{args.task_id}-{args.task_name}")
    run("git", "--literal-pathspecs", "add", "--", *sorted(selected))
    if not run("git", "diff", "--cached", "--name-only", capture=True):
        raise ValueError("No changes to commit.")
    run("git", "commit", "-m", args.message)
    print(json.dumps({"branch_name": branch(), "commit_sha": run(
        "git", "rev-parse", "HEAD", capture=True), "commit_message": args.message}))


def pr(args):
    current = branch()
    if not is_feature(current):
        raise ValueError("PR head must use feature/task-id-task-name.")
    if run("git", "status", "--porcelain", capture=True):
        raise ValueError("Working tree has changes; resolve scope before pushing.")
    if not Path(args.body_file).is_file():
        raise ValueError("PR body file does not exist.")
    run("gh", "auth", "status")
    remote_url = run("git", "remote", "get-url", args.remote, capture=True)
    existing = json.loads(run("gh", "pr", "list", "--repo", remote_url,
                              "--head", current, "--base", "main", "--state", "open",
                              "--json", "title,url", capture=True))
    run("git", "push", "--set-upstream", args.remote, current)
    if not existing:
        run("gh", "pr", "create", "--repo", remote_url, "--base", "main", "--head", current,
            "--title", args.title, "--body-file", args.body_file)
    result = run("gh", "pr", "list", "--repo", remote_url, "--head", current,
                 "--base", "main", "--state", "open", "--json", "title,url", capture=True)
    rows = json.loads(result)
    if len(rows) != 1:
        raise ValueError("Cannot identify a unique open PR; inspect GitHub before retrying.")
    print(json.dumps({"pr_name": rows[0]["title"], "pr_url": rows[0]["url"]}))


def summary(args):
    values = json.loads(Path(args.values).read_text())
    template = (Path(__file__).resolve().parent.parent / "assets" / "summary.md").read_text()
    required = set(re.findall(r"\{\{(\w+)\}\}", template))
    if required - values.keys():
        raise ValueError(f"Missing summary values: {sorted(required - values.keys())}")
    print(re.sub(r"\{\{(\w+)\}\}", lambda match: str(values[match[1]]), template), end="")


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    p = subs.add_parser("check")
    p.add_argument("--plan", required=True)
    p = subs.add_parser("commit")
    for flag in ("task-id", "task-name", "message"):
        p.add_argument(f"--{flag}", required=True)
    p.add_argument("files", nargs=argparse.REMAINDER)
    p = subs.add_parser("pr")
    p.add_argument("--title", required=True)
    p.add_argument("--body-file", required=True)
    p.add_argument("--remote", default="origin")
    p = subs.add_parser("summary")
    p.add_argument("--values", required=True)
    args = parser.parse_args()
    try:
        globals()[args.action](args)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        LOG.error("Stopped: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
