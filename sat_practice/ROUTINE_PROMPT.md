# Routine task prompt — SAT Practice (Nirvaan)

This is the exact text to paste into the Routine's task field in
claude.ai/code/routines. Kept here, version-controlled alongside the data
it drives (`score_log.json`, `passage_topics_used.json`, `config.json`,
`tests/`), so changes to the routine's logic are tracked the same way
changes to the logs are.

If you edit this file, copy the updated prompt block back into the
Routine's task field manually — editing this file does not update the
Routine itself.

---

## Prompt to paste

```
You are running a daily adaptive SAT Reading & Writing practice program for a
high school student named Nirvaan. This is a recurring task — read all repo
files first to understand full history before doing anything, including
/sat_practice/config.json for the student's and parent's email addresses.

STEP 1 — GRADE YESTERDAY'S TEST (skip if no prior test exists)
- Look in /sat_practice/tests/ for the most recent test file that does not yet
  have a "graded: true" flag. Ignore any file marked "sample": true — those
  are dry runs used to review question format, not real test days.
- Search Gmail for a reply from Nirvaan's email address (from
  /sat_practice/config.json) to that test's email (match by subject line,
  which includes the test's date).
- If a submission is found: it may be a plain numbered list ("1. B  2. D...")
  or the fuller text produced by the HTML attachment's "Copy results for
  your records" button (a self-reported score summary followed by the
  same numbered list). Either is fine — extract just the answers from it.
  IMPORTANT: always grade those answers yourself against the answer key
  stored in that test file. Never trust a self-reported score in the
  reply text, even if it looks correctly computed — recompute it, and
  compute accuracy separately for each domain (Information and Ideas /
  Craft and Structure).
- If no submission is found after 20+ hours since it was sent: mark that
  test as "missed" in score_log.json, do NOT change difficulty for either
  domain (hold steady), and note the miss in the email to the parent.

STEP 2 — UPDATE SCORE LOG
Append an entry to /sat_practice/score_log.json with: date, questions
attempted, accuracy per domain, difficulty tier per domain (before and
after adjustment), and any notes.

STEP 3 — ADJUST DIFFICULTY (per domain, independently)
Use a 5-tier scale (1 = foundational, 5 = advanced/reach-level). Apply these
rules using the average accuracy of the LAST 3 GRADED tests for that domain
(if fewer than 3 exist, use whatever is available):
- Average accuracy >= 85% → increase that domain's tier by 1 (max tier 5)
- Average accuracy <= 60% → decrease that domain's tier by 1 (min tier 1)
- Otherwise → hold the current tier
Track Information and Ideas and Craft and Structure as SEPARATE tiers since
he may be stronger in one than the other. Start both at tier 2 if this is
the very first run.

Tier definitions to calibrate question difficulty:
- Tier 1: short, concrete passages (25–60 words); literal comprehension;
  vocabulary is common; distractors are clearly wrong on a careful read.
- Tier 2: passages 60–100 words; one inferential step required; vocabulary
  includes some academic/domain words; one plausible-but-wrong distractor.
- Tier 3: passages 90–130 words; multi-step inference or synthesis of two
  ideas in the passage; vocabulary includes precise/nuanced word choices;
  two distractors are genuinely tempting.
- Tier 4: passages 110–150 words, denser argumentation or older/formal
  prose style (matching historical documents or academic register);
  distractors require careful textual proof to eliminate.
- Tier 5: full 150-word passages at official SAT "hard" difficulty —
  subtle authorial tone, layered argument structure, or cross-text
  comparison; all distractors are plausible without close reading.

STEP 4 — GENERATE TODAY'S TEST
- Target length: 15–20 minutes. Use ~90–120 seconds per question as the
  pacing assumption (slower than real SAT pace since this is training, not
  test day) → build 10 questions total. Keep it short enough to actually
  finish in one sitting — a shorter completed test beats a longer one that
  gets abandoned partway through.
- Split questions between domains proportional to real SAT weighting:
  roughly 5 Craft and Structure, 5 Information and Ideas (52%/48%, rounded).
- Within Craft and Structure, rotate across its sub-types — Words in
  Context, Text Structure and Purpose, Cross-Text Connections — across
  different days rather than all three in one short test; aim for roughly
  even coverage over a week or two rather than every subtype every day.
- Within Information and Ideas, do the same across its sub-types — Central
  Ideas and Details, Inferences, Command of Evidence.
- Every question uses the current tier for its domain (from Step 3).
- Passage topics: rotate across the same categories the real digital SAT
  draws from — literature/literary nonfiction, natural science, social
  science, and historical/founding documents (or historically-styled
  prose). Check /sat_practice/passage_topics_used.json and avoid repeating
  a specific topic within the last 10 school days; log new topics used.
- Format each question exactly like the digital SAT: one short passage,
  one question, four answer choices (A–D), only one correct answer.
- CRITICAL — DO NOT copy or closely paraphrase actual College Board or
  Bluebook passages or questions. Write fully original passages and
  questions that match the official style, structure, difficulty
  calibration, and question-type conventions. This must be original
  content inspired by the format, never reproduced text.
- Write a one-sentence explanation for each correct answer, referencing
  what in the passage proves it.

STEP 5 — SAVE TO REPO
Create /sat_practice/tests/[DATE]_test.json containing: all questions,
answer choices, correct answers, explanations, the difficulty tier used
per domain, and "graded: false".

Also run:
  python3 sat_practice/generate_test_html.py sat_practice/tests/[DATE]_test.json
This writes /sat_practice/tests/[DATE]_test.html — a standalone page with
no answer key, so Nirvaan can open it directly (after a `git pull`, or
from a fresh clone) if the Gmail connector isn't delivering the email.
Commit both the .json and .html files.

STEP 6 — EMAIL NIRVAAN
Send an email to Nirvaan's address (from /sat_practice/config.json) with:
- Subject: "SAT Practice — [DATE] — Tier [Info tier]/[Craft tier]"
- The test questions and answer choices only (NO answer key) in the email body
- Attach /sat_practice/tests/[DATE]_test.html to this email — it's the same
  self-grading page (see Step 5), included so he can take and instantly
  grade the test from the attachment even if something's off with viewing
  the email body itself. His copy of that file does contain the correct
  answers and explanations in its underlying data (needed for it to grade
  itself); they only surface in the page after he answers and taps
  "Submit Test," never before.
- A one-line instruction: reply to this email with his answers as a
  numbered list (e.g., "1. B  2. D  3. A...") within 24 hours
- A short, encouraging note if yesterday's score improved

STEP 7 — EMAIL THE PARENT
Send a separate email to the parent's address (from
/sat_practice/config.json) with:
- Yesterday's results (if graded): accuracy per domain, tier changes
- Today's test difficulty tiers and question count
- Attach /sat_practice/tests/[DATE]_test.html here too, so the parent has
  the same interactive copy on hand
- A flag if a test was missed or if either domain has been stuck at the
  same tier for 5+ consecutive tests (may indicate a plateau worth a
  strategy conversation, not just more volume)

Run this entire sequence every time you are triggered. Always read the
full score_log.json history before making any difficulty decision — never
guess or assume prior state.
```

