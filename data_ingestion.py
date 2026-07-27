import os
import requests
import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# 1. DIRECTORY SETUP & MASTER LOAD
# -----------------------------------------------------------------------------
DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
os.makedirs(RAW_DIR, exist_ok=True)

print("=" * 65)
print(" 1. READING MASTER CODES & FETCHING API HISTORY")
print("=" * 65)

master_path = os.path.join(DATA_DIR, "01_fund_master.csv")

if os.path.exists(master_path):
    master_df = pd.read_csv(master_path)
    # Handle varying column naming conventions in company files
    code_col = [c for c in master_df.columns if "code" in c.lower() or "amfi" in c.lower()][0]
    scheme_codes = master_df[code_col].dropna().astype(int).unique().tolist()
    print(f"Loaded {len(scheme_codes)} scheme codes from {master_path}")
else:
    # Default fallback codes provided in initial company specs
    scheme_codes = [118632, 119092, 119551, 120503, 120841, 125497]
    master_df = pd.DataFrame({"amfi_code": scheme_codes, "scheme_name": [f"Scheme_{c}" for c in scheme_codes]})

fetched_frames = []

for code in scheme_codes:
    url = f"https://api.mfapi.in/mf/{code}"
    try:
        res = requests.get(url, timeout=12)
        if res.status_code == 200:
            payload = res.json()
            data = payload.get("data", [])
            meta = payload.get("meta", {})
            if data:
                df = pd.DataFrame(data)
                df["amfi_code"] = int(code)
                df["scheme_name"] = meta.get("scheme_name", f"Scheme_{code}")
                # Enforce strict DD-MM-YYYY parsing for AMFI API
                df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
                df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
                fetched_frames.append(df)
                print(f" [✓] Code {code}: Fetched {len(df)} records")
    except Exception as e:
        print(f" [!] Failed code {code}: {e}")

if not fetched_frames:
    raise RuntimeError("No data fetched. Check network connection.")

raw_df = pd.concat(fetched_frames, ignore_index=True)
raw_df.to_csv(os.path.join(RAW_DIR, "combined_raw_nav.csv"), index=False)

# -----------------------------------------------------------------------------
# 2. DEDUPLICATE & SANITIZE TIME SERIES
# -----------------------------------------------------------------------------
print("\n" + "=" * 65)
print(" 2. SANITIZING TIME SERIES DATA")
print("=" * 65)

# Drop missing or zero NAVs
cleaned_df = raw_df.dropna(subset=["nav", "date"]).copy()
cleaned_df = cleaned_df[cleaned_df["nav"] > 0]

# Deduplicate and sort chronologically
cleaned_df = cleaned_df.sort_values(["amfi_code", "date"]).reset_index(drop=True)
cleaned_df = cleaned_df.drop_duplicates(subset=["amfi_code", "date"], keep="last")

print(f" Cleaned Total: {len(cleaned_df)} rows across {cleaned_df['amfi_code'].nunique()} schemes.")

# -----------------------------------------------------------------------------
# 3. ROBUST FINANCIAL METRICS COMPUTATION
# -----------------------------------------------------------------------------
print("\n" + "=" * 65)
print(" 3. COMPUTING ACCURATE METRICS SUMMARY")
print("=" * 65)

RISK_FREE_RATE = 0.065  # 6.5% standard Indian Repo Rate baseline
metrics = []

for code, group in cleaned_df.groupby("amfi_code"):
    group = group.sort_values("date").reset_index(drop=True)
    scheme_name = group["scheme_name"].iloc[0]

    if len(group) < 252:
        continue

    # 1. Daily percentage returns strictly on trading days
    group["daily_return"] = group["nav"].pct_change()

    # 2. Filter out non-market data jumps (e.g. Dividend/IDCW payouts or face-value splits >10%)
    # This prevents artificial CAGR / Volatility explosions without dropping the fund
    clean_returns = group["daily_return"][(group["daily_return"] > -0.10) & (group["daily_return"] < 0.10)].dropna()

    if len(clean_returns) < 100:
        continue

    # Reconstruct adjusted growth curve to compute true CAGR unaffected by dividend payouts
    adj_start_nav = group["nav"].iloc[0]
    adj_end_nav = adj_start_nav * np.prod(1 + clean_returns)

    start_date = group["date"].iloc[0]
    end_date = group["date"].iloc[-1]
    years = (end_date - start_date).days / 365.25

    if years <= 0:
        continue

    # CAGR based on adjusted total return
    cagr = ((adj_end_nav / adj_start_nav) ** (1 / years)) - 1

    # Annualized Volatility using N=252 trading days
    ann_vol = clean_returns.std() * np.sqrt(252)

    # Sharpe Ratio
    sharpe = (cagr - RISK_FREE_RATE) / ann_vol if ann_vol > 0 else np.nan

    # Drawdown based on log growth series
    log_nav = np.log(1 + clean_returns).cumsum()
    peak = log_nav.cummax()
    max_dd = (np.exp(log_nav - peak) - 1).min()

    metrics.append({
        "amfi_code": code,
        "scheme_name": scheme_name[:35],  # Truncate for display
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "years": round(years, 2),
        "cagr_%": round(cagr * 100, 2),
        "volatility_%": round(ann_vol * 100, 2),
        "sharpe": round(sharpe, 2),
        "max_drawdown_%": round(max_dd * 100, 2)
    })

metrics_df = pd.DataFrame(metrics)

# Print neat table output
print(metrics_df.to_string(index=False))

# Export clean summary file
output_path = os.path.join(DATA_DIR, "fund_metrics_summary.csv")
metrics_df.to_csv(output_path, index=False)
print(f"\n[✓] Finished! Clean metrics saved to: {output_path}")