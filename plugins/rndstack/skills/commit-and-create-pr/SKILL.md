---
name: commit-and-create-pr
description: Check code quality, run tests, commit changes on a feature branch, and open a GitHub pull request to main. Use when the user asks to commit and create a PR or run this delivery workflow.
---

# Commit and create a PR

Run this workflow in the target repository. Resolve the helper and templates relative to this skill folder. Creating this skill does not authorize running it on its own files.

```text
Inspect → Quality checks → Tests → Feature branch → Stage → Commit → Push → PR → Summary
```

## 1. Inspect and prepare

- Read repository instructions, CI files, package manifests, and task context. Run `git status --short`, `git diff`, `git diff --cached`, and `git branch --show-current`. Inspect untracked files that belong to the task.
- Use the user's task ID and task name. Ask for either if missing; do not invent a task ID. Use lowercase words separated by hyphens for the task name.
- Select only task files. If unrelated edits make scope unclear, ask which files to include. Do not use `git add .` or `git add -A`. Resolve unrelated staged files with the user before proceeding.
- Check `git remote -v`, `gh auth status`, and the target repository. Use `origin` unless the project specifies another remote. Ask if the push repository is unclear. Stop on unresolved merge conflicts or detached HEAD.

## 2. Run quality checks and tests

Prefer the commands used by the repository and CI. Detect every affected language, including packages in a monorepo. Use installed project tools; do not add dependencies or format files merely to run this workflow.

| Language | Sources to inspect | Typical checks when configured |
| --- | --- | --- |
| JavaScript / TypeScript | package.json, lockfiles, CI | lint, format check, typecheck; test and test:e2e scripts |
| Python | pyproject.toml, tox.ini, Makefile, CI | Ruff, Black --check, mypy; pytest |
| Go | go.mod, Makefile, CI | gofmt check, go vet; go test ./... |
| Rust | Cargo.toml, CI | cargo fmt --check, cargo clippy; cargo test |
| Java / Kotlin | Maven or Gradle files, CI | configured checkstyle or lint; test and integration-test tasks |
| .NET | solution and project files, CI | configured format verification or analyzers; dotnet test |
| Other | manifests, build files, CI | repository-defined quality and test commands |

Use non-watch commands. Include available unit, integration, and end-to-end tests. If there are no quality checks, no tests, or a suite needs credentials or services, ask for the missing command or the user's decision to proceed with a recorded limitation. Do not report an absent or skipped suite as passing. Do not weaken failing checks.

Create a temporary JSON plan outside the repository with this structure. Commands are argument arrays, never shell strings. Each command runs from the repository root; use tool-specific directory flags for packages.

```json
{
  "quality": [["npm", "run", "lint"], ["npm", "run", "typecheck"]],
  "tests": [["npm", "test", "--", "--run"], ["npm", "run", "test:e2e"]]
}
```

Run `python3 <skill>/scripts/workflow.py check --plan <plan.json>`. Output streams to the user. Any failure stops execution before Git changes. Fix only issues within the authorized task scope, then rerun affected checks. If checks change files, review and validate the final files again.

## 3. Branch, stage, and commit

- Reuse the current branch if it matches `feature/<task-id>-<task-name>`. If its task differs from the requested task, ask before reusing it. For any other branch, create `feature/<task-id>-<task-name>` with the helper. Do not switch to an existing branch automatically.
- Review the final diff. Select a Conventional Commit message: `<type>[optional scope][optional !]: <description>`. Choose the type from the change, such as `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `perf`, `style`, or `chore`. Include breaking-change details in the body when required.
- Run `python3 <skill>/scripts/workflow.py commit --task-id <id> --task-name <slug> --message <message> -- <file> ...`. Quote each argument. The helper stages the selected paths, rejects unrelated staged paths, and commits. It stops on errors; never bypass commit hooks or force a commit.
- If a hook changes files or fails, inspect the result, rerun checks as needed, and create the commit normally. Do not amend unless the user requests it. If no changes exist, report that and stop unless the user explicitly wants a PR for existing commits.

## 4. Push and create the PR

Explicit invocation of this workflow authorizes the requested commit, push, and PR. If the skill was selected for a narrower request, obtain authorization for the remaining external actions. Respect environment approval requirements.

- Write a PR body to a temporary file. Describe the problem, resulting change, checks run, and any approved limitations. Derive the title from the final change.
- Run `python3 <skill>/scripts/workflow.py pr --title <title> --body-file <body.md> --remote origin`. It pushes the feature branch without force and uses `gh pr create --base main --head <branch> --title ... --body-file ...`. It reuses an open PR for the same head and base. It does not merge.
- On a push or GitHub error, stop and report completed actions. Before retrying an uncertain PR creation, query for an existing PR. Do not create duplicates. Read the PR title and URL from GitHub rather than guessing them.

## 5. Fill the summary template

Use [assets/summary-prompt.md](assets/summary-prompt.md) as the final response prompt. Replace every variable with observed results. Use `Not created` or `Not run: <reason>` when a step is incomplete.

The helper can render [assets/summary.md](assets/summary.md) directly: write a JSON object containing `quality_checks`, `tests`, `branch_name`, `commit_sha`, `commit_message`, `pr_name`, `pr_url`, and `notes`, then run `python3 <skill>/scripts/workflow.py summary --values <results.json>`. Never claim a step succeeded without tool output.
