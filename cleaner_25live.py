#!/usr/bin/env python3
"""
25Live Cleaner — Analysis-Ready Datetime Output with Full Audit (with identity)
-------------------------------------------------------------------------------
* Handles 'cont' tokens (continued across midnight).
* Stitches split rows into one continuous interval per Event/Location/Org.
* Outputs CSV with ISO 8601 datetimes (YYYY-MM-DD HH:MM:SS).
* Audit includes: datatypes, de-dup details, cont replacement counts, stitching stats,
  and SCRIPT IDENTITY (file path, mtime, SHA256, Python/pandas versions, flags).
"""
import pathlib
import sys
import os
import html
import json
import hashlib
import platform
from datetime import datetime, time as dtime
from tkinter import Tk, filedialog, messagebox
import pandas as pd
import numpy as np

# ========================= VERSION / IDENTITY =========================
SCRIPT_VERSION = "25livecleaner v2025-08-28.2"  # <-- bump when you change code

def _script_identity():
    here = os.path.abspath(__file__) if "__file__" in globals() else "(no __file__)"
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(here)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        mtime = "(unknown)"
    try:
        with open(here, "rb") as fh:
            sha256 = hashlib.sha256(fh.read()).hexdigest()
    except Exception:
        sha256 = "(unavailable)"
    py_exe = sys.executable
    return {
        "script_version": SCRIPT_VERSION,
        "script_path": here,
        "script_mtime": mtime,
        "script_sha256": sha256,
        "python_executable": py_exe,
        "python_version": sys.version,
        "platform": platform.platform(),
        "pandas_version": pd.__version__,
        "cwd": os.getcwd(),
    }

# ========================= CONFIG ====================================
AUDIT_FORMAT = "json"
AUTO_OPEN = True
EXPECTED_COLUMNS = [
    "Date", "Res_Start", "Res_End", "Evt_Start", "Evt_End",
    "Location", "Head_Count", "Event_Reservation", "Organization"
]
ISO_8601_FMT = "%Y-%m-%d %H:%M:%S"
DEDUPLICATE = True
IGNORE_HEADCOUNT_IN_DEDUP = True
NORMALIZE_TEXT_FIELDS = True
COALESCE_TIMES = True

# Feature flags
HANDLE_CONT = True
STITCH_CONTINUATIONS = True
STITCH_MAX_GAP = "1min"   # contiguous if next.start - prev.end <= this gap

# ========================= PARSERS/UTILS ==============================
def _parse_date(v):
    if pd.isna(v):
        return pd.NaT
    ts = pd.to_datetime(v, errors="coerce")
    return ts.normalize() if pd.notna(ts) else pd.NaT

def _parse_time(v):
    if pd.isna(v):
        return pd.NaT
    if isinstance(v, (pd.Timestamp, datetime)):
        return pd.Timestamp(v).time()
    if isinstance(v, dtime):
        return v
    s = str(v).strip().replace(".", "")  # remove periods in A.M./P.M.
    ts = pd.to_datetime(s, errors='coerce')
    return ts.time() if pd.notna(ts) else pd.NaT

def _combine_date_time(date_series, time_series):
    return pd.to_datetime(date_series.dt.date.astype(str) + ' ' + time_series.astype(str), errors='coerce')

def _row_has_no_events(row: pd.Series) -> bool:
    return row.astype(str).str.contains(r"\bNo\s*Events\b", case=False, na=False).any()

def _norm_text(s):
    if pd.isna(s):
        return ""
    s = str(s).replace("\u00A0", " ")
    s = " ".join(s.split())
    return s.lower().strip()

def _fmt_datetime_for_audit(v):
    if pd.isna(v) or not isinstance(v, (pd.Timestamp, datetime)):
        return ""
    return v.strftime(ISO_8601_FMT)

# ========================= CONT HELPERS ===============================
def _is_cont(v) -> bool:
    if pd.isna(v):
        return False
    s = str(v).strip().lower()
    return s == "cont" or s.startswith("cont ")

def _time_to_str_hms(t) -> str:
    if pd.isna(t):
        return ""
    if isinstance(t, (pd.Timestamp, datetime)):
        t = pd.Timestamp(t).time()
    if isinstance(t, dtime):
        return f"{t.hour:02d}:{t.minute:02d}:{t.second:02d}"
    x = pd.to_datetime(str(t), errors="coerce")
    return x.time().strftime("%H:%M:%S") if pd.notna(x) else ""

