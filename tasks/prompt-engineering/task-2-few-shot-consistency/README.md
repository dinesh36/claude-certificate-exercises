# Task Statement 4.2: Apply few-shot prompting to improve output consistency and quality
## Knowledge of
- Few-shot examples as the most effective technique for achieving consistently formatted, actionable output when detailed instructions alone produce inconsistent results
- The role of few-shot examples in demonstrating ambiguous-case handling (e.g., tool selection for ambiguous requests, branch-level test coverage gaps)
- How few-shot examples enable the model to generalize judgment to novel patterns rather than matching only pre-specified cases
- The effectiveness of few-shot examples for reducing hallucination in extraction tasks (e.g., handling informal measurements, varied document structures)
## Skills in
- Creating 2–4 targeted few-shot examples for ambiguous scenarios that show reasoning for why one action was chosen over plausible alternatives
- Including few-shot examples that demonstrate specific desired output format (location, issue, severity, suggested fix) to achieve consistency
- Providing few-shot examples distinguishing acceptable code patterns from genuine issues to reduce false positives while enabling generalization
- Using few-shot examples to demonstrate correct handling of varied document structures (inline citations vs bibliographies, methodology sections vs embedded details)
- Adding few-shot examples showing correct extraction from documents with varied formats to address empty/null extraction of required fields

---

# Subject
A recipe ingredient extractor pulls structured ingredient data out of two recipes written in different source formats: a recipe card with a bulleted ingredient list, and a handwritten note with ingredients embedded in prose.

- Several ingredients use informal, non-numeric measurements ("a pinch of salt", "to taste", "a handful of parsley") with no reliable numeric equivalent — these should extract as `null`, not an invented number.
- One ingredient uses a standardized casual unit that does have a reliable numeric equivalent ("a stick of butter" = 8 tbsp) — this is the opposite mistake to guard against: refusing to convert something that's actually well-defined.
- One ingredient uses a different standardized casual unit not shown in any worked example ("a pair of bay leaves"), testing whether the model generalizes the underlying rule instead of only recognizing the exact units it's seen.

---

# How to verify
This task has no script to run. Open a **Claude Code** session at the repository root and paste the two prompts below yourself — each one asks Claude Code to read [recipes.md](recipes.md) by its relative path, so it needs file access. This won't work pasted into claude.ai's chat, which can't resolve a local repo path; if you want to test there instead, open the file yourself and paste its contents in place of the "Read ..." instruction. Paste each prompt into a **separate, fresh conversation** so the few-shot prompt isn't influenced by the first prompt's answers.

Model output is non-deterministic, but this contrast reproduced cleanly across sanity-check runs recorded during scaffolding: two separate runs of prompt 1 both invented a specific number for every genuinely vague ingredient — salt, vanilla, oil, and parsley all got a guessed quantity/unit (e.g. "a handful of parsley" became `0.25 cup`), and "cover everything with broth" became a guessed `6 cups` out of a cooking instruction that gives no amount at all. Salt's guess even drifted between the two runs (`0.125 tsp` vs `1 | pinch`). Prompt 2, with the identical instructions plus four worked examples, correctly left every one of those same ingredients `null` in its own sanity-check run. Neither prompt's instructions say whether to leave a quantity blank or estimate one for vague phrasing — that's deliberate. LLMs have a well-documented tendency to invent a plausible-sounding number when a field expects one, even under a "best judgment" instruction — that tendency, not a categorization mistake, is what few-shot is being used to fix here.

### 1. Detailed instructions only (no few-shot)
```
You are a recipe-data extraction assistant. Read tasks/prompt-engineering/task-2-few-shot-consistency/recipes.md
and extract every ingredient mentioned across both recipes.

For each ingredient, determine:
- ingredient: the ingredient's name, normalized (e.g. "all-purpose flour" -> "flour")
- quantity: a number
- unit: the unit of measurement
- as_written: the exact phrase used in the source recipe
- a short reasoning for how you arrived at the quantity and unit

Use your best judgment for quantities that aren't given as an exact number in the source.
```
Look for: sanity-check runs of this exact prompt invented a specific quantity for every one of
"a pinch of salt" (`0.125 tsp` one run, `1 | pinch` the next — the guess itself drifted), "vanilla
extract, to taste" (`1 tsp`), "a little oil" (`1 tbsp`), "a handful of fresh parsley" (`0.25 cup`),
and even "cover everything with broth" (`6 cups`, invented from a cooking instruction with no
amount at all). None of these were left blank. "1 stick of butter" and "a pair of bay leaves" came
out fine on their own (`1 | stick`, `2 | count`) — the gap is specifically the vague-phrase cases,
not the standardized-unit ones. Separately, check the rendering: since no row format is specified,
expect headings/bullets/a table rather than one consistent line per ingredient.

