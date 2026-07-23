---
paths:
  - "**/*.strings"
  - "**/strings.xml"
---

# Localization Key Conventions

Applies to every localization file in this monorepo — `ios/**/*.strings`, `android/**/res/values*/strings.xml`, and `shared/**/*.strings` alike — regardless of which platform tree it lives in or how deeply it's nested.

- Every key is namespaced by feature and screen, underscore-separated: `<feature>_<screen>_<element>` (e.g. `onboarding_welcome_title`). No bare, un-namespaced keys like `SkipButton`. Underscore-separated keeps every key a valid Android resource identifier as well as a valid iOS `.strings` key, so the same name works unchanged on both platforms.
- Keys are lowercase only. No spaces, no camelCase — underscores are the only separator.
- Every new key needs an English value in `shared/localization/base.strings` before it's added to any platform-specific file.
- Never hardcode a user-facing string directly in Swift or Kotlin source — always go through a localization key.

This file only loads while editing a file matching one of the `paths` globs above. Editing `ios/Sources/Onboarding/OnboardingViewController.swift` or `android/app/src/main/java/com/example/app/SettingsActivity.kt` does not pull this file in — those aren't localization files, even though they live in the same directories as ones that are.
