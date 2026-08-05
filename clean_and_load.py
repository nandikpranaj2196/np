import os
import sqlite3
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

print("=== Starting Mutual Fund Data Pipeline ===")

# --- 1. Clean 02_nav_history.csv ---
print("\n[1/5] Cleaning 02_nav_history.csv...")
nav_df = pd.read_csv('data/raw/02_nav_history.csv')
nav_df.columns = nav_df.columns.str.strip().str.lower()

nav_df['date'] = pd.to_datetime(nav_df['date'])
nav_df = nav_df.sort_values(by=['amfi_code', 'date']).reset_index(drop=True)
nav_df = nav_df.drop_duplicates(subset=['amfi_code', 'date'])
nav_df['nav'] = nav_df.groupby('amfi_code')['nav'].ffill()
nav_df = nav_df[nav_df['nav'] > 0]


# --- 2. Clean 08_investor_transactions.csv ---
print("[2/5] Cleaning 08_investor_transactions.csv...")
tx_df = pd.read_csv('data/raw/08_investor_transactions.csv')
tx_df.columns = tx_df.columns.str.strip().str.lower()

# Exact mapping for 08_investor_transactions.csv headers
tx_df = tx_df.rename(columns={'amount_inr': 'amount'})

tx_type_map = {
    'sip': 'SIP', 'Sip': 'SIP', 'SIP': 'SIP',
    'lumpsum': 'Lumpsum', 'Lump Sum': 'Lumpsum', 'Lumpsum': 'Lumpsum',
    'redemption': 'Redemption', 'Redeem': 'Redemption', 'Redemption': 'Redemption'
}
tx_df['transaction_type'] = tx_df['transaction_type'].astype(str).replace(tx_type_map)
tx_df['transaction_date'] = pd.to_datetime(tx_df['transaction_date'])

tx_df['amount'] = pd.to_numeric(tx_df['amount'], errors='coerce')
tx_df = tx_df[tx_df['amount'] > 0]

tx_df['kyc_status'] = tx_df['kyc_status'].replace({'Y': 'Verified', 'N': 'Pending'})
tx_df = tx_df[tx_df['kyc_status'].isin(['Verified', 'Pending', 'Failed'])]

# Compute units by joining with nav_history
print("   -> Calculating transaction units from NAV history...")
tx_df = pd.merge(
    tx_df,
    nav_df[['amfi_code', 'date', 'nav']],
    left_on=['amfi_code', 'transaction_date'],
    right_on=['amfi_code', 'date'],
    how='left'
)
tx_df['units'] = np.where(
    tx_df['nav'].notna() & (tx_df['nav'] > 0),
    tx_df['amount'] / tx_df['nav'],
    np.nan
)
tx_df = tx_df.drop(columns=['date', 'nav'], errors='ignore')


# --- 3. Clean 07_scheme_performance.csv ---
print("[3/5] Cleaning 07_scheme_performance.csv...")
perf_df = pd.read_csv('data/raw/07_scheme_performance.csv')
perf_df.columns = perf_df.columns.str.strip().str.lower()

# Exact column mapping for performance headers
perf_df = perf_df.rename(columns={
    'return_1yr_pct': 'return_1yr',
    'return_3yr_pct': 'return_3yr',
    'return_5yr_pct': 'return_5yr',
    'expense_ratio_pct': 'expense_ratio'
})

return_cols = ['return_1yr', 'return_3yr', 'return_5yr']
for col in return_cols:
    perf_df[col] = pd.to_numeric(perf_df[col], errors='coerce')

perf_df['expense_ratio'] = pd.to_numeric(perf_df['expense_ratio'], errors='coerce')
perf_df['expense_ratio_flag'] = ~perf_df['expense_ratio'].between(0.1, 2.5)

perf_df['return_anomaly_flag'] = perf_df[return_cols].apply(
    lambda x: ((x > 200) | (x < -100)).any(), axis=1
)


