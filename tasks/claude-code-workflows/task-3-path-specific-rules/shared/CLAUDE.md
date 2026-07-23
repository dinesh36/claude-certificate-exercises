# Shared Module Conventions

Directory-level config for `shared/`. Adds to the project-level `CLAUDE.md` above it — it does not replace it.

- `shared/` holds the source-of-truth content both platforms compile from — it has no UI code and no platform-specific build files.
- Every localization key added here must be in English first; platform-specific translations are added to `ios/` and `android/` afterward, never the other way around.
- Files here are plain data (`.strings`, later `.json` exports) — no Swift, Kotlin, or build scripts belong in this tree.

This file does not repeat the localization key conventions — those apply to every `.strings` file across `ios/`, `android/`, and `shared/` alike, so they live in `.claude/rules/localization-conventions.md` instead of being pasted here and in `ios/CLAUDE.md` and `android/CLAUDE.md`.
