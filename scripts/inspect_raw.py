import os
import sys
from pathlib import Path
import pandas as pd

# Ensure execution inside .venv if run with an external python interpreter
if not hasattr(sys, "real_prefix") and (sys.base_prefix == sys.prefix):
    venv_python = Path(__file__).resolve().parent.parent / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists() and sys.executable.lower() != str(venv_python).lower():
        import subprocess
        result = subprocess.run([str(venv_python), *sys.argv], check=False)
        sys.exit(result.returncode)


def load_file(file_path: Path) -> pd.DataFrame:
    """Load a CSV or Excel file safely, handling common encodings."""
    ext = file_path.suffix.lower()
    if ext == ".csv":
        try:
            return pd.read_csv(file_path, low_memory=False, encoding="utf-8")
        except UnicodeDecodeError:
            return pd.read_csv(file_path, low_memory=False, encoding="latin-1")
    elif ext in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")


def inspect_file(file_path: Path):
    print("=" * 80)
    print(f"FILE: {file_path.name}")
    print("=" * 80)

    try:
        df = load_file(file_path)
    except Exception as e:
        print(f"ERROR: Could not load {file_path.name}: {e}")
        return

    # 1. Filename and row count
    row_count, col_count = df.shape
    print(f"Row count    : {row_count:,}")
    print(f"Column count : {col_count}")
    print("-" * 80)

    # 2. Every column name with its dtype
    print("COLUMNS & DTYPES:")
    for col in df.columns:
        dtype = df[col].dtype
        non_null_count = df[col].notna().sum()
        null_count = row_count - non_null_count
        print(f"  - {col:<35} : {str(dtype):<15} (non-null: {non_null_count:,}, null: {null_count:,})")
    print("-" * 80)

    # 3. For each text column, average character length
    print("TEXT COLUMNS & AVERAGE CHARACTER LENGTH:")
    text_columns = []
    longest_candidates = []

    for col in df.columns:
        # Check if column is object or string type
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            non_null = df[col].dropna()
            if len(non_null) > 0:
                # Convert to string and filter out empty strings
                str_series = non_null.astype(str)
                lengths = str_series.str.len()
                avg_len = lengths.mean()
                max_len = lengths.max()
                text_columns.append(col)
                print(f"  - {col:<35} : avg length = {avg_len:6.1f} chars (max = {max_len:,} chars)")

                # Gather top longest values from this column
                top_idx = lengths.nlargest(3).index
                for idx in top_idx:
                    longest_candidates.append({
                        "col": col,
                        "length": lengths.loc[idx],
                        "text": str_series.loc[idx]
                    })
            else:
                print(f"  - {col:<35} : all null / empty")

    if not text_columns:
        print("  (No text/object columns found)")
    print("-" * 80)

    # 4. The 3 longest text values found anywhere, truncated to 300 chars
    print("3 LONGEST TEXT VALUES FOUND ANYWHERE:")
    if longest_candidates:
        # Sort candidates descending by length
        longest_candidates.sort(key=lambda x: x["length"], reverse=True)
        top_3 = longest_candidates[:3]
        for rank, item in enumerate(top_3, 1):
            col_name = item["col"]
            length = item["length"]
            text_val = item["text"]
            truncated = text_val[:300] + ("..." if len(text_val) > 300 else "")
            # Replace inner newlines for cleaner formatting
            cleaned_snippet = truncated.replace("\r", " ").replace("\n", " ")
            print(f"\n  #{rank} [Column: '{col_name}', Length: {length:,} chars]:")
            print(f"     \"{cleaned_snippet}\"")
    else:
        print("  (No text values found)")
    print("-" * 80)

    # 5. NAICS column check and 10 most common values
    naics_cols = [col for col in df.columns if "naics" in col.lower()]
    if naics_cols:
        for ncol in naics_cols:
            print(f"TOP 10 MOST COMMON VALUES IN NAICS COLUMN '{ncol}':")
            top_naics = df[ncol].value_counts(dropna=False).head(10)
            for val, count in top_naics.items():
                pct = (count / row_count) * 100
                print(f"  - {str(val):<20} : {count:7,} rows ({pct:5.2f}%)")
    else:
        print("NAICS COLUMN: None found matching 'naics' (case-insensitive).")

    print("\n" + "=" * 80 + "\n")


def main():
    raw_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    if not raw_dir.exists():
        print(f"ERROR: Directory not found: {raw_dir}")
        sys.exit(1)

    # Find all .xlsx and .csv files in data/raw
    target_files = sorted(
        [p for p in raw_dir.iterdir() if p.is_file() and p.suffix.lower() in [".csv", ".xlsx", ".xls"]]
    )

    if not target_files:
        print(f"No .csv or .xlsx files found in {raw_dir}")
        return

    print(f"Found {len(target_files)} raw data file(s) in {raw_dir}:")
    for f in target_files:
        print(f"  - {f.name} ({f.stat().st_size / (1024*1024):.2f} MB)")
    print()

    for file_path in target_files:
        inspect_file(file_path)


if __name__ == "__main__":
    main()
