import os
import sys
import json
import re
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Literal, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError
import dotenv

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env
dotenv.load_dotenv(PROJECT_ROOT / ".env")

import google.generativeai as genai
import pandas as pd

from prompts.classify import (
    SYSTEM_PROMPT,
    build_user_prompt,
    VALID_LSR_TAGS,
    ValidLSR,
)

# App configuration
MODEL_ID = "gemini-3.8-flash"
TEMPERATURE = 0.1
CACHE_FILE = PROJECT_ROOT / "data" / "cache.json"
REPORTS_FILE = Path(os.getenv("REPORTS_FILE", str(PROJECT_ROOT / "data" / "reports.json")))

def get_available_api_keys() -> Dict[int, str]:
    """Read whatever GEMINI_API_KEY_N variables are present in .env.

    Returns a dict mapping key number (int) -> api key string.
    Only non-empty keys are included.
    """
    dotenv.load_dotenv(PROJECT_ROOT / ".env", override=True)
    available: Dict[int, str] = {}
    pattern = re.compile(r"^GEMINI_API_KEY_(\d+)$")
    for k, v in os.environ.items():
        m = pattern.match(k)
        if m and v and v.strip():
            try:
                available[int(m.group(1))] = v.strip()
            except ValueError:
                pass

    if 1 not in available:
        fallback = os.getenv("GEMINI_API_KEY")
        if fallback and fallback.strip():
            available[1] = fallback.strip()

    return dict(sorted(available.items()))


def get_api_key(key_num: int = 1) -> Optional[str]:
    """Retrieve Gemini API key by index, falling back to GEMINI_API_KEY for key 1."""
    avail = get_available_api_keys()
    return avail.get(key_num)


# Configure default Gemini key
avail_keys = get_available_api_keys()
if avail_keys:
    first_key_num = 1 if 1 in avail_keys else next(iter(avail_keys))
    genai.configure(api_key=avail_keys[first_key_num])

