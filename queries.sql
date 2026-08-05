-- 1. Top 5 funds by AUM
SELECT f.scheme_name, f.amc_name, a.aum_crores 
FROM fact_aum a
JOIN dim_fund f ON a.amfi_code = f.amfi_code
ORDER BY a.aum_crores DESC
LIMIT 5;

-- 2. Average NAV per month
SELECT strftime('%Y-%m', date) AS month, AVG(nav) AS avg_nav
FROM fact_nav
GROUP BY month
ORDER BY month;

-- 3. SIP YoY Growth Rate
WITH annual_sip AS (
    SELECT strftime('%Y', transaction_date) AS yr, SUM(amount) AS total_sip
    FROM fact_transactions
    WHERE transaction_type = 'SIP'
    GROUP BY yr
)
SELECT yr, total_sip,
       LAG(total_sip) OVER (ORDER BY yr) AS prev_yr_sip,
       ROUND(((total_sip - LAG(total_sip) OVER (ORDER BY yr)) * 100.0 / LAG(total_sip) OVER (ORDER BY yr)), 2) AS yoy_growth_pct
FROM annual_sip;

-- 4. Transaction volume & value by state
SELECT state, COUNT(transaction_id) AS total_transactions, SUM(amount) AS total_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_amount DESC;

-- 5. Funds with expense ratio < 1.0%
SELECT f.scheme_name, p.expense_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio < 1.0
ORDER BY p.expense_ratio ASC;

-- 6. Net Inflow/Outflow by AMC
SELECT f.amc_name,
       SUM(CASE WHEN t.transaction_type IN ('SIP', 'Lumpsum') THEN t.amount ELSE 0 END) -
       SUM(CASE WHEN t.transaction_type = 'Redemption' THEN t.amount ELSE 0 END) AS net_inflow
FROM fact_transactions t
JOIN dim_fund f ON t.amfi_code = f.amfi_code
GROUP BY f.amc_name
ORDER BY net_inflow DESC;

-- 7. High-risk funds with 3-year return > 15%
SELECT f.scheme_name, f.category, p.return_3yr
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE f.risk_level = 'High' AND p.return_3yr > 15.0
ORDER BY p.return_3yr DESC;

-- 8. Count of transactions by KYC Status
SELECT kyc_status, COUNT(*) AS count, SUM(amount) AS total_value
FROM fact_transactions
GROUP BY kyc_status;

-- 9. Top 3 schemes per category by 1-year return
WITH ranked_schemes AS (
    SELECT f.category, f.scheme_name, p.return_1yr,
           DENSE_RANK() OVER (PARTITION BY f.category ORDER BY p.return_1yr DESC) as rnk
    FROM fact_performance p
    JOIN dim_fund f ON p.amfi_code = f.amfi_code
)
SELECT category, scheme_name, return_1yr
FROM ranked_schemes
WHERE rnk <= 3;

-- 10. Expense ratio anomaly flags
SELECT f.scheme_name, p.expense_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio_flag = 1;
