import os
import sys
import json
import re
from pathlib import Path
from typing import Literal

# Ensure execution inside .venv if run with an external python interpreter
if not hasattr(sys, "real_prefix") and (sys.base_prefix == sys.prefix):
    venv_python = Path(__file__).resolve().parent.parent / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists() and sys.executable.lower() != str(venv_python).lower():
        import subprocess
        result = subprocess.run([str(venv_python), *sys.argv], check=False)
        sys.exit(result.returncode)

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import dotenv
import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError

from prompts.classify import SYSTEM_PROMPT, VALID_LSR_TAGS, ValidLSR


class SIFClassification(BaseModel):
    sif_potential: bool = Field(
        description="True if high-energy hazard is present AND control is missing, bypassed, or ineffective."
    )
    confidence: float = Field(ge=0.0, le=1.0)
    lsr_tag: ValidLSR
    activity: str
    location: str
    barrier_failure: str
    reasoning: str


def list_available_models() -> list[str]:
    """Helper function to query and list models supporting generateContent from the Gemini API.

    Can be called manually if needed to discover new model IDs.
    """
    print("Listing available models from Gemini API...")
    models = []
    try:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                models.append(m.name.replace("models/", ""))
        print(f"Found {len(models)} models supporting generateContent: {models}")
    except Exception as e:
        print(f"ERROR: Failed to list models: {e}", file=sys.stderr)
    return models


def main():
    print("=" * 60)
    print("Gemini API Smoke Test")
    print("=" * 60)

    # 1. Load environment variables
    env_path = Path(__file__).resolve().parent.parent / ".env"
    dotenv.load_dotenv(dotenv_path=env_path)
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env file.", file=sys.stderr)
        sys.exit(1)

    print("[1] GEMINI_API_KEY successfully loaded from .env")

    # 2. Check google-generativeai version
    version = getattr(genai, "__version__", "unknown")
    print(f"[2] Installed google-generativeai version: {version}")

    genai.configure(api_key=api_key)

    # 3. Use verified model ID (gemini-3.8-flash)
    selected_model_id = "gemini-3.8-flash"
    print(f"[3] Using model ID: {selected_model_id}")

    # 4. Prepare report and prompt
    report = (
        "Contractor observed working at approximately 15 feet on the pipeline rack "
        "without fall protection. Harness was on site but not worn."
    )

    prompt = f"""{SYSTEM_PROMPT}

## Incident Report to Analyze
"{report}"
"""

    generation_config = genai.GenerationConfig(
        temperature=0.1,
        response_mime_type="application/json",
    )

    model = genai.GenerativeModel(
        model_name=selected_model_id,
        generation_config=generation_config,
    )

    print("\n[4] Sending report to Gemini API...")
    print(f"Report: \"{report}\"\n")

    try:
        response = model.generate_content(prompt)
    except Exception as e:
        print(f"ERROR: Generation request failed: {e}", file=sys.stderr)
        sys.exit(1)

    raw_response = response.text
    print("=" * 60)
    print("RAW RESPONSE:")
    print("=" * 60)
    print(raw_response)
    print("=" * 60)

    # 5. Parse JSON
    cleaned_json_text = raw_response.strip()
    if cleaned_json_text.startswith("```"):
        cleaned_json_text = re.sub(r"^```(?:json)?\s*", "", cleaned_json_text, flags=re.IGNORECASE)
        cleaned_json_text = re.sub(r"\s*```$", "", cleaned_json_text)
        cleaned_json_text = cleaned_json_text.strip()

    try:
        parsed_dict = json.loads(cleaned_json_text)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON: {e}", file=sys.stderr)
        print("Cleaned text was:", cleaned_json_text)
        sys.exit(1)

    print("\nPARSED DICT:")
    print("=" * 60)
    print(json.dumps(parsed_dict, indent=2))
    print("=" * 60)

    # 6. Pydantic schema validation as mandated by project rules
    try:
        validated_model = SIFClassification.model_validate(parsed_dict)
        print("\n[+] Pydantic Validation SUCCESS:")
        print(f"    sif_potential : {validated_model.sif_potential}")
        print(f"    confidence    : {validated_model.confidence}")
        print(f"    lsr_tag       : {validated_model.lsr_tag}")
        print(f"    activity      : {validated_model.activity}")
        print(f"    location      : {validated_model.location}")
        print(f"    barrier       : {validated_model.barrier_failure}")
        print(f"    reasoning     : {validated_model.reasoning}")
    except ValidationError as ve:
        print(f"\n[!] WARNING / PYDANTIC VALIDATION ERROR: {ve}", file=sys.stderr)
        sys.exit(1)

    print("\n[+] Verification SUCCESS: All required keys present, properly typed, and lsr_tag matches IOGP standard!")


if __name__ == "__main__":
    main()
