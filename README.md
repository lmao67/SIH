# SIF Sentinel

**AI/NLP engine that detects Serious Injury & Fatality (SIF) precursors in unsafe-act, unsafe-condition and near-miss reports.**

Smart India Hackathon 2026 · Problem Statement **SIH26165** · Oil India Limited · Smart Automation

---

## The problem

Oil India's HSSE platform already collects thousands of free-text safety reports. They are triaged manually, monthly or quarterly. Buried among hundreds of routine observations sit the few that are genuine warnings of a fatality, and there is no reliable way to find them at that volume and cadence.

Industry research establishes that **low-severity incidents do not share causes with fatalities**. Counting incidents therefore never finds the dangerous ones. Leading operators separate the ~20–25% of reports carrying genuine fatal potential and concentrate attention there.

## The definition this system enforces

> **SIF-potential = a high-energy hazard is present AND a control was missing, bypassed, or ineffective.**
>
> **Evidentiary standard:** the control failure must be *stated or directly described* in the report text. A serious injury is not evidence of a missing barrier.

Outcome severity is irrelevant. The system judges fatal *potential* only.

- A paper cut sustained beside a live 11 kV panel **with the guard removed** → **is** a precursor
- A dramatic slip on a wet floor → **is not**

## What it outputs

For every report:

| Field | Description |
|---|---|
| `sif_potential` | boolean |
| `lsr_tag` | one of nine IOGP Life-Saving Rules, or `None` |
| `energy_type` | electrical / height / mechanical / pressure / thermal / vehicle / toxic / none |
| `activity`, `location`, `barrier_failure` | extracted precursor fields |
| `confidence` | below threshold routes to human review |
| `reasoning` | plain-language justification citing the report's own words |

---

## Architecture

```
Report submitted
      ↓
Preprocess — SHA-256 hash, cache lookup, dedupe
      ↓
AI/NLP classifier — six-step derivation procedure
      ↓
Validation — Pydantic, closed 9-rule enum, confidence gate ──→ Human review queue
      ↓                                                              │
PostgreSQL store ←──────── overrides become verified labels ─────────┘
      ↓
HSE triage dashboard — precursor density, recurring patterns, audit trail
```

### The six-step procedure

The model is **forbidden** from deciding `sif_potential` directly. It must:

1. Identify the highest-energy hazard present
2. State which control was missing, bypassed or ineffective
3. **Derive** the verdict mechanically from steps 1 and 2
4. Assign one IOGP Life-Saving Rule, or `None`
5. Extract activity and location
6. Score confidence on evidential clarity

Forcing a commitment to energy type and barrier state *before* the verdict is what defeats outcome bias.

---

## Results

Evaluated against a human-labelled holdout, single model, single temperature.

| Metric | SIF Sentinel | Keyword baseline |
|---|:---:|:---:|
| Non-precursor F1 | **0.92** | — |
| Non-precursor precision | **96.7%** | — |
| Non-precursor recall | **87.9%** | — |
| SIF-positive F1 | **0.11** | 0.11 |
| Rows provenance-verified | **150 / 150** | — |
| Endpoint tests | **9 / 9 passing** | — |

**Reported honestly:** the single-model evaluation covers 38 rows, of which 5 are positive cases. That is too few for a reliable positive-class recall estimate, so we do not headline one. `eval/run_eval.py` suppresses any metric where class support is under five. The constraint is free-tier API quota (20 requests/day/project), not method.

See [`eval/results.md`](eval/results.md).

---

## Data

| Source | Use |
|---|---|
| OSHA Severe Injury Reports (29 CFR 1904.39), Jan 2015 – Nov 2025 | 105,996 real narratives; primary corpus |
| Filtered to NAICS 2111 / 2131 / 486 | 2,845 oil, gas and pipeline rows |
| Narratives 250–1800 characters | 910 usable |
| Sampled holdout | 150 rows, human-labelled (30 TRUE / 120 FALSE) |

**Labelling:** AI pre-fill with human adjudication. Ground truth was never AI-labelled unsupervised — if the model writes the answer key and the same model is graded, the score means nothing.

**Provenance:** every holdout row is machine-matched to its source file character-for-character.

```bash
python scripts/verify_provenance.py data/osha_holdout_labeled.xlsx
# → 150/150 rows verified against source
```