---

## Setup checklist

1. Repo scaffolding (`score_log.json`, `tests/`, `passage_topics_used.json`, `config.json`) — done.
2. In Claude Code web (claude.ai/code/routines) → New routine → connect this repo.
3. Add the Gmail connector to the routine so it can send and search email.
4. Paste the prompt block above into the routine's task field.
5. Set schedule → Daily → pick a time (routines run in **UTC**, so convert Nirvaan's actual local wake-up/practice time).
6. Run it once manually first and check: does the email format look right? Are questions genuinely SAT-style? Is the difficulty reasonable for tier 2? (See `tests/SAMPLE_test.json` for a dry-run example already reviewed.)
7. Only then let it run on autopilot.

## Notes worth knowing

- Routines need a Pro, Max, Team, or Enterprise plan with Claude Code on the web enabled.
- The grading step depends on Nirvaan actually replying by email — if he texts or tells you verbally instead, the system won't see it and will hold difficulty steady. Worth telling him explicitly to reply to the test email.
- Once Gmail is sending: every test email to Nirvaan and the parent also carries `sat_practice/tests/[DATE]_test.html` as an attachment — the same self-grading page, so either of you can just open the attachment straight from the email instead of pulling the repo.
- While the Gmail connector isn't sending yet: Nirvaan can `git pull` (or `git clone` once) this repo and open `sat_practice/tests/[DATE]_test.html` directly in a browser — no server, no login. It grades itself the moment he taps "Submit Test" (correct answers and explanations are embedded in the page's data, revealed only after he answers), shows per-domain accuracy right there, and has a "Copy results for your records" button formatted so it's easy to paste into `score_log.json` by hand. Note: this in-browser grading does NOT write to `score_log.json` automatically — someone still has to copy that summary in, or wait for Gmail to come back so the routine's own Step 1–2 does it.
- After a couple weeks of real data, it's worth opening `score_log.json` yourself and sanity-checking the tier progression — if it's climbing too fast or stuck too long, tighten the 85%/60% thresholds in the prompt above (and update this file to match).
- 2026-09-18: shortened tests from 22–28 questions (30–45 min) to 10 questions (15–20 min) — Nirvaan was struggling to finish the longer ones. Subtype coverage within each domain now rotates across days instead of all three subtypes appearing in every test. If 10 questions turns out too short (or still too long), adjust the target length/count in STEP 4 above and re-paste into the routine.
