# Task Statement 4.6: Design multi-instance and multi-pass review architectures
## Knowledge of
- Self-review limitations: a model retains reasoning context from generation, making it less likely to question its own decisions in the same session
- Independent review instances (without prior reasoning context) are more effective at catching subtle issues than self-review instructions or extended thinking
- Multi-pass review: splitting large reviews into per-file local analysis passes plus cross-file integration passes to avoid attention dilution and contradictory findings
## Skills in
- Using a second independent Claude instance to review generated code without the generator's reasoning context
- Splitting large multi-file reviews into focused per-file passes for local issues plus separate integration passes for cross-file data flow analysis
- Running verification passes where the model self-reports confidence alongside each finding to enable calibrated review routing

---

# Subject
A three-file notification dispatch system (`dispatcher.py`, `email_channel.py`, `sms_channel.py`) already exists, as if a Claude instance had just generated it.

It has two planted problems:
- An unbounded retry loop in the email channel that looks intentional if you're anchored to the stated design goal, and looks obviously wrong if you're not.
- A rate-limiting gap that only exists across files — no single file looks broken on its own.

The prompts compare a same-session self-review against an independent fresh-session review, then split that independent review into a per-file pass and a cross-file integration pass.

---

# How to verify
This task has no script to run. Open a **Claude Code** session at the repository root (the prompts below ask it to read files by path, so it needs file access — this won't work pasted into claude.ai's chat, which can't resolve a local path).

Session A is two chat turns on its own. Session B's three turns belong together in a **second, separate** session with no shared history from Session A — start a brand-new Claude Code session (or `/clear` the first one) before running Session B.

### 1. Same-session self-review, justify-then-review (Session A)
First message:
```
Read tasks/prompt-engineering/task-6-multi-instance-multi-pass-review/dispatcher.py, tasks/prompt-engineering/task-6-multi-instance-multi-pass-review/email_channel.py, and tasks/prompt-engineering/task-6-multi-instance-multi-pass-review/sms_channel.py.

You designed and wrote all three of these files. In 2-3 sentences, explain why send_email retries in a while True loop until the provider accepts the message, rather than giving up after a fixed number of attempts.
```
Second message, same session, right after the first response:
```
Now review your own code for correctness issues, including send_email. List anything you'd fix before shipping.
```
The first message doesn't just assert a design intent — it makes the model generate and commit to its own justification for the retry loop. The second message then asks it to review that same code. Expect the self-review to under-flag or explicitly defend the `while True` loop (e.g. calling the missing backoff/cap "a nice-to-have" or "acceptable given the intentional design"), because it's now reviewing a decision it just finished arguing for, not a neutral code sample.

### 2. Independent fresh-session review, with self-reported confidence (Session B, turn 1)
Start a new session before running this.
```
Read tasks/prompt-engineering/task-6-multi-instance-multi-pass-review/dispatcher.py, tasks/prompt-engineering/task-6-multi-instance-multi-pass-review/email_channel.py, and tasks/prompt-engineering/task-6-multi-instance-multi-pass-review/sms_channel.py.

You're reviewing this notification dispatch system for the first time, with no other context on why it was written this way. List every correctness issue you find. For each one, self-report a confidence level (high / medium / low) reflecting how sure you are it's a real bug rather than a false positive.
```
Without Session A's justify-then-review framing, expect this instance to flag the unbounded retry loop in `send_email` as a high-confidence issue — no backoff, no attempt cap, can hot-loop against a persistently-failing provider — the same defect Session A likely soft-pedaled or defended.

### 3. Per-file pass (Session B, turn 2 — same session as turn 2 above)
```
Now review dispatcher.py, email_channel.py, and sms_channel.py one at a time, in isolation. For each file, list only the issues visible from that file alone, without referring to either of the other two.
```
Each file should look locally reasonable on this pass. `sms_channel.py` alone has nothing wrong with it — it just doesn't define a rate limit constant, which isn't visibly a bug without the other files. `dispatcher.py` alone has a defensible-looking fallback (`return True` when no rate limit is configured). No file in isolation surfaces the real problem.

### 4. Integration pass (Session B, turn 3 — same session)
```
Now review all three files together, focused specifically on data that flows between them: shared constants, and assumptions one file makes about what another file provides. Trace that flow end to end — what breaks or behaves unexpectedly?
```
Expect this pass to catch what step 3 couldn't: `dispatcher.py` throttles a channel using `getattr(channel_module, "RATE_LIMIT_PER_MINUTE", None)`, and only `email_channel.py` actually defines that constant. `sms_channel.py` never does, so `_within_rate_limit` silently returns `True` for every SMS send — SMS is never rate-limited at all, even though the presence of the constant in `email_channel.py` makes clear every channel was supposed to be.

### Checklist
- Self-review-blind bug: `email_channel.py`'s `send_email` retries in a bare `while True` loop — no backoff, no maximum attempt count, can hot-loop indefinitely against a provider that's persistently failing (e.g. an invalid recipient that will never succeed).
- Cross-file bug: `dispatcher.py`'s `_within_rate_limit` falls back to "unlimited" whenever `RATE_LIMIT_PER_MINUTE` is missing from a channel module. `email_channel.py` defines it (`30`); `sms_channel.py` never does — so SMS sends bypass rate limiting entirely, invisible unless you read both files together.
- Session A (justify-then-review, same session) should under-flag or explicitly defend the retry-loop bug after committing to its own justification for it; Session B turn 1 (independent, fresh session, no justification step) should flag it with high confidence.
- Turn 3 (per-file) should miss the rate-limit gap; turn 4 (integration) should catch it.

---

# Implementation Info
> The sample files are a small, already-"generated" multi-file feature with a self-review-blind bug and a cross-file bug planted in it. The README's four prompts contrast same-session self-review against an independent instance, and a per-file pass against a cross-file integration pass.
## How each Task Info item is covered:
- Self-review limitations: reasoning context from generation biases the same session — `README.md`

  ```
  You designed and wrote all three of these files. In 2-3 sentences, explain why send_email retries in a while True loop until the provider accepts the message, rather than giving up after a fixed number of attempts.

  Now review your own code for correctness issues, including send_email.
  ```
  Session A's first message makes the model generate and commit to its own justification for the retry design; the second message then asks it to review that same code in the same session. The review has to contradict reasoning it produced one turn earlier, reproducing the anchoring effect a real generate-then-review session would have.

- Independent review instances catch what self-review misses — `README.md`

  ```
  You're reviewing this notification dispatch system for the first time, with no other context on why it was written this way.
  ```
  Session B runs in a brand-new session with none of Session A's justify-then-review framing. The contrast between what Session A under-flags/defends and what Session B flags with high confidence is the evidence: same code, same bug, different outcome purely from removing the generator's own committed reasoning.

- Multi-pass review: per-file local passes plus a cross-file integration pass — `README.md`

  ```
  For each file, list only the issues visible from that file alone, without referring to either of the other two.
  ...
  Now review all three files together, focused specifically on data that flows between them
  ```
  Turn 3 constrains the review to one file at a time; turn 4 explicitly asks for cross-file data-flow analysis. The rate-limit gap is designed to be invisible in turn 3's scope and only findable in turn 4's.

- Using a second independent instance without the generator's context — `README.md`

  ```
  Turns 2-4 belong together in a **second, separate** session with no shared history from Session A — start a brand-new Claude Code session (or `/clear` the first one) before running turn 2.
  ```
  The instruction is explicit that Session B must not inherit Session A's conversation, since the whole point is testing review quality without the generator's own committed reasoning.

- Splitting large multi-file reviews into per-file and integration passes — `dispatcher.py`, `sms_channel.py`

  ```
  limit_per_minute = getattr(channel_module, "RATE_LIMIT_PER_MINUTE", None)
  if limit_per_minute is None:
      # No rate limit configured for this channel - nothing to enforce.
      return True
  ```
  `dispatcher.py`'s fallback reads as reasonable in isolation (turn 3's scope). It's only a bug once you know `sms_channel.py` (a separate file) never defines `RATE_LIMIT_PER_MINUTE` — the exact kind of cross-file data-flow issue a per-file pass structurally cannot catch, and an integration pass is designed to.

- Self-reported confidence for calibrated review routing — `README.md`

  ```
  For each one, self-report a confidence level (high / medium / low) reflecting how sure you are it's a real bug rather than a false positive.
  ```
  Session B's first prompt asks for a confidence label alongside every finding, the mechanism that would let a downstream process auto-route high-confidence findings and send low-confidence ones to a human instead of treating every finding as equally actionable.