app = FastAPI(
    title="SIH 2026 SIF-Precursor AI Classifier",
    description="Industrial Safety free-text report classifier using Gemini API and IOGP Life-Saving Rules.",
    version="1.0.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Pydantic Models
# -----------------------------------------------------------------------------
class StrictLLMResponse(BaseModel):
    """Schema for validating raw LLM JSON output."""
    sif_potential: bool
    confidence: float = Field(ge=0.0, le=1.0)
    lsr_tag: ValidLSR
    activity: str
    location: str
    barrier_failure: str
    reasoning: str


class ClassifyRequest(BaseModel):
    report_text: str = Field(description="Free-text narrative of safety incident, near-miss, or hazard")
    site: Optional[str] = Field(default=None, description="Industrial site or operational unit name")


class ClassifyResponse(BaseModel):
    id: Optional[int] = None
    sha256: str
    report_text: str
    site: Optional[str] = None
    status: Literal["success", "needs_review"]
    sif_potential: bool
    confidence: float
    lsr_tag: str
    energy_type: Optional[str] = None
    activity: str
    location: str
    barrier_failure: str
    reasoning: str
    cached: bool = False
    timestamp: str
    model: str = MODEL_ID
    key_id: str = "key_1"


class BatchClassifyRequest(BaseModel):
    file_path: str = Field(description="Path to .xlsx or .csv file containing incidents")
    text_column: str = Field(description="Name of the text column containing narratives")
    site_column: Optional[str] = Field(default=None, description="Optional column name for site/location")
    checkpoint_path: Optional[str] = Field(
        default="data/batch_checkpoint.json",
        description="Path to save intermediate checkpoints every 10 rows"
    )
    delay_seconds: float = Field(default=0.05, ge=0.0, description="Rate-limiting delay between LLM calls")


class BatchClassifyResponse(BaseModel):
    status: str
    file_path: str
    total_rows: int
    classified_count: int
    checkpoint_file: str
    results_summary: Dict[str, int]


class ProvenanceResponse(BaseModel):
    status: str
    holdout_file: str
    source_file: str
    total_rows: int
    verified_count: int
    summary: str
    failing_records: List[Dict[str, Any]]


# -----------------------------------------------------------------------------
# Cache and Persistence Utilities
# -----------------------------------------------------------------------------
def get_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_cache() -> Dict[str, Dict[str, Any]]:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_to_cache(sha256_hash: str, data: Dict[str, Any], key_id: Optional[str] = None) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache = load_cache()
    data_to_save = dict(data)
    data_to_save["model"] = MODEL_ID
    if key_id:
        data_to_save["key_id"] = key_id
    elif "key_id" not in data_to_save or not data_to_save["key_id"]:
        data_to_save["key_id"] = "key_1"
    cache[sha256_hash] = data_to_save
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def load_reports() -> List[Dict[str, Any]]:
    if REPORTS_FILE.exists():
        try:
            with open(REPORTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_report_record(record: Dict[str, Any]) -> None:
    REPORTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    reports = load_reports()
    # Update existing by sha256 or append
    sha = record.get("sha256")
    updated = False
    for i, r in enumerate(reports):
        if r.get("sha256") == sha:
            reports[i] = record
            updated = True
            break
    if not updated:
        reports.append(record)
    with open(REPORTS_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)


# -----------------------------------------------------------------------------
# LLM Invocation & Parsing Logic
# -----------------------------------------------------------------------------
def clean_json_string(raw: str) -> str:
    """Remove markdown code blocks or whitespace around JSON."""
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*```$", "", s)
        s = s.strip()
    return s


def is_quota_error(exc: Exception) -> bool:
    """Check if an exception is a quota or rate-limit error (429, ResourceExhausted, quota limit)."""
    err_str = str(exc).lower()
    return (
        "429" in str(exc)
        or "resourceexhausted" in err_str
        or "quota" in err_str
        or "rate limit" in err_str
    )


def call_gemini_raw(prompt_text: str) -> str:
    """Call the single configured Gemini model (gemini-3.8-flash).

    On any quota error, print the error and exit with code 1 immediately.
    Never switch models under any circumstance.
    """
    gen_config = genai.GenerationConfig(
        temperature=TEMPERATURE,
        response_mime_type="application/json",
    )
    model = genai.GenerativeModel(
        model_name=MODEL_ID,
        generation_config=gen_config,
    )
    try:
        res = model.generate_content(prompt_text)
        return res.text
    except Exception as e:
        if is_quota_error(e):
            print(f"FATAL Quota Error on model {MODEL_ID}: {e}", file=sys.stderr)
            sys.exit(1)
        raise e


def classify_single_narrative(
    report_text: str,
    site: Optional[str] = None,
    key_id: str = "key_1"
) -> ClassifyResponse:
    """Core classification routine with caching and retry on validation failure."""
    now_iso = datetime.now(timezone.utc).isoformat()
    text_clean = (report_text or "").strip()
    sha = get_sha256(text_clean)

    # 1. Handle empty / whitespace-only narratives gracefully
    if not text_clean:
        response_obj = ClassifyResponse(
            sha256=sha,
            report_text=report_text or "",
            site=site,
            status="needs_review",
            sif_potential=False,
            confidence=0.0,
            lsr_tag="None",
            activity="None",
            location="None",
            barrier_failure="not stated in narrative",
            reasoning="Empty or blank narrative provided. Needs human review.",
            cached=False,
            timestamp=now_iso,
            model=MODEL_ID,
            key_id=key_id,
        )
        save_report_record(response_obj.model_dump())
        return response_obj

    # 2. Check Cache
    cached_data = load_cache().get(sha)
    if cached_data:
        record = dict(cached_data)
        record["cached"] = True
        if site and not record.get("site"):
            record["site"] = site
        if not record.get("key_id"):
            record["key_id"] = key_id
        response_obj = ClassifyResponse(**record)
        save_report_record(response_obj.model_dump())
        return response_obj

    # 3. Call LLM with 1 retry on invalid JSON or invalid lsr_tag
    prompt = f"""{SYSTEM_PROMPT}

{build_user_prompt(text_clean)}
"""
    max_attempts = 2
    validated_model: Optional[StrictLLMResponse] = None
    last_error: Optional[str] = None

    for attempt in range(max_attempts):
        try:
            raw_text = call_gemini_raw(prompt)
            cleaned = clean_json_string(raw_text)
            parsed_json = json.loads(cleaned)

            # Pydantic validation (including exact LSR rule match)
            validated_model = StrictLLMResponse.model_validate(parsed_json)
            break
        except Exception as e:
            if is_quota_error(e):
                print(f"FATAL Quota Error on model {MODEL_ID}: {e}", file=sys.stderr)
                sys.exit(1)
            last_error = str(e)
            if attempt == 0:
                # One retry on malformed JSON or validation failure
                continue

    # 4. Handle result
    if validated_model:
        response_obj = ClassifyResponse(
            sha256=sha,
            report_text=report_text,
            site=site,
            status="success",
            sif_potential=validated_model.sif_potential,
            confidence=validated_model.confidence,
            lsr_tag=validated_model.lsr_tag,
            activity=validated_model.activity,
            location=validated_model.location,
            barrier_failure=validated_model.barrier_failure,
            reasoning=validated_model.reasoning,
            cached=False,
            timestamp=now_iso,
            model=MODEL_ID,
            key_id=key_id,
        )
        # Store in cache
        save_to_cache(sha, response_obj.model_dump(), key_id=key_id)
    else:
        # Fallback to needs_review rather than raising an exception
        response_obj = ClassifyResponse(
            sha256=sha,
            report_text=report_text,
            site=site,
            status="needs_review",
            sif_potential=False,
            confidence=0.0,
            lsr_tag="None",
            activity="Unclassified",
            location="Unclassified",
            barrier_failure="not stated in narrative",
            reasoning=f"Automated classification failed validation after 1 retry: {last_error}",
            cached=False,
            timestamp=now_iso,
            model=MODEL_ID,
            key_id=key_id,
        )

    # Store in reports
    save_report_record(response_obj.model_dump())
    return response_obj


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.post("/classify", response_model=ClassifyResponse)
def classify_endpoint(payload: ClassifyRequest):
    """Classify a single incident report text for SIF-potential and IOGP Life-Saving Rules."""
    return classify_single_narrative(payload.report_text, payload.site)


@app.post("/classify/batch", response_model=BatchClassifyResponse)
def classify_batch_endpoint(payload: BatchClassifyRequest):
    """Process an Excel or CSV file in batches, rate-limited, with intermediate checkpoints."""
    file_path = Path(payload.file_path)
    if not file_path.is_absolute():
        file_path = PROJECT_ROOT / file_path

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch file not found: {payload.file_path}"
        )

    # Load file
    ext = file_path.suffix.lower()
    try:
        if ext == ".csv":
            df = pd.read_csv(file_path, low_memory=False)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {ext}. Must be .xlsx or .csv"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading {file_path.name}: {e}"
        )

    if payload.text_column not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Column '{payload.text_column}' not found in file. Available: {df.columns.tolist()}"
        )

    checkpoint_file = Path(payload.checkpoint_path)
    if not checkpoint_file.is_absolute():
        checkpoint_file = PROJECT_ROOT / checkpoint_file
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

    results = []
    total_rows = len(df)

    for idx, row in df.iterrows():
        text_val = str(row[payload.text_column]) if pd.notna(row[payload.text_column]) else ""
        site_val = None
        if payload.site_column and payload.site_column in df.columns:
            site_val = str(row[payload.site_column]) if pd.notna(row[payload.site_column]) else None

        res = classify_single_narrative(text_val, site_val)
        results.append(res.model_dump())

        # Rate limiting delay
        if payload.delay_seconds > 0 and not res.cached:
            time.sleep(payload.delay_seconds)

        # Checkpoint every 10 rows
        if (len(results) % 10 == 0) or (len(results) == total_rows):
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "progress": f"{len(results)}/{total_rows}",
                    "results": results
                }, f, indent=2)

    sif_pos = sum(1 for r in results if r.get("sif_potential") is True)
    sif_neg = sum(1 for r in results if r.get("sif_potential") is False)
    needs_rev = sum(1 for r in results if r.get("status") == "needs_review")

    return BatchClassifyResponse(
        status="completed",
        file_path=str(payload.file_path),
        total_rows=total_rows,
        classified_count=len(results),
        checkpoint_file=str(checkpoint_file),
        results_summary={
            "sif_positive": sif_pos,
            "sif_negative": sif_neg,
            "needs_review": needs_rev,
        }
    )


def infer_energy_type(pred: Dict[str, Any], narrative: str) -> str:
    """Infer the energy category from model outputs and narrative."""
    lsr = str(pred.get("lsr_tag") or "None").strip()
    reasoning = str(pred.get("reasoning") or "").lower()
    barrier = str(pred.get("barrier_failure") or "").lower()
    act = str(pred.get("activity") or "").lower()
    narr = (narrative or "").lower()
    combined = f"{reasoning} {barrier} {act} {narr}"

    if lsr == "Working at Height" or "height" in combined or "fall" in combined or "gravitational" in combined or "ladder" in combined or "scaffold" in combined:
        return "height"
    if lsr == "Driving" or "vehicle" in combined or "truck" in combined or "forklift" in combined or "traffic" in combined:
        return "vehicle"
    if lsr == "Hot Work" or "thermal" in combined or "burn" in combined or "steam" in combined or "heat" in combined or "hot water" in combined or "flame" in combined:
        return "thermal"
    if "electric" in combined or "voltage" in combined or "shock" in combined or "arc" in combined or "11kv" in combined:
        return "electrical"
    if "pressure" in combined or "pressur" in combined or "hydraulic" in combined or "pneumatic" in combined or "pipe burst" in combined or "kick" in combined:
        return "pressure"
    if lsr == "Confined Space" or "toxic" in combined or "gas" in combined or "chemical" in combined or "asphyxi" in combined or "h2s" in combined:
        return "toxic"
    if lsr in ["Safe Mechanical Lifting", "Line of Fire"] or "mechanical" in combined or "pinch" in combined or "crush" in combined or "struck" in combined or "line of fire" in combined or "rotat" in combined or "chain" in combined:
        return "mechanical"

    if not pred.get("sif_potential"):
        return "none"
    return "mechanical"


@app.get("/reports", response_model=List[ClassifyResponse])
def get_reports_endpoint(
    site: Optional[str] = Query(None, description="Filter reports by site name (case-insensitive)"),
    sif_potential: Optional[bool] = Query(None, description="Filter by SIF potential (true/false)"),
    lsr_tag: Optional[str] = Query(None, description="Filter by LSR tag (exact or case-insensitive)"),
):
    """Retrieve stored classification results with optional site, SIF, and LSR filters.
    In dashboard mode, strictly reads only rows whose id maps to the OSHA holdout set
    (ids 1-150 present in eval/partial_results.json). Everything else is excluded.
    In test mode (e.g. pytest / test store), reads from the test store.
    """
    is_test_env = "test" in REPORTS_FILE.name.lower() or "pytest" in sys.modules

    if is_test_env:
        raw_reports = load_reports()
        reports = list(raw_reports)
    else:
        # Dashboard dataset: read ONLY rows whose id maps to the OSHA holdout set
        # (ids 1-150 present in eval/partial_results.json). Everything else must be excluded.
        partial_path = PROJECT_ROOT / "eval" / "partial_results.json"
        reports = []
        if partial_path.exists():
            try:
                with open(partial_path, "r", encoding="utf-8") as f:
                    partial_data = json.load(f)
                    for k, v in partial_data.items():
                        try:
                            row_id = int(k)
                            if 1 <= row_id <= 150:
                                item = dict(v)
                                item["id"] = row_id
                                reports.append(item)
                        except (ValueError, TypeError):
                            pass
            except Exception:
                reports = []

        # Sort holdout records by ID ascending
        reports.sort(key=lambda x: x.get("id", 0))

    filtered = []
    for idx, r in enumerate(reports, start=1):
        # Ensure id is present
        if not r.get("id"):
            r["id"] = idx
        # Ensure energy_type is populated
        if not r.get("energy_type"):
            r["energy_type"] = infer_energy_type(r, r.get("report_text", ""))

        # Filter site
        if site is not None and site.strip():
            r_site = r.get("site") or ""
            if site.strip().lower() not in r_site.lower():
                continue

        # Filter SIF potential
        if sif_potential is not None:
            if r.get("sif_potential") != sif_potential:
                continue

        # Filter LSR tag
        if lsr_tag is not None and lsr_tag.strip() and lsr_tag != "All":
            r_lsr = r.get("lsr_tag") or "None"
            if lsr_tag.strip().lower() != r_lsr.lower():
                continue

        filtered.append(ClassifyResponse(**r))

    return filtered


@app.get("/provenance", response_model=ProvenanceResponse)
def get_provenance_endpoint(
    holdout_file: Optional[str] = Query(
        "data/osha_holdout_unlabeled.xlsx",
        description="Relative path to holdout workbook to verify"
    )
):
    """Run read-only provenance verification checks against the raw source CSV."""
    xlsx_path = PROJECT_ROOT / holdout_file
    csv_path = PROJECT_ROOT / "data" / "raw" / "January2015toNovember2025.csv"

    if not xlsx_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holdout file not found: {holdout_file}"
        )

    if not csv_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw CSV data/raw/January2015toNovember2025.csv not found"
        )

    # Read-only verification (never writes to holdout file)
    df_xlsx = pd.read_excel(xlsx_path)
    df_csv = pd.read_csv(csv_path, low_memory=False)

    source_id_col = next((c for c in ["source_id", "source id", "ID", "id"] if c in df_xlsx.columns), None)
    narrative_col = next((c for c in ["Final Narrative", "narrative", "FinalNarrative"] if c in df_xlsx.columns), None)
    naics_col = next((c for c in ["Primary NAICS", "naics", "PrimaryNAICS", "Site NAICS"] if c in df_xlsx.columns), None)

    if not source_id_col or not narrative_col or not naics_col:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Required verification columns not found in holdout file"
        )

    csv_map = df_csv.set_index("ID")
    total_rows = len(df_xlsx)
    verified_count = 0
    failing_records = []
    valid_naics_prefixes = ("2111", "2131", "486")

    def match_narr(x: str, c: str) -> bool:
        if x == c:
            return True
        if x.replace("\n\n", "\r\n") == c:
            return True
        if x.replace("\r\n", "\n").replace("\r", "\n") == c.replace("\r\n", "\n").replace("\r", "\n"):
            return True
        return False

    for idx, row in df_xlsx.iterrows():
        sid = row[source_id_col]
        row_id = row.get("id", idx + 1)

        if sid not in csv_map.index:
            failing_records.append({
                "row_id": int(row_id),
                "source_id": int(sid),
                "reason": "source_id not found in raw CSV ID column"
            })
            continue

        csv_row = csv_map.loc[sid]
        xlsx_narr = str(row[narrative_col])
        csv_narr = str(csv_row["Final Narrative"])

        if not match_narr(xlsx_narr, csv_narr):
            failing_records.append({
                "row_id": int(row_id),
                "source_id": int(sid),
                "reason": "Narrative character mismatch"
            })
            continue

        raw_naics = str(row[naics_col]).strip().replace(".0", "")
        if not raw_naics.startswith(valid_naics_prefixes):
            failing_records.append({
                "row_id": int(row_id),
                "source_id": int(sid),
                "reason": f"Primary NAICS '{raw_naics}' does not start with 2111, 2131, or 486"
            })
            continue

        verified_count += 1

    summary_str = f"{verified_count}/{total_rows} rows verified against source"

    return ProvenanceResponse(
        status="verified" if len(failing_records) == 0 else "failed",
        holdout_file=str(holdout_file),
        source_file="data/raw/January2015toNovember2025.csv",
        total_rows=total_rows,
        verified_count=verified_count,
        summary=summary_str,
        failing_records=failing_records,
    )