# --- 4. Prepare Dimension Tables (dim_fund & dim_date) ---
print("[4/5] Preparing dimension tables (dim_fund & dim_date)...")
fund_df = pd.read_csv('data/raw/01_fund_master.csv')
fund_df.columns = fund_df.columns.str.strip().str.lower()

# Map fund master headers to schema names
fund_df = fund_df.rename(columns={
    'fund_house': 'amc_name',
    'risk_category': 'risk_level'
})

target_fund_cols = ['amfi_code', 'scheme_name', 'category', 'sub_category', 'amc_name', 'risk_level']
fund_df_db = fund_df[target_fund_cols].drop_duplicates(subset=['amfi_code'])

# Generate dim_date calendar dynamically
all_dates = pd.concat([nav_df['date'], tx_df['transaction_date']]).dropna().unique()
date_dim_df = pd.DataFrame({'date_id': pd.to_datetime(all_dates)})
date_dim_df['date_id'] = date_dim_df['date_id'].dt.strftime('%Y-%m-%d')
date_dt = pd.to_datetime(date_dim_df['date_id'])

date_dim_df['year'] = date_dt.dt.year
date_dim_df['quarter'] = date_dt.dt.quarter
date_dim_df['month'] = date_dt.dt.month
date_dim_df['month_name'] = date_dt.dt.strftime('%B')
date_dim_df['day'] = date_dt.dt.day
date_dim_df['day_of_week'] = date_dt.dt.strftime('%A')
date_dim_df['is_weekend'] = date_dt.dt.dayofweek.isin([5, 6])
date_dim_df = date_dim_df.drop_duplicates(subset=['date_id'])

nav_df['date'] = nav_df['date'].dt.strftime('%Y-%m-%d')
tx_df['transaction_date'] = tx_df['transaction_date'].dt.strftime('%Y-%m-%d')


# --- 5. Export Processed CSVs & Load SQLite DB ---
print("[5/5] Saving cleaned CSVs and loading SQLite database...")
os.makedirs('data/processed', exist_ok=True)

nav_df.to_csv('data/processed/nav_history_clean.csv', index=False)
tx_df.to_csv('data/processed/investor_transactions_clean.csv', index=False)
perf_df.to_csv('data/processed/scheme_performance_clean.csv', index=False)

if os.path.exists('bluestock_mf.db'):
    os.remove('bluestock_mf.db')

conn = sqlite3.connect('bluestock_mf.db')
with open('schema.sql', 'r') as f:
    conn.executescript(f.read())
conn.close()

engine = create_engine('sqlite:///bluestock_mf.db')

# Extract exact destination schema columns
nav_df_db = nav_df[['amfi_code', 'date', 'nav']]
tx_df_db = tx_df[['investor_id', 'amfi_code', 'transaction_date', 'transaction_type', 'amount', 'units', 'kyc_status', 'state']]
perf_df_db = perf_df[['amfi_code', 'return_1yr', 'return_3yr', 'return_5yr', 'expense_ratio', 'expense_ratio_flag', 'return_anomaly_flag']]

# Append to SQLite tables
fund_df_db.to_sql('dim_fund', engine, if_exists='append', index=False)
date_dim_df.to_sql('dim_date', engine, if_exists='append', index=False)
nav_df_db.to_sql('fact_nav', engine, if_exists='append', index=False)
tx_df_db.to_sql('fact_transactions', engine, if_exists='append', index=False)
perf_df_db.to_sql('fact_performance', engine, if_exists='append', index=False)

# Build and load fact_aum from 07_scheme_performance or 03_aum_by_fund_house
if 'aum_crore' in perf_df.columns:
    aum_df_db = perf_df[['amfi_code', 'aum_crore']].dropna()
    aum_df_db = aum_df_db.rename(columns={'aum_crore': 'aum_crores'})
    aum_df_db['as_of_date'] = date_dim_df['date_id'].max()
    aum_df_db = aum_df_db[['amfi_code', 'as_of_date', 'aum_crores']].drop_duplicates()
    aum_df_db.to_sql('fact_aum', engine, if_exists='append', index=False)

print("\nSUCCESS! All datasets cleaned, saved to data/processed/, and loaded into bluestock_mf.db")