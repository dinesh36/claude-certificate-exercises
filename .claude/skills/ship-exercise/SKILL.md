---
name: ship-exercise
description: Take a built exercise (or any exercise-folder change) through the full git/PR lifecycle — branch, commit, PR, merge, and sync master back up. Use when the user asks to open a PR, ship, land, or merge an exercise.
allowed-tools: Bash, Read, Grep
---

# Ship Exercise

Runs the git/GitHub side of landing one exercise's work end to end: branch → commit → PR → merge → resync `master`, with no pause for merge confirmation — the user has authorized this skill to run the full pipeline unattended once invoked. This is the workflow that follows building or updating an exercise (e.g. with the `new-exercise` skill) — it does not touch exercise content itself.

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
- Report the PR URL to the user, then continue straight to step 7 — merging is not a separate confirmation checkpoint in this skill; the user has authorized the full branch → commit → PR → merge → resync pipeline to run end to end without pausing.

## 7. PR merge — runs automatically, no confirmation pause

- Proceed directly to merging once the PR is open — do not wait for the user to say "merge it" first. The gate that actually protects `master` is step 2's pre-flight check (exercise verified to run) and step 1's scoping (only this exercise's own files); once those passed, merging is just the mechanical next step, not a separate decision point.
- Default merge strategy: squash, keeping one commit per exercise in `master`'s history, and delete the branch on merge:
  ```
  gh pr merge <PR> --squash --delete-branch
  ```
- If the user wants a merge commit instead of squash, use `--merge` in place of `--squash`.
- `--delete-branch` removes both the remote branch and (if you're on it) your local branch, and typically leaves you checked out on `master` already — confirm with `git branch --show-current` rather than assuming you need to switch.

## 8. Pull master again after merging

- `git fetch origin --prune` (the `--prune` clears any now-deleted branch refs, like the one `--delete-branch` just removed remotely).
- Try the clean path first: `git checkout master` then `git pull origin master`. If this fast-forwards, you're done — this is what happens every time once a PR is the *only* way changes reach `master`.
- If the pull refuses to fast-forward, local `master` has commits that were never part of this PR's branch (e.g. leftover direct-to-`master` commits from before this workflow was adopted — see step 3's guard). Do not merge or rebase past this blindly:
  1. Run `git log origin/master..master` and confirm every commit it lists is one whose content is already fully captured in the branch/PR you just merged (check by diffing or recalling what you committed in step 4) — not unrelated, un-shipped work.
  2. Only once confirmed, and only with `git status` clean, run `git reset --hard origin/master` to drop those superseded local-only commits and land exactly on the squash commit that's now on `origin/master`.
  3. If any commit in that list is NOT already reflected in the merged PR, stop and ask the user — do not discard work that only exists locally.
- Verify at the end with `git log --oneline -1` that local `master` now matches `origin/master`'s tip exactly.

## 9. Report

Confirm to the user: the PR URL, which merge strategy was used, whether the local/remote feature branch needed manual cleanup or `--delete-branch` handled it, and that local `master` now matches `origin/master`'s tip exactly (name the commit hash).
