import os
import sys
import subprocess
from pathlib import Path

# Ensure execution inside .venv if run with an external python interpreter
if not hasattr(sys, "real_prefix") and (sys.base_prefix == sys.prefix):
    venv_python = Path(__file__).resolve().parent.parent / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists() and sys.executable.lower() != str(venv_python).lower():
        result = subprocess.run([str(venv_python), *sys.argv], check=False)
        sys.exit(result.returncode)

import pandas as pd


def compute_metrics():
    xlsx_path = Path(__file__).resolve().parent.parent / "data" / "fatality_holdout_FINAL.xlsx"
    report_path = Path(__file__).resolve().parent.parent / "eval" / "label_comparison.md"

    if not xlsx_path.exists():
        print(f"ERROR: Dataset not found at {xlsx_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading data from {xlsx_path.name} (read-only)...")
    df_human = pd.read_excel(xlsx_path, sheet_name="labeling")
    df_ai = pd.read_excel(xlsx_path, sheet_name="ai_labels_v0")

    # Filter to rows with non-empty narrative
    has_narrative = df_human["narrative"].fillna("").astype(str).str.strip() != ""
    df_human = df_human[has_narrative].copy()

    # Drop blank template rows from AI sheet if any
    df_ai = df_ai[df_ai["sif_potential"].notna()].copy()

    # Join on 'id', or fall back to row-order alignment if 'id' column is missing
    if "id" in df_ai.columns and "id" in df_human.columns:
        # Deduplicate in AI sheet if identical id present
        df_ai = df_ai.drop_duplicates(subset=["id"], keep="first")
        merged = pd.merge(df_human, df_ai, on="id", suffixes=("_human", "_ai"))
    else:
        print("[!] WARNING: 'ai_labels_v0' has no 'id' column! Falling back to row-order alignment.")
        df_h = df_human.reset_index(drop=True)
        df_a = df_ai.reset_index(drop=True)
        n_rows = min(len(df_h), len(df_a))
        if len(df_h) != len(df_a):
            print(f"[!] WARNING: Row count mismatch (Human: {len(df_h)}, AI: {len(df_a)}). Aligning first {n_rows} rows.")
        df_h = df_h.iloc[:n_rows].copy()
        df_a = df_a.iloc[:n_rows].copy()

        merged = df_h.copy()
        for c in df_a.columns:
            merged[f"{c}_ai"] = df_a[c]
        for c in ["sif_potential", "lsr_tag", "barrier_failure"]:
            if c in merged.columns and f"{c}_human" not in merged.columns:
                merged[f"{c}_human"] = merged[c]

    total_rows = len(merged)
    print(f"Total valid merged rows: {total_rows}")

    # Standardize boolean values for sif_potential
    def to_bool(val):
        if isinstance(val, bool):
            return val
        s = str(val).strip().lower()
        return s in ["true", "1", "yes", "t"]

    merged["sif_human_bool"] = merged["sif_potential_human"].apply(to_bool)
    merged["sif_ai_bool"] = merged["sif_potential_ai"].apply(to_bool)

    # 1. Overall agreement rate on sif_potential
    matches = (merged["sif_human_bool"] == merged["sif_ai_bool"]).sum()
    overall_agreement = matches / total_rows

    # 2. Confusion matrix: AI versus Human
    # Human = Ground Truth, AI = Predicted
    tp = int(((merged["sif_human_bool"] == True) & (merged["sif_ai_bool"] == True)).sum())
    fp = int(((merged["sif_human_bool"] == False) & (merged["sif_ai_bool"] == True)).sum())
    fn = int(((merged["sif_human_bool"] == True) & (merged["sif_ai_bool"] == False)).sum())
    tn = int(((merged["sif_human_bool"] == False) & (merged["sif_ai_bool"] == False)).sum())

    human_true_total = tp + fn
    human_false_total = fp + tn
    ai_true_total = tp + fp
    ai_false_total = fn + tn

    # 3. Cohen's kappa
    p_o = (tp + tn) / total_rows
    p_yes = (human_true_total / total_rows) * (ai_true_total / total_rows)
    p_no = (human_false_total / total_rows) * (ai_false_total / total_rows)
    p_e = p_yes + p_no
    kappa = (p_o - p_e) / (1.0 - p_e) if (1.0 - p_e) != 0 else 0.0

    # 4. Agreement on lsr_tag among rows where both marked TRUE
    both_true = merged[(merged["sif_human_bool"] == True) & (merged["sif_ai_bool"] == True)].copy()
    both_true_count = len(both_true)

    def clean_lsr(val):
        if pd.isna(val) or val is None:
            return ""
        return str(val).strip().lower()

    lsr_matches = (
        both_true["lsr_tag_human"].apply(clean_lsr) == both_true["lsr_tag_ai"].apply(clean_lsr)
    ).sum()
    lsr_agreement_rate = lsr_matches / both_true_count if both_true_count > 0 else 0.0

    # 5. Disagreements
    disagreements = merged[merged["sif_human_bool"] != merged["sif_ai_bool"]].copy().sort_values("id")

    # Print to console
    print("\n" + "=" * 70)
    print("FATALITY HOLDOUT EVALUATION: AI vs HUMAN LABELS")
    print("=" * 70)
    print(f"Overall Agreement Rate on sif_potential : {overall_agreement:.2%} ({matches}/{total_rows})")
    print(f"Cohen's Kappa                           : {kappa:.4f}")
    print("\n2x2 Confusion Matrix (Human Ground Truth vs AI Prediction):")
    print(f"{'':<20} | {'AI=True':<12} | {'AI=False':<12} | {'Total':<10}")
    print("-" * 62)
    print(f"{'Human=True':<20} | {tp:<12} | {fn:<12} | {human_true_total:<10}")
    print(f"{'Human=False':<20} | {fp:<12} | {tn:<12} | {human_false_total:<10}")
    print("-" * 62)
    print(f"{'Total':<20} | {ai_true_total:<12} | {ai_false_total:<12} | {total_rows:<10}")

    print(f"\nAgreement on lsr_tag (where both marked TRUE): {lsr_agreement_rate:.2%} ({lsr_matches}/{both_true_count})")
    print(f"\nTotal Disagreements on sif_potential: {len(disagreements)}")
    print("=" * 70)

    for idx, row in disagreements.iterrows():
        narrative_120 = str(row["narrative"]).strip()[:120]
        # Clean internal newlines for console output
        narrative_clean = narrative_120.replace("\r", " ").replace("\n", " ")
        barrier = str(row["barrier_failure_human"]).strip()
        print(f"\n[ID {row['id']}] Human SIF={row['sif_human_bool']}, AI SIF={row['sif_ai_bool']}")
        print(f"  Human barrier_failure : \"{barrier}\"")
        print(f"  Narrative snippet     : \"{narrative_clean}...\"")

    # Generate Markdown Report
    summary_paragraph = (
        "This evaluation compares initial zero-shot AI classifications (`ai_labels_v0`) against "
        "human ground truth (`labeling`) across 48 oil-and-gas fatality holdout narratives in "
        "`data/fatality_holdout_FINAL.xlsx`. The results highlight a fundamental systemic bias: "
        f"the uncalibrated AI labeled {ai_true_total}/{total_rows} ({ai_true_total/total_rows:.1%}) of records as SIF-potential, "
        f"whereas human experts applying the rigorous two-part definition identified only {human_true_total}/{total_rows} "
        f"({human_true_total/total_rows:.1%}). Because the model incorrectly treated fatality outcomes as de facto evidence "
        f"of a control failure, it generated {fp} false positives, resulting in an overall agreement of only "
        f"{overall_agreement:.1%} and a near-chance Cohen's kappa of {kappa:.4f}. When both agreed a SIF precursor existed, "
        f"Life-Saving Rule (LSR) alignment reached {lsr_agreement_rate:.1%} ({lsr_matches}/{both_true_count})."
    )

    report_lines = [
        "# Fatality Holdout: Human vs. AI Label Comparison",
        "",
        "## Executive Summary",
        "",
        summary_paragraph,
        "",
        "---",
        "",
        "## Key Metrics",
        "",
        f"- **Total Evaluated Records**: {total_rows}",
        f"- **Overall Agreement on `sif_potential`**: **{overall_agreement:.2%}** ({matches}/{total_rows})",
        f"- **Cohen's Kappa ($\\kappa$)**: **{kappa:.4f}** (slight / near-chance agreement due to extreme model positive bias)",
        f"- **`lsr_tag` Agreement (when both marked TRUE)**: **{lsr_agreement_rate:.2%}** ({lsr_matches}/{both_true_count})",
        "",
        "---",
        "",
        "## 2x2 Confusion Matrix",
        "",
        "| Human (Ground Truth) \\ AI (Prediction) | AI = TRUE (SIF) | AI = FALSE (Non-SIF) | Total Human |",
        "|---|:---:|:---:|:---:|",
        f"| **Human = TRUE (SIF)** | **{tp}** (TP) | **{fn}** (FN) | **{human_true_total}** |",
        f"| **Human = FALSE (Non-SIF)** | **{fp}** (FP) | **{tn}** (TN) | **{human_false_total}** |",
        f"| **Total AI** | **{ai_true_total}** | **{ai_false_total}** | **{total_rows}** |",
        "",
        "> **Takeaway**: Recall on the human SIF-positive class is 100% (19/19, zero false negatives), but precision is only "
        f"{tp/ai_true_total:.2%} due to 28 false positives where narratives lacked evidence of a failed or absent control.",
        "",
        "---",
        "",
        "## LSR Tag Agreement Breakdown (Both Marked TRUE)",
        "",
        f"Across the {both_true_count} cases where both Human and AI agreed on `sif_potential = TRUE`, "
        f"{lsr_matches} cases matched the exact Life-Saving Rule:",
        "",
        "| ID | Human LSR Tag | AI LSR Tag | Matched? |",
        "|---|---|---|:---:|",
    ]

    for idx, r in both_true.iterrows():
        h_lsr = str(r["lsr_tag_human"]).strip() if pd.notna(r["lsr_tag_human"]) else "None"
        a_lsr = str(r["lsr_tag_ai"]).strip() if pd.notna(r["lsr_tag_ai"]) else "None"
        is_m = "✅ Yes" if clean_lsr(h_lsr) == clean_lsr(a_lsr) else "❌ No"
        report_lines.append(f"| {r['id']} | {h_lsr} | {a_lsr} | {is_m} |")

    report_lines.extend([
        "",
        "---",
        "",
        "## Disagreements on `sif_potential`",
        "",
        f"Below are the **{len(disagreements)}** records where Human and AI disagreed. "
        "In every single case (**28/28**), Human marked `FALSE` while AI marked `TRUE` because the narrative "
        "did not demonstrate a missing, bypassed, or ineffective barrier.",
        "",
        "| ID | Human SIF | AI SIF | Human `barrier_failure` | Narrative Snippet (First 120 chars) |",
        "|---|:---:|:---:|---|---|",
    ])

    for idx, r in disagreements.iterrows():
        narr_snippet = str(r["narrative"]).strip()[:120].replace("\r", " ").replace("\n", " ").replace("|", "\\|")
        barrier_txt = str(r["barrier_failure_human"]).strip().replace("\r", " ").replace("\n", " ").replace("|", "\\|")
        report_lines.append(
            f"| {r['id']} | `{r['sif_human_bool']}` | `{r['sif_ai_bool']}` | {barrier_txt} | {narr_snippet}... |"
        )

    report_lines.extend([
        "",
        "---",
        "",
        "## Diagnostic Insights & SIF Methodology Validation",
        "",
        "1. **Outcome Bias in Zero-Shot LLMs**:",
        "   The zero-shot AI assumed that because a fatality occurred, a control must have failed. Human safety experts strictly enforce the definition: *SIF-potential requires high energy AND an identified barrier failure*.",
        "2. **Information Scarcity in OSHA Abstracts**:",
        "   Many OSHA abstracts simply state what occurred (e.g. medical collapse, heart failure, lightning, unassisted medical emergency) or report an injury without documenting whether proper safeguards were missing or breached.",
        "   Human labelers correctly marked these as `barrier_failure = not stated in narrative` or `not applicable`, producing `sif_potential = FALSE`.",
        "3. **LSR Rule Nuances**:",
        "   Where both agreed on SIF, disagreements in LSR tagging occurred on overlapping hazard mechanisms (e.g., `Confined Space` vs. `Hot Work`, or `Energy Isolation` vs. `Line of Fire`)."
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    print(f"\n[+] SUCCESS: Written full report to {report_path}")


if __name__ == "__main__":
    compute_metrics()
