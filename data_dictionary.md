# Data Dictionary — Bluestock Mutual Fund Analytics

## Star Schema Overview
- **Fact Tables:** `fact_nav`, `fact_transactions`, `fact_performance`, `fact_aum`
- **Dimension Tables:** `dim_fund`, `dim_date`

---

### 1. `dim_fund`
| Column | Data Type | Key Constraint | Definition |
|---|---|---|---|
| `amfi_code` | INTEGER | PRIMARY KEY | Unique 6-digit identifier for scheme |
| `scheme_name` | TEXT | NOT NULL | Name of mutual fund scheme |
| `category` | TEXT | - | Asset class (Equity, Debt, Hybrid, etc.) |
| `sub_category` | TEXT | - | Detailed classification (Large Cap, Mid Cap, etc.) |
| `amc_name` | TEXT | NOT NULL | Asset Management Company |
| `risk_level` | TEXT | - | SEBI Riskometer level |

---

### 2. `fact_nav`
| Column | Data Type | Key Constraint | Definition |
|---|---|---|---|
| `amfi_code` | INTEGER | FK -> `dim_fund` | Reference to scheme |
| `date` | TEXT | FK -> `dim_date` | Record date |
| `nav` | REAL | NAV > 0 | Net Asset Value in INR |

---

### 3. `fact_transactions`
| Column | Data Type | Key Constraint | Definition |
|---|---|---|---|
| `transaction_id` | INTEGER | PRIMARY KEY | Auto-increment transaction ID |
| `investor_id` | TEXT | - | Masked investor ID |
| `amfi_code` | INTEGER | FK -> `dim_fund` | Scheme reference |
| `transaction_date`| TEXT | FK -> `dim_date` | Date of transaction |
| `transaction_type`| TEXT | Enum check | `SIP`, `Lumpsum`, or `Redemption` |
| `amount` | REAL | amount > 0 | Amount in INR |
| `units` | REAL | - | Units transacted |
| `kyc_status` | TEXT | Enum check | `Verified`, `Pending`, or `Failed` |
| `state` | TEXT | - | Investor residency state |

---

### 4. `fact_performance`
| Column | Data Type | Key Constraint | Definition |
|---|---|---|---|
| `amfi_code` | INTEGER | PK / FK -> `dim_fund` | Scheme reference |
| `return_1yr` | REAL | - | 1-Year CAGR return (%) |
| `return_3yr` | REAL | - | 3-Year CAGR return (%) |
| `return_5yr` | REAL | - | 5-Year CAGR return (%) |
| `expense_ratio` | REAL | - | Fee percentage |
| `expense_ratio_flag`| BOOLEAN | - | 1 if out of normal bounds (0.1%–2.5%) |
| `return_anomaly_flag`| BOOLEAN | - | 1 if returns are anomalous |