### 2. Few-shot prompt (four targeted examples)
```
You are a recipe-data extraction assistant. Read tasks/prompt-engineering/task-2-few-shot-consistency/recipes.md
and extract every ingredient mentioned across both recipes.

For each ingredient, determine:
- ingredient: the ingredient's name, normalized (e.g. "all-purpose flour" -> "flour")
- quantity: a number
- unit: the unit of measurement
- as_written: the exact phrase used in the source recipe
- a short reasoning for how you arrived at the quantity and unit

Use your best judgment for quantities that aren't given as an exact number in the source.

Here are four worked examples showing exactly how to render and reason through the tricky cases:

Example A (a standardized casual unit — convert confidently, don't leave it blank):
Source: "a dozen eggs"
eggs | 12 | count | a dozen eggs | "dozen" is a standardized casual count (always 12), a reliable conversion rather than a guess

Example B (a genuinely vague quantity — leave it null, don't invent a number):
Source: "a dash of hot sauce"
hot sauce | null | null | a dash of hot sauce | "a dash" has no standard numeric equivalent; inventing a precise volume would be a guess, so quantity and unit stay null while the phrase is preserved

Example C (a vague cook's-discretion phrase — also leave it null):
Source: "black pepper, as needed"
black pepper | null | null | black pepper, as needed | "as needed" describes a discretionary amount with no numeric equivalent, so it stays null instead of a guessed small amount

Example D (a clean, explicit numeric case — reinforcing the exact row format):
Source: "3 tablespoons honey"
honey | 3 | tbsp | 3 tablespoons honey | quantity and unit are stated directly in the source, so they're extracted as given

Now extract every ingredient from the two recipes in the file the same way.
```
Look for: every ingredient comes back as the exact five-field, pipe-delimited row the examples use
(`<ingredient> | <quantity> | <unit> | <as_written> | <reasoning>`), run after run. On content,
"a pinch of salt", "vanilla extract, to taste", and "a handful of fresh parsley" all come out with
`quantity: null` and `unit: null` (following Example B/C's pattern — this is the exact reversal of
what prompt 1 did with the same three ingredients), "1 stick of butter" comes out `1 | stick`
(following Example A's "standardized unit" reasoning, not its exact wording — no example mentions
butter or sticks), and "a pair of bay leaves" — a standardized-count phrasing that appears in none
of the four examples — still comes out `2 | count` with its own reasoning line, showing the model
generalized the underlying rule instead of matching a memorized case.

### Checklist
| Ingredient (as written) | Quantity | Unit | Why |
|---|---|---|---|
| "2 cups all-purpose flour" | `2` | `cup` | Stated explicitly in the source |
| "a pinch of salt" | `null` | `null` | Genuinely vague, no standard numeric equivalent |
| "1 stick of butter, melted" | `1` | `stick` (or `8` \| `tbsp`) | "stick" is a standardized US baking unit — either keeping it as-is or converting to tbsp/cup is a confident, non-invented answer; either is acceptable, following Example A's pattern rather than its exact wording |
| "vanilla extract, to taste" | `null` | `null` | Cook's-discretion phrase, no numeric equivalent |
| "a pound of chicken thighs" | `1` | `lb` | Stated explicitly; the "about" hedge doesn't change the stated unit |
| "a pair of bay leaves" | `2` | `count` | Novel case: "pair" is a standardized casual count (= 2) that appears in none of the four few-shot examples — tests whether the model generalizes "standardized unit → confident number" to an unseen word |
| "a handful of fresh parsley" | `null` | `null` | Genuinely vague, no standard numeric equivalent |

The soup recipe also mentions oil and broth with no quantity given at all — extracting those too (with `quantity`/`unit` null) is fine and expected; this Checklist only lists the seven ingredients this task actually grades.

This isn't a hedge — it's a confirmed result. Two separate sanity-check runs of prompt 1 both
invented a number for salt, vanilla, oil, and parsley (and for broth, which isn't even graded
above), with salt's own guess drifting between the two runs. A separate sanity-check run of
prompt 2 left every one of those same ingredients correctly `null`, while still confidently
resolving butter, bay leaves, and chicken thighs the same way prompt 1 already did. The gap few-shot
closes is specifically the invented-number problem on vague phrasing, not the ingredients either
prompt already handles fine.

---

