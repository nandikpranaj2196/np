import sqlite3
import numpy as np
import pandas as pd

DB = "data/db/bluestock_mf.db"

con = sqlite3.connect(DB)

nav = pd.read_sql(
    "SELECT * FROM nav_cleaned",
    con,
    parse_dates=["date"]
)

funds = pd.read_sql("SELECT * FROM fund_master", con)
perf = pd.read_sql("SELECT * FROM scheme_performance", con)

nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")
nav = nav.dropna(subset=["nav"]).sort_values(["amfi_code", "date"])

rows = []

for code, g in nav.groupby("amfi_code"):
    g = g.sort_values("date").copy()

    if len(g) < 2:
        continue

    r = g["nav"].pct_change().dropna()

    if len(r) < 2:
        continue

    beginning = g["nav"].iloc[0]
    ending = g["nav"].iloc[-1]
    n = len(r)

    cagr = (ending / beginning) ** (252 / n) - 1
    volatility = r.std() * np.sqrt(252)
    annual_return = r.mean() * 252
    sharpe = annual_return / volatility if volatility != 0 else np.nan

    wealth = (1 + r).cumprod()
    running_max = wealth.cummax()
    drawdown = wealth / running_max - 1
    max_drawdown = drawdown.min()

    var95 = -np.percentile(r, 5)

    rows.append({
        "amfi_code": code,
        "cagr": cagr,
        "annualised_return": annual_return,
        "annualised_volatility": volatility,
        "sharpe": sharpe,
        "historical_var_95": var95,
        "max_drawdown": max_drawdown,
        "observations": n
    })

metrics = pd.DataFrame(rows)

metrics.to_sql(
    "computed_metrics",
    con,
    if_exists="replace",
    index=False
)

print(f"Computed metrics for {len(metrics)} funds")
print(metrics.head())

con.close()
