import sqlite3
import pandas as pd
import numpy as np

DB = "data/db/bluestock_mf.db"

con = sqlite3.connect(DB)

perf = pd.read_sql("SELECT * FROM scheme_performance", con)
funds = pd.read_sql("SELECT * FROM fund_master", con)

# Avoid duplicate expense_ratio_pct after merge.
cols = [
    "amfi_code",
    "scheme_name",
    "category",
    "risk_category"
]

if "expense_ratio_pct" in funds.columns:
    cols.append("expense_ratio_pct")

recommendations = perf.merge(
    funds[cols],
    on=["amfi_code", "scheme_name", "category"],
    how="left",
    suffixes=("", "_fund")
)

if "expense_ratio_pct_fund" in recommendations.columns:
    recommendations["expense_ratio"] = recommendations["expense_ratio_pct_fund"]
elif "expense_ratio_pct" in recommendations.columns:
    recommendations["expense_ratio"] = recommendations["expense_ratio_pct"]
else:
    recommendations["expense_ratio"] = 0

recommendations["score"] = (
    recommendations["return_3yr_pct"].fillna(0) * 0.40
    + recommendations["sharpe_ratio"].fillna(0) * 20 * 0.30
    - recommendations["expense_ratio"].fillna(0) * 0.10
    - recommendations["max_drawdown_pct"].abs().fillna(0) * 0.20
)

output_cols = [
    "scheme_name",
    "category",
    "risk_category",
    "return_3yr_pct",
    "sharpe_ratio",
    "expense_ratio",
    "max_drawdown_pct",
    "score"
]

result = recommendations.sort_values(
    "score",
    ascending=False
)[output_cols].head(10)

result.to_sql(
    "recommendations",
    con,
    if_exists="replace",
    index=False
)

print("\nTOP 10 FUND RECOMMENDATIONS")
print(result.to_string(index=False))

con.close()
