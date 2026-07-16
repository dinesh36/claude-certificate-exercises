---
name: ship-exercise
description: Take a built exercise (or any exercise-folder change) through the full git/PR lifecycle — branch, commit, PR, merge, and sync master back up. Use when the user asks to open a PR, ship, land, or merge an exercise.
allowed-tools: Bash, Read, Grep
---

# Ship Exercise

Runs the git/GitHub side of landing one exercise's work: branch → commit → PR → merge → resync `master`. This is the workflow that follows building or updating an exercise (e.g. with the `new-exercise` skill) — it does not touch exercise content itself.

## 1. Identify what's being shipped

- `git status --short` to see every changed/untracked file, not just what's inside the exercise folder. Ship the whole body of work for this exercise: its `exercises/<domain-slug>/task-<N>-<slug>/` folder, plus anything else touched to build or land it — `common/` additions or edits, the `CLAUDE.md` Exercises-table row, README/skill updates, wiki cross-references, etc. None of that should be left behind uncommitted just because it lives outside the exercise folder.
- Only exclude a changed file if it's genuinely unrelated to this exercise (e.g. leftover edits from a different task). If you're not sure whether something belongs, ask the user rather than guessing either way — don't silently drop it and don't silently bundle it in.
- If the remaining changes still span more than one exercise's worth of work, stop and ask the user how to split them into separate PRs.
- Read `N`, the title, and the domain(s) from that exercise's README `# Task Statement` header (and/or `CLAUDE.md`'s Exercises table) — needed for the branch name, commit message, and PR text below.

## 2. Pre-flight checks

- Confirm the current branch is `master`, and that `git status`/`git diff` show only the exercise's shipment as scoped in step 1 (exercise folder + its supporting files) — no drive-by unrelated changes riding along.
- Run `uv run exercises/<domain-slug>/task-<N>-<slug>/main.py` (and any alternate scenario the exercise's README documents in "How to run") and confirm it actually executes end to end. Do not proceed to branch/commit/PR on the strength of "should work" — this session's own history has caught real bugs this way.

## 3. Branch creation

- Name: `exercise/task-<N>-<kebab-slug>` — copy `<N>-<kebab-slug>` straight from the exercise's own folder name, so the branch and the folder always match.
- `git checkout -b exercise/task-<N>-<kebab-slug>` from the current `master`.
- If commits for this exercise already exist directly on local `master` (this repo's early history was built that way, before this skill existed), stop and ask the user how to proceed instead of silently rewriting `master` — moving existing commits onto a branch requires resetting `master`, which is a destructive operation this skill must never perform unprompted.

## 4. Commit

- Stage everything identified in step 1 as part of this exercise's shipment — the exercise folder plus every other file that belongs with it (`common/`, `CLAUDE.md`, README/skill updates, etc.). Pass explicit paths to `git add` (list them out, or `git add -u` plus the specific untracked paths) — never `git add -A`/`git add .`, which would also pick up any unrelated stray changes sitting in the working tree.

<commit_message_template>
  <subject>&lt;Add|Update|Rename|Remove&gt; Exercise &lt;N&gt;: &lt;Title&gt;</subject>
  <body>&lt;optional paragraph — only if the change needs explaining beyond the subject, e.g. what moved/why a shared file changed&gt;</body>
  <trailer>Co-Authored-By: Claude Sonnet 5 &lt;noreply@anthropic.com&gt;</trailer>
  <rule>Match the verb to what actually happened: `Add` for a brand-new exercise, `Update` for changes to an existing one (README rewrite, scenario swap, bug fix), `Rename` for a folder/number move, `Remove` for deleting one. Check `git log` before picking wording if unsure — this is this repo's established subject style, not a generic convention. Keep the trailer's author name (`Claude Sonnet 5`) matching what `git log` shows; don't substitute a different Co-Authored-By convention.</rule>
</commit_message_template>

## 5. PR title & body format

<pr_template>
  <title>Add Exercise &lt;N&gt;: &lt;Title&gt;</title>
  <body>
## Summary
- &lt;1-3 bullets, drawn from the exercise's own README `# Exercise` section — the scenario and what business logic/mechanic it demonstrates, not a restatement of the task statement text&gt;

## Test plan
- [x] `uv run exercises/&lt;domain-slug&gt;/task-&lt;N&gt;-&lt;slug&gt;/main.py` — &lt;what this confirmed, e.g. "default/broad scenario"&gt;
- [x] `uv run exercises/&lt;domain-slug&gt;/task-&lt;N&gt;-&lt;slug&gt;/main.py "&lt;alt scenario&gt;"` — &lt;what this confirmed, e.g. "narrow scenario, verified it skips the optional fork"&gt;
  </body>
  <rule>Every "Test plan" line must correspond to a command actually run this session (step 2), not a hypothetical — if you haven't run it, run it before writing the PR body rather than just checking the box.</rule>
</pr_template>

## 6. Push and create the PR

- `git push -u origin exercise/task-<N>-<kebab-slug>`
- `gh pr create --title "<title>" --body "$(cat <<'EOF' ... EOF)" --base master`
- Report the PR URL to the user. This is as far as the skill goes without an explicit go-ahead: opening a PR is visible but still reversible (it can be closed); merging is not, so treat merge as a separate checkpoint below.

## 7. PR merge — separate confirmation checkpoint

- Do not run the merge command until the user has explicitly said to merge in this conversation (e.g. "merge it", "looks good, ship it") — even if they invoked this skill expecting the whole pipeline in one go, still surface the PR and wait, since merging into `master` is materially harder to undo than opening a PR.
- Default merge strategy: squash, keeping one commit per exercise in `master`'s history, and delete the branch on merge:
  ```
  gh pr merge <PR> --squash --delete-branch
  ```
- If the user wants a merge commit instead of squash, use `--merge` in place of `--squash`.

## 8. Sync local master back up

- `git checkout master`
- `git pull origin master` — a plain pull, not `--rebase`, since `master` should only ever fast-forward here (the merge that just landed is the only new commit).
- `git branch -d exercise/task-<N>-<kebab-slug>` to remove the now-merged local branch.

## 9. Report

Confirm to the user: the PR URL, which merge strategy was used, and that local `master` is up to date and the feature branch is gone both locally and (via `--delete-branch`) on the remote.
