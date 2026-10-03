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
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter


def build_fatality_sheet():
    raw_xlsx = Path(__file__).resolve().parent.parent / "data" / "raw" / "data.xlsx"
    output_xlsx = Path(__file__).resolve().parent.parent / "data" / "fatality_holdout_unlabeled.xlsx"

    print("=" * 70)
    print("Building OSHA Fatality Holdout Labeling Workbook")
    print("=" * 70)

    if not raw_xlsx.exists():
        print(f"ERROR: Raw data file not found: {raw_xlsx}", file=sys.stderr)
        sys.exit(1)

    # 1. Load data.xlsx
    # Check if skiprows=2 is required or if row 1 already contains the headers
    print(f"[1] Loading {raw_xlsx.name}...")
    df = None
    try:
        df_skip = pd.read_excel(raw_xlsx, skiprows=2)
        if "Site NAICS" in df_skip.columns:
            df = df_skip
            print("    Loaded with skiprows=2 (header on row 3).")
        else:
            print("    Row 3 contains data rows, loading row 1 as header...")
            df = pd.read_excel(raw_xlsx)
    except Exception:
        df = pd.read_excel(raw_xlsx)

    initial_count = len(df)
    print(f"    Initial raw rows: {initial_count:,}")

    # 2. DROP and never write forbidden columns
    # Forbidden: Establishment Name, Site City, Site County, Victim Name (Age), and opening-conference-date
    forbidden_cols = [
        "Establishment Name",
        "Site City",
        "Site County",
        "Victim Name (Age)",
        "Opening Conference Date",
    ]
    # Match case-insensitively or partial match for opening conference date
    cols_to_drop = []
    for c in df.columns:
        c_str = str(c).strip()
        if c_str in forbidden_cols or "opening" in c_str.lower() or "victim" in c_str.lower():
            cols_to_drop.append(c)

    df = df.drop(columns=cols_to_drop)
    print(f"[2] Dropped sensitive/unneeded columns: {', '.join(str(c) for c in cols_to_drop)}")

    # 3. Filter Site NAICS (cast to string, strip any trailing .0) to values starting with 2111, 2131, or 486
    # Expected to yield ~428 rows
    naics_raw = df["Site NAICS"].dropna().astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    naics_mask = naics_raw.str.startswith(("2111", "2131", "486"))
    df_naics = df.loc[naics_mask.index[naics_mask]].copy()
    df_naics["naics"] = naics_raw.loc[naics_mask.index[naics_mask]]
    naics_surviving = len(df_naics)
    print(f"[3] Filtered Site NAICS (starts with 2111, 2131, 486):")
    print(f"    Surviving rows: {naics_surviving:,} (yielded ~{naics_surviving} rows)")

    # 4. Keep only rows with Event Date in 2015 or later
    df_naics["event_date_dt"] = pd.to_datetime(df_naics["Event Date"], errors="coerce")
    date_mask = df_naics["event_date_dt"].dt.year >= 2015
    df_2015 = df_naics[date_mask].copy()
    date_surviving = len(df_2015)
    print(f"[4] Filtered Event Date >= 2015 (matching SIR data era):")
    print(f"    Surviving rows: {date_surviving:,} (retained {date_surviving / naics_surviving * 100:.2f}%)")

    # 5. Stratified sampling across NAICS prefix so drilling (2111) and support activities (2131) are represented
    df_2015["naics_prefix"] = df_2015["naics"].str.extract(r"^(2111|2131|486)")
    prefix_counts = df_2015["naics_prefix"].value_counts()
    print(f"[5] NAICS prefix breakdown in 2015+ pool:")
    for prefix, cnt in prefix_counts.items():
        print(f"    - Prefix {prefix}: {cnt} rows")

    # Proportional allocation ensuring at least 1 sample from each group
    target_sample_size = 30
    proportions = prefix_counts / len(df_2015)
    allocations = (proportions * target_sample_size).round().astype(int).clip(lower=1)
    diff = target_sample_size - allocations.sum()
    if diff != 0:
        allocations[prefix_counts.idxmax()] += diff

    print(f"    Allocated sample distribution (total {target_sample_size}):")
    for prefix, alloc in allocations.items():
        print(f"    - Prefix {prefix}: {alloc} rows")

    sampled_subsets = []
    for prefix, n_alloc in allocations.items():
        grp_df = df_2015[df_2015["naics_prefix"] == prefix]
        sampled_subsets.append(grp_df.sample(n=n_alloc, random_state=42))

    sample_df = pd.concat(sampled_subsets).sample(frac=1.0, random_state=42).reset_index(drop=True)
    print(f"    Sampled {len(sample_df)} rows with random_state=42")

    # 6. Build the final output dataframe
    # Exact column order:
    # id (starting at 151), source (="fatality"), inspection_nr, event_date, naics, state, imis_url, narrative,
    # severity_bucket (="fatality"), energy_type, barrier_failure, sif_potential, lsr_tag, labeled_by, notes
    out_df = pd.DataFrame()
    out_df["id"] = range(151, 151 + len(sample_df))
    out_df["source"] = "fatality"

    # Inspection number formatted as integer string
    inspection_nrs = sample_df["Inspection #"].fillna(0).astype(int).astype(str)
    out_df["inspection_nr"] = inspection_nrs

    # Formatted Event Date (YYYY-MM-DD)
    out_df["event_date"] = sample_df["event_date_dt"].dt.strftime("%Y-%m-%d")

    out_df["naics"] = sample_df["naics"]
    out_df["state"] = sample_df["Site State"].fillna("").astype(str)

    # imis_url
    base_url = "https://www.osha.gov/ords/imis/establishment.inspection_detail?id="
    out_df["imis_url"] = inspection_nrs.apply(lambda nr: f"{base_url}{nr}")

    # narrative (blank for labelers)
    out_df["narrative"] = ""

    out_df["severity_bucket"] = "fatality"

    # Blank labeling columns
    blank_cols = ["energy_type", "barrier_failure", "sif_potential", "lsr_tag", "labeled_by", "notes"]
    for c in blank_cols:
        out_df[c] = ""

    # Security check: ensure none of the forbidden columns leaked
    for forbidden in forbidden_cols:
        assert forbidden not in out_df.columns, f"Security check failed: {forbidden} found in output!"

    # 7. Write to Excel with formatting & Data Validations
    print(f"[6] Writing to {output_xlsx.name} with formatting & validations...")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Fatality_Holdout_Unlabeled"

    headers = list(out_df.columns)
    ws.append(headers)

    for row in out_df.itertuples(index=False):
        ws.append(list(row))

    # Freeze top row
    ws.freeze_panes = "A2"

    # Styling
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # Navy blue
    data_font = Font(name="Calibri", size=10)
    link_font = Font(name="Calibri", size=10, color="1D4ED8", underline="single")
    border_side = Side(border_style="thin", color="E2E8F0")
    cell_border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)

    # Style header row
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = cell_border

    ws.row_dimensions[1].height = 28

    # Style data rows
    for row_idx in range(2, len(out_df) + 2):
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = data_font
            cell.border = cell_border

            header_name = headers[col_idx - 1]
            if header_name == "narrative":
                cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            elif header_name in ["id", "source", "inspection_nr", "event_date", "naics", "state", "severity_bucket", "sif_potential"]:
                cell.alignment = Alignment(horizontal="center", vertical="top")
            elif header_name == "imis_url":
                cell.alignment = Alignment(horizontal="left", vertical="top")
                cell.font = link_font
            else:
                cell.alignment = Alignment(horizontal="left", vertical="top")

    # Column widths
    col_widths = {
        "id": 8,
        "source": 12,
        "inspection_nr": 16,
        "event_date": 14,
        "naics": 12,
        "state": 8,
        "imis_url": 45,
        "narrative": 80,  # 80 width with wrap text
        "severity_bucket": 16,
        "energy_type": 16,
        "barrier_failure": 26,
        "sif_potential": 14,
        "lsr_tag": 26,
        "labeled_by": 14,
        "notes": 30,
    }

    for col_idx, col_name in enumerate(headers, start=1):
        col_letter = get_column_letter(col_idx)
        width = col_widths.get(col_name, 20)
        ws.column_dimensions[col_letter].width = width

    # 8. Data Validation Dropdowns
    max_row = len(out_df) + 1

    # 8a. sif_potential: TRUE, FALSE
    sif_col_letter = get_column_letter(headers.index("sif_potential") + 1)
    dv_sif = DataValidation(type="list", formula1='"TRUE,FALSE"', allow_blank=True)
    dv_sif.error = "Please select TRUE or FALSE"
    dv_sif.errorTitle = "Invalid Selection"
    ws.add_data_validation(dv_sif)
    dv_sif.add(f"{sif_col_letter}2:{sif_col_letter}{max_row}")

    # 8b. lsr_tag: 9 IOGP rules + "None"
    iogp_rules = [
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
    lsr_options = ",".join(iogp_rules)
    lsr_col_letter = get_column_letter(headers.index("lsr_tag") + 1)
    dv_lsr = DataValidation(type="list", formula1=f'"{lsr_options}"', allow_blank=True)
    dv_lsr.error = "Please select a valid Life-Saving Rule or None"
    dv_lsr.errorTitle = "Invalid LSR"
    ws.add_data_validation(dv_lsr)
    dv_lsr.add(f"{lsr_col_letter}2:{lsr_col_letter}{max_row}")

    # 8c. energy_type: electrical, height, mechanical, pressure, thermal, vehicle, toxic, none
    energy_types = "electrical,height,mechanical,pressure,thermal,vehicle,toxic,none"
    energy_col_letter = get_column_letter(headers.index("energy_type") + 1)
    dv_energy = DataValidation(type="list", formula1=f'"{energy_types}"', allow_blank=True)
    dv_energy.error = "Please select a valid energy category"
    dv_energy.errorTitle = "Invalid Energy Type"
    ws.add_data_validation(dv_energy)
    dv_energy.add(f"{energy_col_letter}2:{energy_col_letter}{max_row}")

    wb.save(output_xlsx)
    print(f"\n[+] SUCCESS: Saved fatality labeling workbook to {output_xlsx}")
    print(f"    Columns ({len(headers)}): {', '.join(headers)}")
    print(f"    Rows: {len(out_df)} (IDs {out_df['id'].min()} - {out_df['id'].max()})")


if __name__ == "__main__":
    build_fatality_sheet()