def _fill_cont_times(row, start_col_raw, end_col_raw, start_col_parsed, end_col_parsed):
    start_is_cont = _is_cont(row[start_col_raw])
    end_is_cont   = _is_cont(row[end_col_raw])
    start_s = "00:00:00" if start_is_cont else _time_to_str_hms(row[start_col_parsed])
    end_s   = "23:59:59" if end_is_cont   else _time_to_str_hms(row[end_col_parsed])
    return start_is_cont, end_is_cont, start_s, end_s

def _to_dt_from_str(date_s: pd.Series, time_str_series: pd.Series) -> pd.Series:
    mask_bad = time_str_series.eq("") | date_s.isna()
    comb = (date_s.dt.strftime("%Y-%m-%d") + " " + time_str_series.astype(str)).mask(mask_bad)
    return pd.to_datetime(comb, errors="coerce")

# ========================= STITCHING (warning-safe) ===================
def _safe_concat_same_columns(parts, template_cols) -> pd.DataFrame:
    frames = []
    for d in parts:
        if d is None or not isinstance(d, pd.DataFrame) or d.empty:
            continue
        try:
            if d.isna().all().all():
                continue
        except Exception:
            pass
        frames.append(d.reindex(columns=template_cols))
    if not frames:
        return pd.DataFrame(columns=template_cols)
    return pd.concat(frames, ignore_index=True)

def _stitch_continuations(df: pd.DataFrame,
                          key_cols,
                          start_col="__StartEff_DT",
                          end_col="__EndEff_DT",
                          max_gap="1min"):
    if df.empty:
        return df, {"groups_considered": 0, "groups_stitched": 0, "rows_removed": 0,
                    "rows_before": 0, "rows_after": 0}

    df_sorted = df.sort_values(key_cols + [start_col, end_col],
                               kind="mergesort").reset_index(drop=True)

    out_rows = []
    groups_considered = groups_stitched = rows_removed = 0

    for _, grp in df_sorted.groupby(key_cols, dropna=False, sort=False):
        groups_considered += 1

        valid = grp[grp[start_col].notna() & grp[end_col].notna()].copy()
        invalid = grp[~(grp[start_col].notna() & grp[end_col].notna())].copy()

        if valid.empty:
            out_rows.append(_safe_concat_same_columns([grp], template_cols=df_sorted.columns))
            continue

        open_start = None
        open_end = None
        open_row = None
        stitched_rows = []

        for _, r in valid.iterrows():
            if open_start is None:
                open_start = r[start_col]; open_end = r[end_col]; open_row = r.copy()
            else:
                if (r[start_col] - open_end) <= pd.Timedelta(max_gap):
                    if r[end_col] > open_end:
                        open_end = r[end_col]
                else:
                    base = open_row.copy()
                    base[start_col] = open_start
                    base[end_col]   = open_end
                    stitched_rows.append(base)
                    open_start = r[start_col]; open_end = r[end_col]; open_row = r.copy()

        if open_start is not None:
            base = open_row.copy()
            base[start_col] = open_start
            base[end_col]   = open_end
            stitched_rows.append(base)

        stitched_df = pd.DataFrame(stitched_rows)

        if len(stitched_df) < len(valid):
            groups_stitched += 1
            rows_removed += (len(valid) - len(stitched_df))

        merged = _safe_concat_same_columns([stitched_df, invalid], template_cols=grp.columns)
        out_rows.append(merged)

    before_ct = int(df.shape[0])
    out = _safe_concat_same_columns(out_rows, template_cols=df_sorted.columns)
    after_ct = int(out.shape[0])

    out = out.sort_values([start_col, end_col],
                          kind="mergesort",
                          na_position="first").reset_index(drop=True)

    stats = {
        "groups_considered": int(groups_considered),
        "groups_stitched": int(groups_stitched),
        "rows_removed": int(rows_removed),
        "rows_before": before_ct,
        "rows_after": after_ct
    }
    return out, stats

