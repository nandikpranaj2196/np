# Bluestock Mutual Fund Analytics - Power BI Specification

## Dashboard Overview
Interactive mutual fund analytics dashboard covering fund performance, risk, market trends, portfolio analytics, and investor behaviour.

## Page 1: Executive Overview
- Total AUM
- Total schemes
- Average 3-year return
- Average Sharpe ratio
- Top performing funds
- AUM by fund house
- SIP inflow trend
- Slicers: Fund House, Category, Risk Category

## Page 2: Fund Performance
- 1Y, 3Y and 5Y returns
- Fund vs benchmark
- CAGR
- Sharpe ratio
- Alpha
- Beta
- Morningstar rating
- Top 10 funds by return
- Slicers: Category, Fund House, Plan

## Page 3: Risk Analytics
- Risk vs return scatter
- Sharpe ratio comparison
- Historical VaR 95%
- Maximum drawdown
- Annualised volatility
- Beta
- Slicers: Risk Category, Category

## Page 4: Investor Analytics
- Transactions by age group
- Transactions by city tier
- Payment mode distribution
- Transaction type distribution
- State/city analysis
- Slicers: Age Group, City Tier, Gender

## Page 5: Market & Portfolio Analytics
- Category-wise inflows
- SIP inflow trend
- Folio growth
- Portfolio sector allocation
- Top holdings
- Benchmark index trends

## Required Measures

CAGR = (Ending NAV / Beginning NAV) ^ (252 / n) - 1

Sharpe = Annualised Return / Annualised Volatility

Beta = Covariance(Fund Return, Benchmark Return) / Variance(Benchmark Return)

Historical VaR(95%) = -5th percentile of daily returns

Maximum Drawdown = Minimum((Wealth / Running Maximum) - 1)

## Data Sources
- fund_master
- nav_cleaned
- scheme_performance
- computed_metrics
- recommendations
- aum_by_fund_house
- monthly_sip_inflows
- category_inflows
- industry_folio_count
- investor_transactions
- portfolio_holdings
- benchmark_indices
