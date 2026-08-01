# Task Statement 5.5: Design human review workflows and confidence calibration

## Knowledge of
- The risk that aggregate accuracy metrics (e.g., 97% overall) may mask poor performance on specific document types or fields
- Stratified random sampling for measuring error rates in high-confidence extractions and detecting novel error patterns
- Field-level confidence scores calibrated using labeled validation sets for routing review attention
- The importance of validating accuracy by document type and field segment before automating high-confidence extractions

## Skills in
- Implementing stratified random sampling of high-confidence extractions for ongoing error rate measurement and novel pattern detection
- Analyzing accuracy by document type and field to verify consistent performance across all segments before reducing human review
- Having models output field-level confidence scores, then calibrating review thresholds using labeled validation sets
- Routing extractions with low model confidence or ambiguous/contradictory source documents to human review, prioritizing limited reviewer capacity

---

# Subject

An HR platform, BrightPath Talent, runs job applications through a screening pipeline that pulls out five candidate fields (name, years of experience, highest degree, certifications, most recent title) across three application formats: chronological resumes, functional resumes, and video-interview transcripts.

- This task is scripted: the Skills-in bullets need real computation over a labeled dataset (stratified sampling, accuracy-by-segment breakdown, threshold calibration), which a single documented chat session can't show cleanly.

---

# How to run

See the repository root [README](../../../README.md) for one-time setup (uv project; this task also needs the `claude` CLI on `PATH`, since it shells out for one live confidence-scoring call).

```bash
uv run tasks/context-management/task-5-stratified-confidence-calibration/calibrate.py
```

The run prints five sections in order: aggregate accuracy vs. accuracy broken down by document type and field (the hidden `video_transcript`/`years_experience` problem the aggregate number hides), a stratified sample of high-confidence extractions for ongoing QA, calibrated per-segment auto-approve thresholds, one live model-generated confidence score, and today's queue routed into auto-approved / sent-to-review / deferred buckets under limited reviewer capacity.

---

# Implementation Info

> `data.py` builds a 210-record labeled validation set (`VALIDATION_SET`) from fixed per-segment accuracy targets, plus a 12-item live queue (`TODAYS_QUEUE`) waiting to be routed. `calibrate.py` reads both and does the actual analysis.

## How each Task Info item is covered:

- Aggregate accuracy masking a segment-specific problem — `calibrate.py`, `data.py`

  ```python
  def aggregate_accuracy(records):
      return sum(1 for r in records if r["is_correct"]) / len(records)

  def accuracy_by_segment(records):
      buckets = defaultdict(list)
      for r in records:
          buckets[(r["document_type"], r["field"])].append(r["is_correct"])
      return {seg: sum(vals) / len(vals) for seg, vals in buckets.items()}
  ```

  A real run prints `93.3%` in aggregate across 210 extractions, then the segment breakdown shows `video_transcript / years_experience` at `60.0%` — over 33 points below the number a reviewer would see if they only checked the aggregate. Candidates describe their work history in loose, approximate spoken terms during video interviews, and auto-caption text carries its own transcription noise, which chronological and functional resumes (structured, written documents) mostly avoid.

- Stratified random sampling of high-confidence extractions — `calibrate.py`

  ```python
  def stratified_sample_high_confidence(records, per_stratum=3, seed=7):
      rng = random.Random(seed)
      high_conf = [r for r in records if r["model_confidence"] >= HIGH_CONFIDENCE_THRESHOLD]
      by_type = defaultdict(list)
      for r in high_conf:
          by_type[r["document_type"]].append(r)
      sample = []
      for doc_type, items in by_type.items():
          sample.extend(rng.sample(items, min(per_stratum, len(items))))
      return sample
  ```

  This draws a fixed number of records from *every* document type's high-confidence pool, so the QA sample always covers `chronological_resume`, `functional_resume`, and `video_transcript` instead of being dominated by whichever type has the most volume (a plain random sample over all 210 records would skew heavily toward `chronological_resume`, which has the most applications).

