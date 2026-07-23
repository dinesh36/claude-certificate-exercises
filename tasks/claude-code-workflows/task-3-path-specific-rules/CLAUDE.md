# CLAUDE.md

This is the **cross-platform mobile monorepo** — a small sample project (Task Statement 3.3) demonstrating path-specific rules for conditional convention loading. It has three trees: `ios/` (a Swift app), `android/` (a Kotlin app), and `shared/` (the source-of-truth localization strings both platforms compile from).

This file is this sample project's own **project-level** config. It is nested inside the larger certification repo, so a live Claude Code session opened anywhere under here also inherits the outer repo's own root `CLAUDE.md` above this one.

## Why a path-specific rule instead of three CLAUDE.md files

Each of `ios/`, `android/`, and `shared/` has its own directory-level `CLAUDE.md` with genuinely platform-specific conventions (Swift style, Kotlin style, and shared-module conventions, respectively).

The translation-key naming convention is different: it must apply to every localization file in all three trees, regardless of how deep that file sits (`ios/Sources/Onboarding/Localizable.strings`, `android/app/src/main/res/values/strings.xml`, `shared/localization/base.strings`). Pasting the same convention into all three directory-level `CLAUDE.md` files would work, but it means three copies to keep in sync, and it would still apply even while editing files in those directories that have nothing to do with localization (a `.swift` view controller, a `.kt` activity).

`.claude/rules/localization-conventions.md` solves both problems: its `paths:` glob matches localization files by name pattern, not by directory, so it loads once, applies everywhere those files live, and stays out of context entirely while editing unrelated files in the same directories.
