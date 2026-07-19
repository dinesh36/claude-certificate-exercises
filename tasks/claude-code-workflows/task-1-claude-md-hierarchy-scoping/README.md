# Task Statement 3.1: Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organization
## Knowledge of
- The CLAUDE.md configuration hierarchy: user-level (~/.claude/CLAUDE.md), project-level (.claude/CLAUDE.md or root CLAUDE.md), and directory-level (subdirectory CLAUDE.md files)
- That user-level settings apply only to that user—instructions in ~/.claude/CLAUDE.md are not shared with teammates via version control
- The @import syntax for referencing external files to keep CLAUDE.md modular (e.g., importing specific standards files relevant to each package)
- .claude/rules/ directory for organizing topic-specific rule files as an alternative to a monolithic CLAUDE.md
## Skills in
- Diagnosing configuration hierarchy issues (e.g., a new team member not receiving instructions because they're in user-level rather than project-level configuration)
- Using @import to selectively include relevant standards files in each package's CLAUDE.md based on maintainer domain knowledge
- Splitting large CLAUDE.md files into focused topic-specific files in .claude/rules/ (e.g., testing.md, api-conventions.md, deployment.md)
- Using the /memory command to verify which memory files are loaded and diagnose inconsistent behavior across sessions

---

# Subject
A fintech billing monorepo sample project with two packages: `billing_api` (a payment-intake REST service) and `ledger_worker` (an async ledger-posting worker). It demonstrates CLAUDE.md's configuration hierarchy, `@import` modularity, and `.claude/rules/` as an alternative to one monolithic file.
- This folder's own root `CLAUDE.md` is the sample's project-level config; each package's `CLAUDE.md` is a directory-level file that adds package-specific conventions on top of it, never replacing it.
- Shared conventions live in `.claude/rules/*.md` and are pulled into whichever package's `CLAUDE.md` actually needs them via `@import`, instead of being duplicated inline or crammed into one giant file.
- The "How to verify" section below also walks through diagnosing a hierarchy misconfiguration — conventions mistakenly placed in a personal `~/.claude/CLAUDE.md` instead of the tracked project config — using the `/memory` command.

---

# How to verify
This task has no script to run — it's a set of Claude Code configuration files. Open a Claude Code session with this folder (`tasks/claude-code-workflows/task-1-claude-md-hierarchy-scoping/`) as the working directory, then try:

```
What testing conventions apply to files under packages/billing_api?
```
Expected: it cites the `.claude/rules/testing.md` conventions (pytest, mock external I/O, 85% coverage), even though `packages/billing_api/CLAUDE.md` never mentions testing itself. This proves the project-level file's rules are inherited by every directory beneath it, not just the ones that explicitly repeat them.

```
What conventions apply specifically to packages/billing_api that don't apply to packages/ledger_worker?
```
Expected: it cites `api-conventions.md`'s REST rules (`/v1/` versioning, `Idempotency-Key` header, the `{error_code, message}` error shape). It explicitly says these don't apply to `ledger_worker`, whose own `CLAUDE.md` imports `queue-conventions.md` instead. This proves `@import` is being used to selectively scope conventions per package, rather than sharing one undifferentiated file.

```
/memory
```
Run this with your working directory set to `packages/billing_api`. Expected: the listed memory files include:
- `packages/billing_api/CLAUDE.md`
- This task's own root `CLAUDE.md`
- Further up the tree, the outer certification repo's root `CLAUDE.md`
- **Not** `packages/ledger_worker/CLAUDE.md`

This is the concrete, checkable way to confirm which files are actually in scope for a given directory, instead of assuming from the folder layout.

```
A new engineer on the ledger_worker package says Claude Code isn't applying our queue-conventions rules for them, even though it works fine on my machine and the file is committed at packages/ledger_worker/CLAUDE.md. What's the most likely cause, and how do we fix it?
```
Expected: it should reason that the engineer likely has a conflicting or overriding personal `~/.claude/CLAUDE.md`, or is running from a different working directory than they think. `~/.claude/CLAUDE.md` is user-level and never shared via version control, so "committed at the project level" doesn't guarantee it's the *only* thing loaded for them. The fix is to have them run `/memory` themselves to see exactly what's loaded on their machine, instead of assuming the repo state alone explains their behavior.

---

# Implementation Info
> A fintech billing monorepo split into `CLAUDE.md` (project-level), `packages/billing_api/CLAUDE.md` and `packages/ledger_worker/CLAUDE.md` (directory-level), and `.claude/rules/*.md` (modular topic files pulled in via `@import`) — plus two minimal illustrative Python stubs (`packages/billing_api/app.py`, `packages/ledger_worker/worker.py`) so the conventions have something real to describe.
## How each Task Info item is covered:
- **The CLAUDE.md configuration hierarchy: user-level, project-level, and directory-level** — `CLAUDE.md`, `packages/billing_api/CLAUDE.md`

  ```markdown
  This file is this sample project's own **project-level** config. It is nested
  inside the larger certification repo, so a live Claude Code session opened
  anywhere under here also inherits the outer repo's own root `CLAUDE.md` above
  this one — that's expected: it's a real instance of the same hierarchy
  layering this task is teaching, not something to work around.
  ```

  This folder's `CLAUDE.md` is genuinely project-level for the sample. `packages/billing_api/CLAUDE.md` and `packages/ledger_worker/CLAUDE.md` are genuinely directory-level. As the excerpt says, the certification repo's own root `CLAUDE.md` above this folder is a live, real project-level layer above *this* sample's project level. That's three real layers stacked, not a diagram.

- **That user-level settings apply only to that user — instructions in ~/.claude/CLAUDE.md are not shared via version control** — `README.md` ("How to verify" section)

  ```
  A new engineer on the ledger_worker package says Claude Code isn't applying
  our queue-conventions rules for them, even though it works fine on my
  machine and the file is committed at packages/ledger_worker/CLAUDE.md.
  ```

  This prompt is designed so the only coherent explanation is the user-level/project-level distinction. The committed file is version-controlled and identical for everyone, so a per-engineer difference in behavior points at something outside git — a personal `~/.claude/CLAUDE.md`, or a differing working directory, that never reaches teammates.

- **The @import syntax for referencing external files to keep CLAUDE.md modular** — `packages/billing_api/CLAUDE.md`

  ```markdown
  In addition to the project-level testing conventions inherited from the repo
  root, this package follows:

  @../../.claude/rules/api-conventions.md
  ```

  The package's REST conventions live in their own file, and are pulled in with `@import` — not pasted inline into the package's `CLAUDE.md`.

- **.claude/rules/ directory for organizing topic-specific rule files as an alternative to a monolithic CLAUDE.md** — `.claude/rules/testing.md`, `.claude/rules/api-conventions.md`, `.claude/rules/queue-conventions.md`

  ```markdown
  # REST API Conventions (billing_api)

  - All endpoints are versioned under `/v1/`.
  - Every payment-mutating endpoint requires an `Idempotency-Key` header...
  ```

  Three separate topic files — testing, API, queue — instead of one monolithic `CLAUDE.md` holding every convention for both packages. Each is short, single-purpose, and independently readable.

- **Diagnosing configuration hierarchy issues (e.g., a new team member not receiving instructions because they're in user-level rather than project-level configuration)** — `README.md` ("How to verify" section, same diagnostic prompt as above)

  The prompt and its expected answer are themselves the demonstrated skill. Given a symptom — rules not applying for one teammate despite a committed project file — the correct diagnosis routes through the hierarchy: check for a personal `~/.claude/CLAUDE.md` override, then verify with `/memory`. It doesn't just re-check the already-committed file.

- **Using @import to selectively include relevant standards files in each package's CLAUDE.md based on maintainer domain knowledge** — `packages/billing_api/CLAUDE.md`, `packages/ledger_worker/CLAUDE.md`

  ```markdown
  Do not import `queue-conventions.md` here — that governs `ledger_worker`, a
  different package with different failure semantics (a dropped HTTP request
  is retried by the caller; a dropped queue message needs explicit redelivery
  instead).
  ```

  Each package's `CLAUDE.md` explicitly imports only the rules file relevant to its own domain — REST vs. queue semantics — and explains why it deliberately does *not* import the other package's file. That's selective inclusion, not blanket sharing.

- **Splitting large CLAUDE.md files into focused topic-specific files in .claude/rules/ (e.g., testing.md, api-conventions.md, deployment.md)** — `.claude/rules/testing.md`, `.claude/rules/api-conventions.md`, `.claude/rules/queue-conventions.md`

  ```markdown
  # Testing Conventions

  - Every package ships its tests under `tests/`, mirroring the package's own
    module layout.
  ```

  `testing.md` holds only testing conventions. `api-conventions.md` holds only REST conventions. `queue-conventions.md` holds only queue/worker conventions. Each file stays focused enough to read in isolation, mirroring the task statement's own `testing.md`/`api-conventions.md`/`deployment.md` example split.

- **Using the /memory command to verify which memory files are loaded and diagnose inconsistent behavior across sessions** — `README.md` ("How to verify" section, `/memory` prompt)

  ```
  Run this with your working directory set to packages/billing_api. Expected:
  the listed memory files include packages/billing_api/CLAUDE.md, this task's
  own root CLAUDE.md, and (further up the tree) the outer certification
  repo's root CLAUDE.md — but not packages/ledger_worker/CLAUDE.md.
  ```

  `/memory` is the literal, checkable way to confirm which files are in scope for a given working directory. It's used here two ways: to prove correct scoping (`billing_api`'s session doesn't see `ledger_worker`'s file), and, in the diagnostic prompt above, as the tool a teammate would run to explain their own inconsistent behavior.
