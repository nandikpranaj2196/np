-- Dimension: Fund Information
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    amc_name TEXT NOT NULL,
    risk_level TEXT
);

-- Dimension: Date Calendar
CREATE TABLE IF NOT EXISTS dim_date (
    date_id TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- Fact: Daily NAV History
CREATE TABLE IF NOT EXISTS fact_nav (
    amfi_code INTEGER NOT NULL,
    date TEXT NOT NULL,
    nav REAL NOT NULL,
    PRIMARY KEY (amfi_code, date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    FOREIGN KEY (date) REFERENCES dim_date (date_id)
);

-- Fact: Investor Transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    amfi_code INTEGER NOT NULL,
    transaction_date TEXT NOT NULL,
    transaction_type TEXT CHECK(transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount REAL NOT NULL CHECK(amount > 0),
    units REAL,
    kyc_status TEXT CHECK(kyc_status IN ('Verified', 'Pending', 'Failed')),
    state TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    FOREIGN KEY (transaction_date) REFERENCES dim_date (date_id)
);

-- Fact: Scheme Performance
CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    return_1yr REAL,
    return_3yr REAL,
    return_5yr REAL,
    expense_ratio REAL,
    expense_ratio_flag BOOLEAN,
    return_anomaly_flag BOOLEAN,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code)
);

-- Fact: Fund AUM
CREATE TABLE IF NOT EXISTS fact_aum (
    amfi_code INTEGER NOT NULL,
    as_of_date TEXT NOT NULL,
    aum_crores REAL NOT NULL CHECK(aum_crores >= 0),
    PRIMARY KEY (amfi_code, as_of_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    FOREIGN KEY (as_of_date) REFERENCES dim_date (date_id)
);