# ========================= CLEAN ONE FILE =============================
def _clean_one_file(path: pathlib.Path):
    di = {"file": path.name}
    df_raw = pd.read_excel(path, header=None, engine="openpyxl")
    di["raw_rows"] = len(df_raw)

    if df_raw.shape[1] < len(EXPECTED_COLUMNS):
        df_raw.columns = EXPECTED_COLUMNS[:df_raw.shape[1]]
        for i in range(df_raw.shape[1], len(EXPECTED_COLUMNS)):
            df_raw[EXPECTED_COLUMNS[i]] = pd.NA
    df_raw.columns = EXPECTED_COLUMNS + [f"Extra_{i + 1}" for i in range(df_raw.shape[1] - len(EXPECTED_COLUMNS))]

    df = df_raw[EXPECTED_COLUMNS].copy()
    di["data_type_checks"] = {"before_cleaning": {col: str(df[col].dtype) for col in df.columns}}

    df = df.replace(r"^\s*$", pd.NA, regex=True).dropna(how="all")
    di["after_drop_all_empty"] = len(df)

    df = df[~df.apply(_row_has_no_events, axis=1)].copy()
    di["after_drop_no_events"] = len(df)

    df['parsed_date'] = df['Date'].apply(_parse_date)
    time_cols = ["Res_Start", "Res_End", "Evt_Start", "Evt_End"]
    for col in time_cols:
        df[f'parsed_{col}'] = df[col].apply(_parse_time)

    # ===== Build datetime columns with 'cont' handling =====
    cont_counts = {"Res_Start": 0, "Res_End": 0, "Evt_Start": 0, "Evt_End": 0}
    if HANDLE_CONT:
        tmp = df.apply(lambda r: _fill_cont_times(r, "Res_Start", "Res_End", "parsed_Res_Start", "parsed_Res_End"),
                       axis=1, result_type="expand")
        df[["Res_Start_is_cont", "Res_End_is_cont", "Res_Start_fill", "Res_End_fill"]] = tmp
        cont_counts["Res_Start"] = int(df["Res_Start_is_cont"].sum())
        cont_counts["Res_End"]   = int(df["Res_End_is_cont"].sum())

        tmp = df.apply(lambda r: _fill_cont_times(r, "Evt_Start", "Evt_End", "parsed_Evt_Start", "parsed_Evt_End"),
                       axis=1, result_type="expand")
        df[["Evt_Start_is_cont", "Evt_End_is_cont", "Evt_Start_fill", "Evt_End_fill"]] = tmp
        cont_counts["Evt_Start"] = int(df["Evt_Start_is_cont"].sum())
        cont_counts["Evt_End"]   = int(df["Evt_End_is_cont"].sum())

        df["Res_Start_DT"] = _to_dt_from_str(df["parsed_date"], df["Res_Start_fill"])
        df["Res_End_DT"]   = _to_dt_from_str(df["parsed_date"], df["Res_End_fill"])
        df["Evt_Start_DT"] = _to_dt_from_str(df["parsed_date"], df["Evt_Start_fill"])
        df["Evt_End_DT"]   = _to_dt_from_str(df["parsed_date"], df["Evt_End_fill"])
    else:
        df['Res_Start_DT'] = _combine_date_time(df['parsed_date'], df['parsed_Res_Start'])
        df['Res_End_DT']   = _combine_date_time(df['parsed_date'], df['parsed_Res_End'])
        df['Evt_Start_DT'] = _combine_date_time(df['parsed_date'], df['parsed_Evt_Start'])
        df['Evt_End_DT']   = _combine_date_time(df['parsed_date'], df['parsed_Evt_End'])

    df["Head_Count"] = pd.to_numeric(df["Head_Count"], errors="coerce").fillna(0).astype(int)

    final_cols_to_check = EXPECTED_COLUMNS + ['Res_Start_DT', 'Res_End_DT', 'Evt_Start_DT', 'Evt_End_DT']
    di["data_type_checks"]["after_cleaning"] = {col: str(df[col].dtype) for col in final_cols_to_check if col in df}
    if HANDLE_CONT:
        di["cont_tokens_replaced"] = cont_counts

    before = len(df)
    df = df.dropna(subset=["parsed_date"]).copy()
    di["dropped_no_date"] = before - len(df)

    all_times_empty = df[[f'parsed_{c}' for c in time_cols]].isna().all(axis=1)
    no_location = df["Location"].isna() | (df["Location"].astype(str).str.strip() == "")
    before = len(df)
    df = df[~(all_times_empty & no_location)].copy()
    di["dropped_date_only"] = before - len(df)

    for c in ["Event_Reservation", "Organization", "Location"]:
        df[c] = df[c].apply(lambda x: html.unescape(str(x)) if pd.notna(x) else x)

    di["final_rows"] = len(df)
    return df, di

