# iOS App Conventions

Directory-level config for `ios/`. Adds to the project-level `CLAUDE.md` above it — it does not replace it.

- Swift only, formatted with `swiftformat` before commit — 4-space indent, no tabs.
- Prefer `guard let` / `if let` over force-unwrapping (`!`). A force-unwrap in a code review needs a comment justifying why it can't fail.
- View controllers are named `<Screen>ViewController` and live under `Sources/<Feature>/`.

This file does not repeat the localization key conventions — those apply to every `.strings` file across `ios/`, `android/`, and `shared/` alike, so they live in `.claude/rules/localization-conventions.md` instead of being pasted here and in `android/CLAUDE.md` and `shared/CLAUDE.md`.