- Field-level confidence scores calibrated against a labeled validation set — `calibrate.py`

  ```python
  def calibrate_thresholds(records, target_precision=TARGET_PRECISION, min_subset_size=5):
      ...
      for candidate in candidates:
          subset = [r for r in items if r["model_confidence"] >= candidate]
          if len(subset) < min_subset_size:
              continue
          precision = sum(r["is_correct"] for r in subset) / len(subset)
          if precision >= target_precision:
              chosen = candidate
              break
      thresholds[seg] = chosen if chosen is not None else "always_review"
  ```

  A real run against the labeled set calibrates a per-segment auto-approve threshold (e.g. `chronological_resume/candidate_name -> 0.9`) — except `video_transcript/years_experience`, which correctly comes back `always_review`, since no confidence cutoff on that segment's data reaches 98% precision.

  This threshold search almost shipped a bug: without a `min_subset_size` guard, a segment can calibrate to a threshold supported by only one lucky validation record — a single correct extraction sitting at the top confidence value clears a 98% precision bar by pure chance, a 1-record "threshold" that isn't a real signal. Requiring at least 5 supporting records before accepting a threshold fixed it, and is itself a real instance of validating a calibration decision against a large-enough segment before trusting it — the same principle the Knowledge-of bullets describe for accuracy measurement.

  The live model call demonstrates the other half of this bullet — a model actually producing a field-level confidence score, not just a mock number:

  ```python
  def get_model_confidence_extraction(document_text, field):
      prompt = (
          f"Extract the '{field}' value from this interview transcript excerpt and report your "
          f"confidence (0.0-1.0) that the extraction is correct. Respond with ONLY a JSON object "
          f'of the shape {{"field": "...", "value": "...", "confidence": 0.0}} and nothing else.\n\n'
          f"Transcript excerpt:\n{document_text}"
      )
      try:
          result = subprocess.run(
              ["claude", "-p", prompt, "--output-format", "json"],
              capture_output=True, text=True, timeout=90, check=True,
          )
      except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
          return {"errorCategory": "transient", "isRetryable": True, "description": f"claude -p invocation failed: {exc}"}
  ```

  Against `SAMPLE_TRANSCRIPT_EXCERPT` — a candidate hedging between "eight years," "closer to nine," and "somewhere in the seven to nine year range" — a real run returned `{"field": "years_experience", "value": "7-9", "confidence": 0.3}`. That's a genuine headless Claude Code call, not a canned value, and it's well-calibrated behavior in its own right: the model reported low confidence precisely because the transcript itself was ambiguous, rather than picking one number and sounding sure about it. A `json.JSONDecodeError`/`KeyError`/`TypeError` from a malformed or non-JSON response returns a structured `{"errorCategory": "validation", ...}` error instead of silently defaulting to a made-up confidence score, per this repo's tool-error convention.

- Routing low-confidence or ambiguous extractions to review, prioritizing limited reviewer capacity — `calibrate.py`, `data.py`

  ```python
  def route_todays_queue(queue, thresholds, capacity=REVIEWER_CAPACITY):
      needs_review = []
      auto_approved = []
      for item in queue:
          seg = (item["document_type"], item["field"])
          threshold = thresholds.get(seg, "always_review")
          reasons = []
          if threshold == "always_review":
              reasons.append(f"segment {seg} never reaches {TARGET_PRECISION:.0%} precision on the validation set")
          elif item["model_confidence"] < threshold:
              reasons.append(f"confidence {item['model_confidence']} below calibrated threshold {threshold}")
          if item.get("ambiguous_source"):
              reasons.append("source document flagged ambiguous/contradictory")
          if reasons:
              needs_review.append({**item, "reasons": reasons})
          else:
              auto_approved.append(item)

      needs_review.sort(key=lambda r: r["model_confidence"])
      reviewed_now = needs_review[:capacity]
      deferred = needs_review[capacity:]
      return auto_approved, reviewed_now, deferred
  ```

  A real run against the 12-item queue and `REVIEWER_CAPACITY = 5` auto-approves 5 items, routes 5 more to review right now (lowest confidence first), and defers the remaining 2 — including `APP-Q004`, a `video_transcript/years_experience` extraction at 0.95 confidence that still gets routed to review, since that segment is calibrated `always_review` regardless of how confident the model sounds.
