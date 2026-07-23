# Android App Conventions

Directory-level config for `android/`. Adds to the project-level `CLAUDE.md` above it — it does not replace it.

- Kotlin only, linted with `ktlint` before commit.
- Represent screen state as a sealed class (`sealed class SettingsState`), never a bare boolean/enum grab-bag.
- Activities are named `<Screen>Activity` and live under `app/src/main/java/com/example/app/`.

This file does not repeat the localization key conventions — those apply to every `strings.xml` file across `ios/`, `android/`, and `shared/` alike, so they live in `.claude/rules/localization-conventions.md` instead of being pasted here and in `ios/CLAUDE.md` and `shared/CLAUDE.md`.