# Implementation Info
> `recipes.md` is the real sample file, containing both recipes in their original source shape (a bulleted recipe card, a prose handwritten note). `README.md`'s "How to verify" section holds the two prompts a reader runs themselves, each pointing Claude Code at `recipes.md` by path, plus a Checklist of the ground-truth extractions to compare against.
## How each Task Info item is covered:
- **Few-shot as the most effective technique when detailed instructions alone are inconsistent** — `README.md`

  ```
  For each ingredient, determine:
  - ingredient: the ingredient's name, normalized (e.g. "all-purpose flour" -> "flour")
  - quantity: a number
  - unit: the unit of measurement
  - as_written: the exact phrase used in the source recipe
  - a short reasoning for how you arrived at the quantity and unit
  ```

  Prompt 1 states every field a response needs in full detail, but never states whether vague phrasing should extract as `null` or an estimate. Two sanity-check runs of this exact prompt both invented a number for salt, vanilla, oil, and parsley regardless — proof the gap is real, not hypothetical. Prompt 2 keeps this exact content spec unchanged and adds only four worked examples, which correctly left every one of those same ingredients `null` in its own sanity-check run — isolating what few-shot buys over detailed prose alone.

- **Few-shot demonstrating ambiguous-case handling** — `README.md`

  ```
  Example A (a standardized casual unit — convert confidently, don't leave it blank):
  Source: "a dozen eggs"
  eggs | 12 | count | a dozen eggs | "dozen" is a standardized casual count (always 12), a reliable conversion rather than a guess
  ```

  Example A shows the reasoning for confidently converting a standardized casual unit on an ingredient ("eggs"/"dozen") that never appears in the recipe file, so applying the same reasoning to "1 stick of butter" requires generalizing the rule, not copying the example.

- **Few-shot enabling generalization to novel patterns, not just pre-specified cases** — `README.md`

  ```
  | "a pair of bay leaves" | `2` | `count` | Novel case: "pair" is a standardized casual
  count (= 2) that appears in none of the four few-shot examples — tests whether the model
  generalizes "standardized unit → confident number" to an unseen word |
  ```

  None of the four examples use the word "pair" or discuss bay leaves — this ingredient exists specifically to check whether the model applies the demonstrated *judgment style* (standardized casual units convert confidently) to a genuinely unseen unit rather than only handling units it's seen before.

- **Few-shot reducing hallucination in extraction (informal measurements, varied document structures)** — `README.md`

  ```
  - a pinch of salt
  - vanilla extract, to taste
  ```
  ```
  Start with a pound of chicken thighs browned in a big pot with a little oil. Toss in a
  pair of bay leaves and a handful of fresh parsley...
  ```

  The pancake recipe is a bulleted ingredient list; the soup recipe is ingredients embedded in narrative prose — two genuinely different document shapes the same extraction has to run against correctly, the recipe-file analog of citations-vs-bibliographies or methodology-vs-embedded-details. Both also carry informal measurements ("a pinch", "to taste", "a handful") that few-shot Examples B and C teach the model to leave `null` instead of converting into an invented precise value.

- **2–4 targeted few-shot examples showing reasoning for the chosen action** — `README.md`

  ```
  Example A ... Example B ... Example C ... Example D ...
  ```

  Four examples, each targeting a distinct judgment call (standardized-unit conversion, genuinely-vague-quantity null, cook's-discretion-phrase null, clean-numeric reinforcement), each with a one-line reasoning explaining why that output was chosen over a plausible alternative.

- **Few-shot demonstrating the desired output format for consistency** — `README.md`

  ```
  eggs | 12 | count | a dozen eggs | "dozen" is a standardized casual count...
  hot sauce | null | null | a dash of hot sauce | "a dash" has no standard numeric equivalent...
  ```

  Neither prompt's prose instructions state a rendering template — both just list the five fields a response needs. Only prompt 2's four examples actually show the exact five-field, pipe-delimited row, the same way task 4.1's `severity | function | category | description` format pinned down its own schema — here pinned by demonstration instead of by a stated rule.

- **Few-shot distinguishing acceptable patterns from genuine issues to reduce false positives** — `README.md`

  ```
  Example A: "a dozen eggs" -> eggs | 12 | count | ...
  Example B: "a dash of hot sauce" -> hot sauce | null | null | ...
  ```

  Examples A and B sit on opposite sides of the same distinction: a standardized casual unit ("dozen") is an acceptable pattern that deserves a confident conversion, while a genuinely vague one ("dash") is where guessing a number would be the false positive. Showing both, rather than just one, is what lets "1 stick of butter" convert correctly instead of getting lumped in with the vague phrases out of over-caution.

- **Few-shot demonstrating correct handling of varied document structures** — `README.md`

  ```
  ## Classic Pancakes (Recipe Card — Bulleted Ingredient List)
  ## Grandma's Chicken Soup (Handwritten Note — Ingredients Embedded in Prose)
  ```

  The same five-field extraction has to run correctly against a structured bulleted ingredient list and a two-sentence prose narrative with ingredients folded into the cooking steps — two genuinely different document shapes for the same underlying extraction task.
