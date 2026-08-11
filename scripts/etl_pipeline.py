from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
import logging

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
DB = ROOT / "data" / "db" / "bluestock_mf.db"

PROC.mkdir(parents=True, exist_ok=True)
DB.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

FILES = {
    "fund_master": "01_fund_master.csv",
    "nav_history": "02_nav_history.csv",
    "aum_by_fund_house": "03_aum_by_fund_house.csv",
    "monthly_sip_inflows": "04_monthly_sip_inflows.csv",
    "category_inflows": "05_category_inflows.csv",
    "industry_folio_count": "06_industry_folio_count.csv",
    "scheme_performance": "07_scheme_performance.csv",
    "investor_transactions": "08_investor_transactions.csv",
    "portfolio_holdings": "09_portfolio_holdings.csv",
    "benchmark_indices": "10_benchmark_indices.csv",
}

def main():
    data = {}

    for table, filename in FILES.items():
        path = RAW / filename

        if not path.exists():
            raise FileNotFoundError(f"Missing: {path}")

        df = pd.read_csv(path)

        if df.empty:
            raise ValueError(f"Empty file: {filename}")

        df.columns = [
            str(c).strip().lower().replace(" ", "_").replace("-", "_")
            for c in df.columns
        ]

        data[table] = df
        logging.info("%s: %d rows", table, len(df))

    # Clean NAV
    nav = data["nav_history"].copy()

    nav["date"] = pd.to_datetime(nav["date"], errors="coerce")
    nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")

    nav = nav.dropna(subset=["amfi_code", "date", "nav"])
    nav = nav.drop_duplicates(["amfi_code", "date"])
    nav = nav.sort_values(["amfi_code", "date"])

    # Complete daily dates and forward fill
    groups = []

    for code, group in nav.groupby("amfi_code"):
        group = group.set_index("date").sort_index()

        full_dates = pd.date_range(
            group.index.min(),
            group.index.max(),
            freq="D"
        )

        group = group.reindex(full_dates)
        group["amfi_code"] = code
        group["nav"] = group["nav"].ffill()

        group.index.name = "date"
        groups.append(group.reset_index())

    nav = pd.concat(groups, ignore_index=True)

    nav["return"] = nav.groupby("amfi_code")["nav"].pct_change()
    nav["return_pct"] = nav["return"] * 100

    nav.to_csv(PROC / "nav_cleaned.csv", index=False)

    # Replace existing DB
    if DB.exists():
        DB.unlink()

    conn = sqlite3.connect(DB)

    # Load source tables
    for table, df in data.items():
        if table != "nav_history":
            df.to_sql(table, conn, if_exists="replace", index=False)

    nav.to_sql(
        "nav_cleaned",
        conn,
        if_exists="replace",
        index=False
    )

    # Indexes
    conn.execute(
        "CREATE INDEX idx_nav_code_date "
        "ON nav_cleaned(amfi_code, date)"
    )

    conn.execute(
        "CREATE INDEX idx_transactions_investor "
        "ON investor_transactions(investor_id)"
    )

    conn.execute(
        "CREATE INDEX idx_transactions_scheme "
        "ON investor_transactions(amfi_code)"
    )

    conn.commit()
    conn.close()

    logging.info("ETL completed successfully")
    logging.info("Clean NAV rows: %d", len(nav))
    logging.info("Database: %s", DB)

if __name__ == "__main__":
    main()