# ========================= MAIN ======================================
def main():
    # Print identity to console so you also see it in the terminal
    ident = _script_identity()
    print(f"Running {ident['script_version']} from {ident['script_path']}")
    print(f"Python: {ident['python_executable']} | pandas: {ident['pandas_version']}")
    print(f"Flags: HANDLE_CONT={HANDLE_CONT}, STITCH_CONTINUATIONS={STITCH_CONTINUATIONS}, COALESCE_TIMES={COALESCE_TIMES}")

    root = Tk()
    root.withdraw()
    files = filedialog.askopenfilenames(title="Select 25Live Excel files", filetypes=[("Excel files", "*.xlsx")])
    if not files:
        messagebox.showerror("Cancelled", "No files selected – exiting.")
        sys.exit(1)

    cleaned_frames, audits = [], []
    for f in files:
        p = pathlib.Path(f)
        try:
            df, di = _clean_one_file(p)
            audits.append(di)
            if not df.empty:
                df["Source_File"] = p.name
                cleaned_frames.append(df)
        except Exception as e:
            print(f"❌ Failed to process {p.name}: {e}")

    if not cleaned_frames:
        print("❌ No data to export.")
        sys.exit(1)

    master = pd.concat(cleaned_frames, ignore_index=True)

    if COALESCE_TIMES:
        master["__StartEff_DT"] = master["Res_Start_DT"].where(master["Res_Start_DT"].notna(), master["Evt_Start_DT"])
        master["__EndEff_DT"]   = master["Res_End_DT"].where(master["Res_End_DT"].notna(), master["Evt_End_DT"])
    else:
        master["__StartEff_DT"] = master["Res_Start_DT"]
        master["__EndEff_DT"]   = master["Res_End_DT"]

    if NORMALIZE_TEXT_FIELDS:
        for col in ["Location", "Event_Reservation", "Organization"]:
            master[f"__norm_{col}"] = master[col].map(_norm_text)
    else:
        for col in ["Location", "Event_Reservation", "Organization"]:
            master[f"__norm_{col}"] = master[col].fillna("")

    stitch_stats = {"groups_considered": 0, "groups_stitched": 0, "rows_removed": 0, "rows_before": len(master), "rows_after": len(master)}
    if STITCH_CONTINUATIONS:
        stitch_key_cols = ["__norm_Event_Reservation", "__norm_Location", "__norm_Organization"]
        master, stitch_stats = _stitch_continuations(master, key_cols=stitch_key_cols,
                                                     start_col="__StartEff_DT",
                                                     end_col="__EndEff_DT",
                                                     max_gap=STITCH_MAX_GAP)

    # De-duplication (after stitching)
    dedup_keys_base = ["parsed_date", "__StartEff_DT", "__EndEff_DT",
                       "__norm_Location", "__norm_Event_Reservation", "__norm_Organization"]
    dedup_keys_full = dedup_keys_base if IGNORE_HEADCOUNT_IN_DEDUP else dedup_keys_base + ["Head_Count"]

    master["__dup_group_size"] = master.groupby(dedup_keys_full, dropna=False)["Source_File"].transform("size")
    master["__dup_rank"] = master.groupby(dedup_keys_full, dropna=False).cumcount()

    cand_keys_ignore_loc = [k for k in dedup_keys_full if k != "__norm_Location"]
    if cand_keys_ignore_loc:
        master["__mixed_location"] = master.groupby(cand_keys_ignore_loc, dropna=False)["__norm_Location"].transform("nunique") > 1
    else:
        master["__mixed_location"] = False

    dup_mask = master["__dup_group_size"] > 1
    duplicates_df = master.loc[dup_mask].copy()
    if not duplicates_df.empty:
        status_conditions = [duplicates_df["__mixed_location"], duplicates_df["__dup_rank"] == 0]
        duplicates_df["dup_status"] = np.select(status_conditions, ["keep", "keep"], default="drop")
        duplicates_df["dup_reason"] = np.select([duplicates_df["__mixed_location"]], ["mixed_location"], default="exact_duplicate")

    rows_to_drop = (master["__dup_group_size"] > 1) & (~master["__mixed_location"]) & (master["__dup_rank"] > 0)
    dedup_removed = int(rows_to_drop.sum())
    if DEDUPLICATE:
        master = master.loc[~rows_to_drop].reset_index(drop=True)

    master.sort_values(by=["__StartEff_DT", "__EndEff_DT"], kind="mergesort", inplace=True, na_position='first')

    downloads = pathlib.Path.home() / "Downloads"
    downloads.mkdir(exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = downloads / f"25Live_cleaned_{stamp}.csv"
    audit_path = downloads / f"25Live_cleaned_{stamp}_audit.json"

    final_csv_columns = [
        'Res_Start_DT', 'Res_End_DT', 'Evt_Start_DT', 'Evt_End_DT',
        'Location', 'Head_Count', 'Event_Reservation', 'Organization', 'Source_File'
    ]
    master_out = master[final_csv_columns].copy()
    for col in ['Res_Start_DT', 'Res_End_DT', 'Evt_Start_DT', 'Evt_End_DT']:
        master_out[col] = master_out[col].dt.strftime(ISO_8601_FMT)
    master_out.to_csv(csv_path, index=False)

    # --- AUDIT FILE GENERATION ---
    dup_groups_payload = []
    if not duplicates_df.empty:
        group_cols = [*dedup_keys_full]
        for key_vals, grp in duplicates_df.groupby(group_cols, dropna=False, sort=False):
            key_dict = dict(zip(group_cols, key_vals))
            key_dict_fmt = {
                "Date": _fmt_datetime_for_audit(key_dict.get("parsed_date")),
                "StartEff_DT": _fmt_datetime_for_audit(key_dict.get("__StartEff_DT")),
                "EndEff_DT": _fmt_datetime_for_audit(key_dict.get("__EndEff_DT")),
                "norm_Location": key_dict.get("__norm_Location", ""),
                "norm_Event_Reservation": key_dict.get("__norm_Event_Reservation", ""),
                "norm_Organization": key_dict.get("__norm_Organization", "")
            }
            mixed_location = bool(grp["__mixed_location"].max())
            rows_payload = []
            for _, r in grp.sort_values(["__dup_rank"]).iterrows():
                rows_payload.append({
                    "dup_status": r.get("dup_status", "unique"), "dup_reason": r.get("dup_reason", ""),
                    "Source_File": r.get("Source_File", ""),
                    "Res_Start_DT": _fmt_datetime_for_audit(r.get("Res_Start_DT")),
                    "Res_End_DT": _fmt_datetime_for_audit(r.get("Res_End_DT")),
                    "Evt_Start_DT": _fmt_datetime_for_audit(r.get("Evt_Start_DT")),
                    "Evt_End_DT": _fmt_datetime_for_audit(r.get("Evt_End_DT")),
                    "Location": r.get("Location", ""), "Head_Count": int(r.get("Head_Count", 0)),
                    "Event_Reservation": r.get("Event_Reservation", ""), "Organization": r.get("Organization", "")
                })
            dup_groups_payload.append({
                "dedup_key": key_dict_fmt, "mixed_location": mixed_location,
                "group_size": int(grp.shape[0]), "rows": rows_payload
            })

    audit_obj = {
        "generated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "script_identity": _script_identity(),
        "config": {
            "deduplicate": DEDUPLICATE,
            "ignore_headcount_in_dedup": IGNORE_HEADCOUNT_IN_DEDUP,
            "normalize_text_fields": NORMALIZE_TEXT_FIELDS,
            "coalesce_times": COALESCE_TIMES,
            "handle_cont": HANDLE_CONT,
            "stitch_continuations": STITCH_CONTINUATIONS,
            "stitch_max_gap": STITCH_MAX_GAP
        },
        "files": audits,
        "stitching": stitch_stats,
        "dedup": {"rows_dropped": int(dedup_removed), "groups": dup_groups_payload},
        "output": {
            "csv_path": str(csv_path), "rows_written": len(master_out),
            "unique_source_files": master_out["Source_File"].nunique(),
            "date_range": {
                "first": master["__StartEff_DT"].min().strftime(ISO_8601_FMT) if master["__StartEff_DT"].notna().any() else "N/A",
                "last": master["__StartEff_DT"].max().strftime(ISO_8601_FMT) if master["__StartEff_DT"].notna().any() else "N/A"
            }
        }
    }
    if AUDIT_FORMAT.lower() == "json":
        with open(audit_path, "w", encoding="utf-8") as jf:
            json.dump(audit_obj, jf, indent=2, default=str)

    print(f"✅ Analysis-ready CSV written: {csv_path}")
    print(f"🧠 Audit saved: {audit_path}")

    if AUTO_OPEN:
        try:
            if sys.platform.startswith("win"):
                os.startfile(csv_path)
            else:
                os.system(f"open '{csv_path}'" if sys.platform == "darwin" else f"xdg-open '{csv_path}'")
        except Exception as e:
            print(f"⚠️  Could not auto-open file: {e}")

if __name__ == "__main__":
    main()