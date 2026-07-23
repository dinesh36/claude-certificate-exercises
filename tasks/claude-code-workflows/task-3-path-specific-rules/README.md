# Task Statement 3.3: Apply path-specific rules for conditional convention loading
## Knowledge of
- .claude/rules/ files with YAML frontmatter paths fields containing glob patterns for conditional rule activation
- How path-scoped rules load only when editing matching files, reducing irrelevant context and token usage
- The advantage of glob-pattern rules over directory-level CLAUDE.md files for conventions that span multiple directories (e.g., test files spread throughout a codebase)
## Skills in
- Creating .claude/rules/ files with YAML frontmatter path scoping (e.g., paths: ["terraform/**/*"]) so rules load only when editing matching files
- Using glob patterns in path-specific rules to apply conventions to files by type regardless of directory location (e.g., **/*.test.tsx for all test files)
- Choosing path-specific rules over subdirectory CLAUDE.md files when conventions must apply to files spread across the codebase

---

# Subject
A cross-platform mobile monorepo sample project with three trees: `ios/` (a Swift app), `android/` (a Kotlin app), and `shared/` (the source-of-truth localization strings both platforms compile from). It demonstrates a path-specific rule that applies one translation-key convention to every localization file in the repo, regardless of which platform tree it lives in.
- Each platform tree has its own directory-level `CLAUDE.md` with genuinely platform-specific conventions (Swift style, Kotlin style, shared-module rules).
- `.claude/rules/localization-conventions.md` is scoped by a `paths:` glob (`**/*.strings`, `**/strings.xml`) instead of living in any one directory-level file, so it applies everywhere a localization file exists and nowhere else.

---

# How to verify
This task has no script to run — it's a set of Claude Code configuration files. Open a Claude Code session with this folder (`tasks/claude-code-workflows/task-3-path-specific-rules/`) as the working directory, then try:

```
Review ios/Sources/Onboarding/Localizable.strings against our conventions.
```
Expected: it flags `"SkipButton"` as a violation — it's a bare, un-namespaced, non-underscore key, when the convention requires `<feature>_<screen>_<element>` like `onboarding_welcome_title`. This proves `.claude/rules/localization-conventions.md` loaded for a `.strings` file under `ios/`.

```
Review android/app/src/main/res/values/strings.xml against our conventions.
```
Expected: it flags `"darkModeLabel"` the same way — bare and camelCase instead of underscore-namespaced — even though this file lives in a completely different directory tree (`android/`, not `ios/`). This is the concrete proof that the rule is scoped by file pattern, not by directory: the same convention caught the same class of mistake in two unrelated trees.

```
Review ios/Sources/Onboarding/OnboardingViewController.swift against our conventions.
```
Expected: no localization-key findings at all — at most a note about the file being fine, or iOS style feedback drawn from `ios/CLAUDE.md`. This file doesn't match the `paths:` glob, so `.claude/rules/localization-conventions.md` never loads for it, even though it sits in the same folder as `Localizable.strings`.

```
Why is the localization convention in .claude/rules/ instead of just being added to ios/CLAUDE.md, android/CLAUDE.md, and shared/CLAUDE.md?
```
Expected: it should explain that the convention needs to apply identically across all three trees, and a directory-level file would mean maintaining three copies that could drift out of sync — plus each directory-level `CLAUDE.md` would apply to every file in that directory, including ones that have nothing to do with localization. A single glob-scoped rule file avoids both problems.

---

# Implementation Info
> A cross-platform mobile monorepo with `.claude/rules/localization-conventions.md` (the path-scoped rule) and three directory-level `CLAUDE.md` files (`ios/CLAUDE.md`, `android/CLAUDE.md`, `shared/CLAUDE.md`) — plus illustrative Swift, Kotlin, and `.strings`/`.xml` stub files so the rule has real content to check.
## How each Task Info item is covered:
- **.claude/rules/ files with YAML frontmatter paths fields containing glob patterns for conditional rule activation** — `.claude/rules/localization-conventions.md`

  ```yaml
  ---
  paths:
    - "**/*.strings"
    - "**/strings.xml"
  ---
  ```

  The frontmatter's `paths:` list is the actual glob-pattern activation mechanism — this file only loads for a session editing a file matching one of these two patterns.

- **How path-scoped rules load only when editing matching files, reducing irrelevant context and token usage** — `.claude/rules/localization-conventions.md`

  ```markdown
  This file only loads while editing a file matching one of the `paths` globs
  above. Editing `ios/Sources/Onboarding/OnboardingViewController.swift` or
  `android/app/src/main/java/com/example/app/SettingsActivity.kt` does not
  pull this file in — those aren't localization files, even though they live
  in the same directories as ones that are.
  ```

  The rule file states its own scoping behavior directly, and the "How to verify" section's third prompt is the checkable version of this: reviewing the `.swift` file produces no localization-convention findings, because the rule never loaded for it.

- **The advantage of glob-pattern rules over directory-level CLAUDE.md files for conventions that span multiple directories (e.g., test files spread throughout a codebase)** — `CLAUDE.md` ("Why a path-specific rule instead of three CLAUDE.md files")

  ```markdown
  Pasting the same convention into all three directory-level `CLAUDE.md`
  files would work, but it means three copies to keep in sync, and it would
  still apply even while editing files in those directories that have
  nothing to do with localization.
  ```

  This states the tradeoff directly: three directory-level files mean duplication and over-broad application; one glob-scoped rule file avoids both.

- **Creating .claude/rules/ files with YAML frontmatter path scoping (e.g., `paths: ["terraform/**/*"]`) so rules load only when editing matching files** — `.claude/rules/localization-conventions.md`

  ```yaml
  paths:
    - "**/*.strings"
    - "**/strings.xml"
  ```

  Same file as above, from the "creating it" side rather than the "why" side — this is a real, working `paths:` scoped rule file in this repo, not a description of one.

- **Using glob patterns in path-specific rules to apply conventions to files by type regardless of directory location (e.g., `**/*.test.tsx` for all test files)** — `.claude/rules/localization-conventions.md`, `ios/Sources/Onboarding/Localizable.strings`, `android/app/src/main/res/values/strings.xml`

  ```markdown
  Applies to every localization file in this monorepo — `ios/**/*.strings`,
  `android/**/res/values*/strings.xml`, and `shared/**/*.strings` alike —
  regardless of which platform tree it lives in or how deeply it's nested.
  ```

  The `**/*.strings` and `**/strings.xml` globs match by file type, not by directory — proven by the "How to verify" section's first two prompts catching the same kind of violation in both `ios/` and `android/`.

- **Choosing path-specific rules over subdirectory CLAUDE.md files when conventions must apply to files spread across the codebase** — `README.md` ("How to verify" section, the "why is it in .claude/rules/" prompt)

  ```
  Why is the localization convention in .claude/rules/ instead of just being
  added to ios/CLAUDE.md, android/CLAUDE.md, and shared/CLAUDE.md?
  ```

  The prompt and its expected answer are themselves the demonstrated skill: given a convention that spans three directory trees, the correct choice is a path-specific rule, not three duplicated directory-level files.
