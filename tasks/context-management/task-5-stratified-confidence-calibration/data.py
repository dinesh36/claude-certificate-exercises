"""Mock labeled validation set and live queue for BrightPath Talent's resume
screening pipeline (Domain 5, Task Statement 5.5).

`VALIDATION_SET` is generated from per-segment target accuracies with a
seeded RNG, not hand-typed record by record — but the per-segment rates
themselves are the deliberate fixture: every segment sits at 88%+ except
one (`video_transcript` applications' `years_experience` field), which is
real-world plausible (candidates describe their work history in loose,
approximate spoken terms during video interviews, and auto-caption text
carries its own transcription noise) and is what `calibrate.py`'s
accuracy-by-segment breakdown is supposed to surface despite a healthy
aggregate accuracy.
"""

import random

FIELDS = ["candidate_name", "years_experience", "highest_degree", "certifications", "most_recent_title"]

# Ground-truth extraction accuracy per (document_type, field) segment.
# Every segment is high except video_transcript/years_experience, which is
# the hidden problem an aggregate accuracy number would mask.
SEGMENT_ACCURACY = {
    ("chronological_resume", "candidate_name"): 0.98,
    ("chronological_resume", "years_experience"): 0.97,
    ("chronological_resume", "highest_degree"): 0.99,
    ("chronological_resume", "certifications"): 0.96,
    ("chronological_resume", "most_recent_title"): 0.95,
    ("functional_resume", "candidate_name"): 0.97,
    ("functional_resume", "years_experience"): 0.88,
    ("functional_resume", "highest_degree"): 0.95,
    ("functional_resume", "certifications"): 0.93,
    ("functional_resume", "most_recent_title"): 0.92,
    ("video_transcript", "candidate_name"): 0.96,
    ("video_transcript", "years_experience"): 0.58,
    ("video_transcript", "highest_degree"): 0.93,
    ("video_transcript", "certifications"): 0.92,
    ("video_transcript", "most_recent_title"): 0.94,
}

DOCUMENT_COUNTS = {
    "chronological_resume": 20,
    "functional_resume": 12,
    "video_transcript": 10,
}


def _confidence_for(doc_type, field, is_correct, rng):
    """The model is well-calibrated everywhere except video_transcript/years_experience,
    where it stays confident (0.86-0.97) regardless of whether it's actually right —
    candidates state a number even when they're estimating out loud, and the model
    takes the stated number at face value. That miscalibration is what
    `calibrate.py`'s threshold search has to catch."""
    if (doc_type, field) == ("video_transcript", "years_experience"):
        return round(rng.uniform(0.86, 0.97), 2)
    if is_correct:
        return round(rng.uniform(0.90, 0.99), 2)
    return round(rng.uniform(0.55, 0.85), 2)


def _build_validation_set(seed=42):
    """Assign correctness deterministically per segment (round(accuracy * N)
    correct, rest incorrect, order shuffled) rather than an independent coin
    flip per record — with only 10-20 documents per document_type, a coin
    flip's sampling noise would blur out the deliberate per-segment rates
    this fixture depends on."""
    rng = random.Random(seed)
    doc_ids_by_type = {}
    doc_id = 0
    for doc_type, count in DOCUMENT_COUNTS.items():
        ids = []
        for _ in range(count):
            doc_id += 1
            ids.append(f"APP-{doc_id:04d}")
        doc_ids_by_type[doc_type] = ids

    records = []
    for doc_type, ids in doc_ids_by_type.items():
        for field in FIELDS:
            accuracy = SEGMENT_ACCURACY[(doc_type, field)]
            n = len(ids)
            n_correct = round(accuracy * n)
            correctness = [True] * n_correct + [False] * (n - n_correct)
            rng.shuffle(correctness)
            for document_id, is_correct in zip(ids, correctness):
                records.append({
                    "document_id": document_id,
                    "document_type": doc_type,
                    "field": field,
                    "model_confidence": _confidence_for(doc_type, field, is_correct, rng),
                    "is_correct": is_correct,
                })
    return records


VALIDATION_SET = _build_validation_set()

# Today's incoming extraction queue, waiting to be routed to auto-approve or
# human review. Mixes: comfortably high-confidence items, a known-bad segment
# (video_transcript/years_experience) shown at high confidence anyway,
# low-confidence items, and a couple flagged ambiguous_source (the underlying
# document itself was hard to read/contradictory, independent of model
# confidence).
TODAYS_QUEUE = [
    {"document_id": "APP-Q001", "document_type": "chronological_resume", "field": "years_experience", "model_confidence": 0.97, "ambiguous_source": False},
    {"document_id": "APP-Q002", "document_type": "chronological_resume", "field": "candidate_name", "model_confidence": 0.98, "ambiguous_source": False},
    {"document_id": "APP-Q003", "document_type": "functional_resume", "field": "years_experience", "model_confidence": 0.80, "ambiguous_source": False},
    {"document_id": "APP-Q004", "document_type": "video_transcript", "field": "years_experience", "model_confidence": 0.95, "ambiguous_source": False},
    {"document_id": "APP-Q005", "document_type": "video_transcript", "field": "highest_degree", "model_confidence": 0.93, "ambiguous_source": False},
    {"document_id": "APP-Q006", "document_type": "chronological_resume", "field": "certifications", "model_confidence": 0.70, "ambiguous_source": True},
    {"document_id": "APP-Q007", "document_type": "functional_resume", "field": "most_recent_title", "model_confidence": 0.91, "ambiguous_source": False},
    {"document_id": "APP-Q008", "document_type": "video_transcript", "field": "candidate_name", "model_confidence": 0.96, "ambiguous_source": False},
    {"document_id": "APP-Q009", "document_type": "chronological_resume", "field": "highest_degree", "model_confidence": 0.99, "ambiguous_source": False},
    {"document_id": "APP-Q010", "document_type": "video_transcript", "field": "certifications", "model_confidence": 0.85, "ambiguous_source": False},
    {"document_id": "APP-Q011", "document_type": "functional_resume", "field": "candidate_name", "model_confidence": 0.60, "ambiguous_source": False},
    {"document_id": "APP-Q012", "document_type": "video_transcript", "field": "years_experience", "model_confidence": 0.88, "ambiguous_source": True},
]

# A real video-interview transcript excerpt used for the live claude -p
# confidence call — deliberately the same problem segment (years_experience)
# the mock data flags. Candidates describing work history out loud tend to
# hedge, self-correct, and give approximate ranges instead of a clean number.
SAMPLE_TRANSCRIPT_EXCERPT = """
VIDEO INTERVIEW TRANSCRIPT — EXCERPT (auto-generated captions, Candidate #4417)

INTERVIEWER: Can you walk me through your background?

CANDIDATE: Yeah, for sure. So I've been doing backend engineering for, gosh,
I want to say around eight years now? Maybe closer to nine if you count the
two years I was doing it part time during grad school. I started full time
right after undergrad, so we're talking two thousand fifteen-ish, and then I
took about eight months off in twenty nineteen for a family thing, so it's
a little fuzzy exactly how you'd count the total. Somewhere in the seven to
nine year range I'd say, depending on how you slice it.
"""