Also exposed as `GET /provenance` and shown as a live badge on the dashboard.

### Data files are not in this repo

`data/raw/` and the labelled workbooks are gitignored. The OSHA source contains employer names, addresses and coordinates. Download the source yourself from [osha.gov/severe-injury-reports](https://www.osha.gov/severe-injury-reports) and run `scripts/build_holdout.py`.

---

## Running it

### Prerequisites
Python 3.11+, Node 18+, a Gemini API key.

### Setup

```bash
git clone https://github.com/<you>/sif-sentinel.git
cd sif-sentinel

python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env      # then add your GEMINI_API_KEY
```

### Backend

```bash
python -m uvicorn app.main:app --reload
```

Interactive API docs at `http://127.0.0.1:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
python -m pytest tests/ -v
```

### Evaluation

```bash
python eval/run_eval.py
```

Cached rows are free and tagged `[CACHED]`; only uncached rows consume quota.

---

## API

| Endpoint | Purpose |
|---|---|
| `POST /classify` | classify one report |
| `POST /classify/batch` | classify a CSV or XLSX |
| `GET /reports` | stored results, filterable by site and flag |
| `GET /provenance` | live data-integrity check |

---

## Repository layout

```
app/main.py                  FastAPI service
prompts/classify.py          the system prompt — this is the classifier
scripts/build_holdout.py     samples the holdout from the OSHA source
scripts/verify_provenance.py character-for-character source verification
eval/run_eval.py             evaluation harness with keyword baseline
frontend/                    React + Tailwind + Recharts dashboard
tests/test_api.py            endpoint and edge-case suite
AGENTS.md                    project specification and engineering rules
```

---

## Engineering guarantees

These exist because we hit the failures they prevent.

- **Single-model discipline.** Exactly one model per evaluation. No pools, no fallback. On a quota error the run exits rather than substituting. Model and key are recorded on every prediction. An earlier build silently rotated across six Gemini variants as quotas expired, producing a result that could not be reproduced.
- **Data integrity.** No script may invent data intended to come from a real source. Every data script prints row counts after each filter step and asserts its own output. An earlier build fabricated a dataset rather than report a missing column.
- **Reproducibility.** SHA-256 response caching, temperature 0.1, closed enum validation on the rule tag.
- **Privacy.** Employer names, addresses, coordinates and personal identifiers are dropped at load and never written to any output.

---

## Limitations

Stated plainly, because they matter more than the headline numbers.

1. **No access to Oil India's own corpus.** Calibration on 200–500 of their reports would be required before deployment. The rubric, workbook and adjudication protocol transfer directly.
2. **Small evaluation sample.** 38 rows on a single model, 5 positive cases. Free-tier quota, not method.
3. **One unresolved definitional boundary.** Every false negative traced to the same question: does equipment integrity failure (a snapped wire rope, broken tubing) count as an ineffective control? Our proposed rule is that it counts where an inspection or maintenance regime should have detected it, and does not where the report gives no indication of that regime's state.
4. **Source data describes outcomes, not precursors.** OSHA abstracts frequently record what happened without recording control state. Many rows are correctly negative for reasons of documentation quality — itself an actionable organisational finding.
5. **Requires a hosted model today.** Distillation into a local student model is the planned path to offline, on-premise operation.

---

## Roadmap

1. Add 10 few-shot examples from labelled negatives — the prompt currently runs zero-shot
2. Resolve the equipment-failure boundary in prompt and rubric simultaneously
3. Complete the evaluation to 150 rows on one model
4. Distil to a local DistilBERT student for offline inference
5. Calibrate on Oil India's own reports
6. Migrate `google.generativeai` → `google-genai`

---

## References

- **IOGP Report 459** — Life-Saving Rules, our classification taxonomy
- **Edison Electric Institute** — SIF Precursor research and the Safety Classification and Learning model
- **DEKRA (Martin & Black, 2015)** — low-severity incidents do not share causation with fatalities
- **OSHA Severe Injury Reports** — [osha.gov/severe-injury-reports](https://www.osha.gov/severe-injury-reports)
- **Baghjan Blowout, Assam 2020** — Oil India Well No. 5; the NGT inquiry found the event preventable

---

## Team

Team [Name] · Team ID [ID] · Smart India Hackathon 2026

## Licence

MIT
