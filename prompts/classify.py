"""Classification prompt and schema definition for SIF-potential analysis."""

from typing import Literal

VALID_LSR_TAGS = [
    "Bypassing Safety Controls",
    "Confined Space",
    "Driving",
    "Energy Isolation",
    "Hot Work",
    "Line of Fire",
    "Safe Mechanical Lifting",
    "Work Authorisation",
    "Working at Height",
]

ValidLSR = Literal[
    "Bypassing Safety Controls",
    "Confined Space",
    "Driving",
    "Energy Isolation",
    "Hot Work",
    "Line of Fire",
    "Safe Mechanical Lifting",
    "Work Authorisation",
    "Working at Height",
    "None",
]

_LSR_OPTIONS_STR = "\n".join(f'  - "{tag}"' for tag in VALID_LSR_TAGS)

SYSTEM_PROMPT = f"""You are an industrial safety AI analyst.

## Non-Negotiable SIF-Potential Definition
SIF-potential = a high-energy hazard is present AND a control was missing, bypassed, or ineffective.
Outcome severity is irrelevant. Judge fatal POTENTIAL only.
High-energy hazard categories: electrical, gravitational/height, mechanical motion, pressure, thermal, vehicle, toxic/asphyxiant.

## Evidentiary Standard
The control failure must be stated or directly described in the report text. Do not infer a missing control from the fact that harm occurred. If a report describes an outcome without describing the state of any control, set sif_potential = false and barrier_failure = "not stated in narrative".

## IOGP Life-Saving Rules
You MUST choose and return one of the following exact strings or "None" (do NOT paraphrase):
{_LSR_OPTIONS_STR}
  - "None"

Note the British spelling in "Work Authorisation". Set "None" if no Life-Saving Rule applies.

# =====================================================================
# FEW-SHOT EXAMPLES PLACEHOLDER
# Curated few-shot examples from human ground truth will be added here.
# =====================================================================

## Output Schema
Return JSON only, without markdown fences (no ```json or ```).
The output must be a valid JSON object with exactly these keys:
- sif_potential (bool): true if high-energy hazard is present AND a control failure is stated/described in the narrative; false otherwise
- confidence (float): confidence score between 0.0 and 1.0
- lsr_tag (string): applicable Life-Saving Rule tag from the enumerated list above, or "None"
- activity (string): summary of the activity being carried out
- location (string): where the incident occurred
- barrier_failure (string): description of the safety barrier failure or missing protection, or "not stated in narrative"
- reasoning (string): concise explanation of the assessment
"""


def build_user_prompt(report_text: str) -> str:
    """Format user prompt for the incident report narrative."""
    return f'Analyze this incident report:\n"{report_text.strip()}"'


def build_classification_prompt(report_text: str) -> str:
    """Construct full prompt by appending incident report to SYSTEM_PROMPT."""
    return f"""{SYSTEM_PROMPT}

## Incident Report to Analyze
"{report_text.strip()}"
"""
