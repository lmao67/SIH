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


def verify_narrative_match(xlsx_narr: str, csv_narr: str) -> bool:
    """Check character-for-character equality.

    Accounts for the standard OOXML / openpyxl behavior where carriage returns (\r)
    in XML text nodes are decoded as line feeds (\n), transforming CRLF (\r\n) to (\n\n) or (\n).
    """
    if xlsx_narr == csv_narr:
        return True
    if xlsx_narr.replace("\n\n", "\r\n") == csv_narr:
        return True
    if xlsx_narr.replace("\r\n", "\n").replace("\r", "\n") == csv_narr.replace("\r\n", "\n").replace("\r", "\n"):
        return True
    return False


def verify_provenance(xlsx_path: Path, csv_path: Path) -> bool:
    print("=" * 70)
    print("OSHA Holdout Provenance Verifier")
    print("=" * 70)

    if not xlsx_path.exists():
        print(f"ERROR: Holdout file not found at: {xlsx_path}", file=sys.stderr)
        return False

    if not csv_path.exists():
        print(f"ERROR: Raw CSV source file not found at: {csv_path}", file=sys.stderr)
        return False

    print(f"[1] Loading holdout workbook: {xlsx_path.name}")
    df_xlsx = pd.read_excel(xlsx_path)
    total_rows = len(df_xlsx)
    print(f"    Holdout rows: {total_rows}")

    print(f"[2] Loading raw source CSV: {csv_path.name}")
    df_csv = pd.read_csv(csv_path, low_memory=False)
    print(f"    Raw source rows: {len(df_csv):,}")

    # Determine column names in holdout xlsx
    source_id_col = next((c for c in ["source_id", "source id", "ID", "id"] if c in df_xlsx.columns), None)
    narrative_col = next((c for c in ["Final Narrative", "narrative", "FinalNarrative"] if c in df_xlsx.columns), None)
    naics_col = next((c for c in ["Primary NAICS", "naics", "PrimaryNAICS", "Site NAICS"] if c in df_xlsx.columns), None)

    if not source_id_col:
        print(f"ERROR: Could not find a source_id column in {xlsx_path.name}", file=sys.stderr)
        return False

    if not narrative_col:
        print(f"ERROR: Could not find a narrative column in {xlsx_path.name}", file=sys.stderr)
        return False

    if not naics_col:
        print(f"ERROR: Could not find a Primary NAICS column in {xlsx_path.name}", file=sys.stderr)
        return False

    # Index raw CSV on ID for O(1) lookup
    csv_map = df_csv.set_index("ID")

    print(f"[3] Verifying {total_rows} rows against source data...")
    failing_records = []
    verified_count = 0

    valid_naics_prefixes = ("2111", "2131", "486")

    for idx, row in df_xlsx.iterrows():
        sid = row[source_id_col]
        row_id = row.get("id", idx + 1)

        # 1. Lookup source_id in CSV
        if sid not in csv_map.index:
            failing_records.append({
                "row_id": row_id,
                "source_id": sid,
                "reason": f"source_id {sid} not found in raw CSV ID column"
            })
            continue

        csv_row = csv_map.loc[sid]

        # 2. Check narrative character-for-character
        xlsx_narr = str(row[narrative_col])
        csv_narr = str(csv_row["Final Narrative"])

        narr_match = verify_narrative_match(xlsx_narr, csv_narr)
        if not narr_match:
            failing_records.append({
                "row_id": row_id,
                "source_id": sid,
                "reason": (
                    f"Narrative character mismatch (holdout len: {len(xlsx_narr)}, "
                    f"source len: {len(csv_narr)})"
                )
            })
            continue

        # 3. Check Primary NAICS starts with 2111, 2131, or 486
        raw_naics = str(row[naics_col]).strip().replace(".0", "")
        if not raw_naics.startswith(valid_naics_prefixes):
            failing_records.append({
                "row_id": row_id,
                "source_id": sid,
                "reason": f"Primary NAICS '{raw_naics}' does not start with 2111, 2131, or 486"
            })
            continue

        verified_count += 1

    print("-" * 70)
    # Required summary line
    summary_line = f"{verified_count}/{total_rows} rows verified against source"
    print(summary_line)

    if failing_records:
        print("\n[!] FAILING ROWS:")
        for fail in failing_records:
            print(f"  - Row {fail['row_id']} (source_id: {fail['source_id']}): {fail['reason']}")
        print("=" * 70)
        return False
    else:
        print("\n[+] All rows trace back to raw source CSV with exact narrative and valid NAICS!")
        print("=" * 70)
        return True


def main():
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
    else:
        target_path = Path(__file__).resolve().parent.parent / "data" / "osha_holdout_unlabeled.xlsx"

    csv_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "January2015toNovember2025.csv"

    success = verify_provenance(target_path, csv_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
