# AGENTS.md

Standing brief for any agent working in this repo. Read this before writing code.

---

## What we're building

SIH 2026, Problem Statement **SIH26165** (Oil India Limited, Smart Automation).

An AI/NLP service that ingests free-text industrial safety reports
(unsafe act, unsafe condition, near-miss) and outputs:

1. `sif_potential` — true/false
2. `lsr_tag` — one of the nine IOGP Life-Saving Rules below, or `"None"`
3. Structured precursor fields — `activity`, `location`, `barrier_failure`

Plus a dashboard ranking sites and activities by SIF-precursor density and
surfacing recurring precursor patterns.

---

## Non-negotiable definition

**SIF-potential = a high-energy hazard is present AND a control was missing,
bypassed, or ineffective.**

Outcome severity is irrelevant. Judge fatal POTENTIAL only.

- A paper cut sustained next to a live 11kV panel with the guard removed
  **IS** SIF-potential.
- A dramatic-sounding slip on a wet floor is **NOT**.
- A fatality is **not** automatically SIF-potential. A fatal heart attack on
  site has no high-energy hazard and no failed control.

Evidentiary standard: the control failure must be stated or directly
described in the report text. Do not infer a missing control from the fact
that harm occurred. If a report describes an outcome without describing the
state of any control, set `sif_potential = false` and
`barrier_failure = "not stated in narrative"`.

High-energy hazard categories: electrical, gravitational/height, mechanical
motion, pressure, thermal, vehicle, toxic/asphyxiant.

---

## The nine IOGP Life-Saving Rules

Exact strings. `lsr_tag` must match one of these character-for-character, or be
`"None"`.

1. Bypassing Safety Controls
2. Confined Space
3. Driving
4. Energy Isolation
5. Hot Work
6. Line of Fire
7. Safe Mechanical Lifting
8. Work Authorisation
9. Working at Height

Note the British spelling in **Work Authorisation**.

`"None"` on a `sif_potential: true` row is legitimate. Do not force a tag.

---

## Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.14 + FastAPI |
| Runtime LLM | Gemini API, model ID `gemini-3.8-flash` |
| SDK | `google-generativeai` 0.8.6 |
| Database | Supabase (Postgres) |
| Frontend | React + Tailwind + Recharts |
| Tests | pytest |

`google-generativeai` 0.8.6 is deprecated in favour of `google-genai`. We are
staying on 0.8.6 for this build. Do not migrate without being asked.

Do not add auth, user accounts, notifications, or Docker. Out of scope.

---

## Data integrity (critical — read twice)

An earlier agent fabricated an entire "OSHA" dataset rather than report that
the source file lacked a narrative column. It cost real time to catch.

- **NEVER** invent, synthesise, or fill in data that is meant to come from a
  real source file. If a required column does not exist, **STOP and report it**.
  Do not generate placeholder content.
- Synthetic data is allowed **only** in `scripts/generate_data.py`, and only
  written to files whose names begin with `synthetic_`.
- Any script reading `data/raw/` must print row counts after **every** filter
  step and fail loudly if a filter yields zero rows.
- Any script producing a data file must assert its own output: that filtered
  values actually satisfy the filter, and that every id traces back to the
  source.
- **Never auto-label the holdout sets.** They are human ground truth. Read only.

---

## Privacy

Source OSHA files contain employer names, addresses, coordinates, and victim
names. These must never reach the repo, the outputs, or a demo.

Always drop: `Employer`, `Address1`, `Address2`, `City`, `Latitude`,
`Longitude`, `Zip`, `Establishment Name`, `Site City`, `Site County`,
`Victim Name (Age)`.

`data/raw/` is gitignored and stays that way.

---

## Data files

| Path | What it is |
|---|---|
| `data/raw/January2015toNovember2025.csv` | OSHA Severe Injury Report, 105,996 rows. `Final Narrative` is the text column, `Primary NAICS` the industry column. **The only real narrative source.** |
| `data/raw/data.xlsx` | OSHA fatality metadata. Header on row 3 (`skiprows=2`). **Has no narrative column.** Useful only for inspection numbers. |
| `data/osha_holdout_unlabeled.xlsx` | 150 SIR rows sampled for human labeling (90 high severity, 60 hospitalized). Awaiting labels. |
| `data/fatality_holdout_FINAL.xlsx` | 48 fatality narratives, human-labeled (19 TRUE / 29 FALSE). Sheet `labeling` is ground truth; `ai_labels_v0` holds superseded AI labels kept for comparison. **Read only.** |

Oil and gas filter: `Primary NAICS` starts with `2111`, `2131`, or `486`.

---

## Rules for agents

- Never hardcode secrets. Use `.env` and `python-dotenv`.
- Every LLM response is Pydantic-validated before use. One retry on malformed
  JSON, then return status `needs_review`. Never crash.
- Cache classification by SHA-256 of `report_text`. Demos must be reproducible
  and must not re-bill the API.
- Temperature `0.1` for all classification calls.
- Hardcode the model ID. Do not list available models on every run.
- Write a pytest test for every endpoint before moving on.
- Print what you did and what you changed. Do not silently rewrite working
  files.

---

## Evaluation

- Optimise for **recall on the SIF-positive class**. Missing a precursor is the
  expensive error.
- Report per-class precision, recall, F1, and a confusion matrix.
- Always include a keyword baseline for comparison: flag any report containing
  harness, isolation, confined, permit, live, or guard.
- Synthetic data is for prompt development only. **Never** put synthetic rows
  in a test set.
- The holdout runs **once**, at the end. Report the honest number and explain
  any gap against validation performance.

---

## Known findings (for the report)

- A zero-shot LLM labeled 98% of oil-and-gas fatality narratives as
  SIF-potential. Human labelers applying the two-part test marked 40%. Nearly
  every disagreement is the model treating a fatal outcome as evidence of a
  control failure — exactly the reasoning error SIF-precursor methodology
  exists to correct.
- Many OSHA abstracts describe the outcome without stating whether a control
  was present, so `barrier_failure` is often "not stated in narrative" and the
  row is correctly FALSE. This is a property of the source, not a labeling flaw.
- The fatality holdout spans 1992–2019, so writing conventions vary (older
  records are ALL CAPS). Treated as a robustness property, not cleaned.
