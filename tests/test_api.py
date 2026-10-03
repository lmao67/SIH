import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Route test reports to separate store so fixtures never land in the production dataset
TEST_REPORTS_FILE = PROJECT_ROOT / "data" / "test_reports.json"
os.environ["REPORTS_FILE"] = str(TEST_REPORTS_FILE)

from app import main as app_main
app_main.REPORTS_FILE = TEST_REPORTS_FILE

from fastapi.testclient import TestClient
from app.main import app, CACHE_FILE, call_gemini_raw

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_test_reports_store():
    """Initialize isolated test_reports.json and clean up after test suite."""
    app_main.REPORTS_FILE = TEST_REPORTS_FILE
    TEST_REPORTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TEST_REPORTS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
    yield
    if TEST_REPORTS_FILE.exists():
        try:
            TEST_REPORTS_FILE.unlink()
        except Exception:
            pass


def test_valid_report():
    """Test standard high-energy hazard with a missing/bypassed barrier."""
    payload = {
        "report_text": "Contractor observed working at approximately 15 feet on the pipeline rack without fall protection. Harness was on site but not worn.",
        "site": "Permian Basin Facility A"
    }
    response = client.post("/classify", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["sif_potential"] is True
    assert data["lsr_tag"] == "Working at Height"
    assert "harness" in data["barrier_failure"].lower() or "fall" in data["barrier_failure"].lower()
    assert data["site"] == "Permian Basin Facility A"
    assert data["confidence"] > 0.5


def test_empty_string_report():
    """Test empty string report handled gracefully with status 'needs_review' and no crash."""
    payload = {
        "report_text": "   ",
        "site": "Refinery Alpha"
    }
    response = client.post("/classify", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "needs_review"
    assert data["sif_potential"] is False
    assert data["barrier_failure"] == "not stated in narrative"
    assert data["lsr_tag"] == "None"


def test_5000_word_report():
    """Test that an extremely long 5,000-word narrative does not crash the model or parser."""
    # Base narrative describing an electrical LOTO failure surrounded by extensive industrial operational filler
    base_incident = (
        "During maintenance on the high-voltage 13.8kV main transformer substation, "
        "an electrician began servicing the circuit breaker with the interlock removed and no LOTO applied. "
        "The upstream disconnect remained energized while work proceeded without safety isolation. "
    )
    padding = "Routine site logs: ambient temperature 72F, daily inspection logs verified, perimeter fencing intact. "
    # Build approximately 5,000 words
    words_per_pad = len(padding.split())
    reps = (5000 - len(base_incident.split())) // words_per_pad
    long_narrative = base_incident + (padding * reps)

    assert len(long_narrative.split()) >= 4500

    payload = {
        "report_text": long_narrative,
        "site": "Mega Complex Substation"
    }
    response = client.post("/classify", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ["success", "needs_review"]
    assert "sif_potential" in data
    assert "lsr_tag" in data
    assert "activity" in data
    assert "reasoning" in data


def test_broken_english_report():
    """Test report written in non-native or broken English."""
    payload = {
        "report_text": "guy worker climb on high rig derrick maybe 20 meter, no tie off rope harness left on truck, heavy wind shake pole, worker almost drop",
        "site": "Rig 104"
    }
    response = client.post("/classify", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["sif_potential"] is True
    assert data["lsr_tag"] == "Working at Height"
    assert data["confidence"] >= 0.5


def test_no_hazard_report():
    """Test benign report with zero high energy and no barrier failure."""
    payload = {
        "report_text": "Employee was seated in the administration office writing meeting minutes. Employee received a slight paper cut on the left index finger, rinsed it under the office sink, applied a band-aid from the first aid kit, and resumed typing.",
        "site": "Headquarters Office"
    }
    response = client.post("/classify", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["sif_potential"] is False
    assert data["lsr_tag"] == "None"


def test_cache_hit_asserting_api_not_called_twice():
    """Assert that calling the API with identical text hits cache and does not invoke Gemini."""
    unique_text = f"Special unit test narrative for caching verification timestamp {os.urandom(8).hex()}: Operator isolated live 480V valve with lock and tag."
    payload = {
        "report_text": unique_text,
        "site": "Cache Testing Station"
    }

    mock_llm_json = json.dumps({
        "sif_potential": True,
        "confidence": 0.95,
        "lsr_tag": "Energy Isolation",
        "activity": "Valve maintenance and electrical isolation",
        "location": "Substation",
        "barrier_failure": "Lock removed without proper verification",
        "reasoning": "Live 480V electrical hazard present without verified isolation controls"
    })

    # First call: should call the LLM once and save to cache
    with patch("app.main.call_gemini_raw", return_value=mock_llm_json) as mock_first:
        res1 = client.post("/classify", json=payload)
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["status"] == "success"
        assert data1["cached"] is False
        assert mock_first.call_count == 1

    # Second call: mock call_gemini_raw to guarantee it is NOT called
    with patch("app.main.call_gemini_raw") as mock_second:
        res2 = client.post("/classify", json=payload)
        assert res2.status_code == 200
        data2 = res2.json()

        # Ensure mock was never called
        mock_second.assert_not_called()

        assert data2["cached"] is True
        assert data2["sha256"] == data1["sha256"]
        assert data2["sif_potential"] == data1["sif_potential"]
        assert data2["lsr_tag"] == data1["lsr_tag"]


def test_get_reports_filtering():
    """Test retrieving stored reports with site and sif_potential filters."""
    # Submit one True and one False
    client.post("/classify", json={"report_text": "Crane load suspended above active pathway with broken sling", "site": "Site Alpha"})
    client.post("/classify", json={"report_text": "Worker filled water cooler in canteen", "site": "Site Beta"})

    # Filter site Alpha
    res = client.get("/reports?site=Alpha")
    assert res.status_code == 200
    reports = res.json()
    assert len(reports) >= 1
    for r in reports:
        assert "alpha" in (r["site"] or "").lower()

    # Filter sif_potential = False
    res_false = client.get("/reports?sif_potential=false")
    assert res_false.status_code == 200
    reports_false = res_false.json()
    assert len(reports_false) >= 1
    for r in reports_false:
        assert r["sif_potential"] is False


def test_provenance_endpoint():
    """Test GET /provenance returns read-only verification summary."""
    response = client.get("/provenance")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "verified"
    assert data["total_rows"] == 150
    assert data["verified_count"] == 150
    assert "150/150 rows verified against source" in data["summary"]
    assert len(data["failing_records"]) == 0


def test_batch_classify_endpoint(tmp_path):
    """Test POST /classify/batch with rate limiting and checkpointing."""
    import pandas as pd
    test_file = tmp_path / "test_batch.csv"
    checkpoint_file = tmp_path / "checkpoint.json"

    df = pd.DataFrame({
        "id": [1, 2, 3],
        "incident_narrative": [
            "Worker entered permit-required confined vessel without atmospheric testing or blower ventilation.",
            "Janitor washed floor with soap and left warning sign out.",
            "Worker fell 12 feet from drilling scaffold without safety harness tied off."
        ],
        "location": ["Unit 1", "Unit 2", "Unit 3"]
    })
    df.to_csv(test_file, index=False)

    payload = {
        "file_path": str(test_file),
        "text_column": "incident_narrative",
        "site_column": "location",
        "checkpoint_path": str(checkpoint_file),
        "delay_seconds": 0.01
    }

    response = client.post("/classify/batch", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "completed"
    assert data["total_rows"] == 3
    assert data["classified_count"] == 3
    assert checkpoint_file.exists()

    with open(checkpoint_file, "r") as f:
        cp_data = json.load(f)
    assert "results" in cp_data
    assert len(cp_data["results"]) == 3


def test_quota_error_exits_code_1(capsys):
    """Test that any quota error (429/ResourceExhausted) on gemini-3.8-flash prints error and exits with code 1."""
    with patch("google.generativeai.GenerativeModel.generate_content", side_effect=Exception("429 ResourceExhausted: Quota exceeded for gemini-3.8-flash")):
        with pytest.raises(SystemExit) as exc_info:
            call_gemini_raw("test prompt")
        assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "FATAL Quota Error" in captured.err or "429" in captured.err

