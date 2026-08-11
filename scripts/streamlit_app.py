import sqlite3
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

DB = "data/db/bluestock_mf.db"

st.set_page_config(
    page_title="Bluestock Mutual Fund Analytics",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def load_data():
    con = sqlite3.connect(DB)

    funds = pd.read_sql("SELECT * FROM fund_master", con)
    perf = pd.read_sql("SELECT * FROM scheme_performance", con)
    metrics = pd.read_sql("SELECT * FROM computed_metrics", con)
    recommendations = pd.read_sql("SELECT * FROM recommendations", con)
    transactions = pd.read_sql("SELECT * FROM investor_transactions", con)
    sip = pd.read_sql("SELECT * FROM monthly_sip_inflows", con)
    cat_inflows = pd.read_sql("SELECT * FROM category_inflows", con)
    aum = pd.read_sql("SELECT * FROM aum_by_fund_house", con)
    folios = pd.read_sql("SELECT * FROM industry_folio_count", con)
    holdings = pd.read_sql("SELECT * FROM portfolio_holdings", con)
    benchmarks = pd.read_sql("SELECT * FROM benchmark_indices", con)

    con.close()

    return (
        funds,
        perf,
        metrics,
        recommendations,
        transactions,
        sip,
        cat_inflows,
        aum,
        folios,
        holdings,
        benchmarks,
    )


(
    funds,
    perf,
    metrics,
    recommendations,
    transactions,
    sip,
    cat_inflows,
    aum,
    folios,
    holdings,
    benchmarks,
) = load_data()


# ---------------------------------------------------------
# Clean / standardise columns
# ---------------------------------------------------------

def clean_numeric(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


perf = clean_numeric(
    perf,
    [
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
        "benchmark_3yr_pct",
        "alpha",
        "beta",
        "sharpe_ratio",
        "sortino_ratio",
        "std_dev_ann_pct",
        "max_drawdown_pct",
        "aum_crore",
        "expense_ratio_pct",
    ],
)

metrics = clean_numeric(
    metrics,
    [
        "cagr",
        "annualised_return",
        "annualised_volatility",
        "sharpe",
        "historical_var_95",
        "max_drawdown",
    ],
)

transactions = clean_numeric(
    transactions,
    ["amount_inr", "annual_income_lakh"],
)

sip = clean_numeric(
    sip,
    [
        "sip_inflow_crore",
        "active_sip_accounts_crore",
        "new_sip_accounts_lakh",
        "sip_aum_lakh_crore",
        "yoy_growth_pct",
    ],
)

cat_inflows = clean_numeric(
    cat_inflows,
    ["net_inflow_crore"],
)

aum = clean_numeric(
    aum,
    ["aum_lakh_crore", "aum_crore", "num_schemes"],
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

st.sidebar.title("📊 Bluestock MF")

page = st.sidebar.radio(
    "Navigate",
    [
        "Executive Overview",
        "Fund Performance",
        "Risk Analytics",
        "Investor Analytics",
        "Recommendations",
    ],
)


# =========================================================
# PAGE 1: EXECUTIVE OVERVIEW
# =========================================================

if page == "Executive Overview":

    st.title("📊 Bluestock Mutual Fund Analytics")
    st.caption(
        "End-to-end mutual fund analytics covering performance, risk, "
        "fund flows and investor behaviour."
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Funds",
        f"{len(funds):,}"
    )

    c2.metric(
        "NAV Observations",
        f"{metrics['observations'].sum():,.0f}"
        if "observations" in metrics.columns
        else "64,320"
    )

    c3.metric(
        "Transactions",
        f"{len(transactions):,}"
    )

    c4.metric(
        "Fund Houses",
        f"{funds['fund_house'].nunique():,}"
        if "fund_house" in funds.columns
        else "N/A"
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if "category" in funds.columns:
            category_counts = (
                funds["category"]
                .fillna("Unknown")
                .value_counts()
                .reset_index()
            )

            category_counts.columns = ["category", "funds"]

            fig = px.bar(
                category_counts,
                x="category",
                y="funds",
                title="Funds by Category",
            )

            fig.update_layout(
                xaxis_title="Category",
                yaxis_title="Number of Funds",
            )

            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "fund_house" in funds.columns:
            house_counts = (
                funds["fund_house"]
                .fillna("Unknown")
                .value_counts()
                .head(10)
                .reset_index()
            )

            house_counts.columns = ["fund_house", "funds"]

            fig = px.bar(
                house_counts,
                x="funds",
                y="fund_house",
                orientation="h",
                title="Top Fund Houses by Number of Schemes",
            )

            st.plotly_chart(fig, use_container_width=True)

    st.subheader("SIP Trend")

    if not sip.empty and "month" in sip.columns:
        sip_plot = sip.copy()
        sip_plot["month"] = pd.to_datetime(
            sip_plot["month"],
            errors="coerce"
        )

        sip_plot = sip_plot.sort_values("month")

        fig = px.line(
            sip_plot,
            x="month",
            y="sip_inflow_crore",
            markers=True,
            title="Monthly SIP Inflows",
        )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="SIP Inflow (₹ Crore)",
        )

        st.plotly_chart(fig, use_container_width=True)


# =========================================================
# PAGE 2: FUND PERFORMANCE
# =========================================================

elif page == "Fund Performance":

    st.title("📈 Fund Performance")

    categories = ["All"]

    if "category" in perf.columns:
        categories += sorted(
            perf["category"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    selected_category = st.sidebar.selectbox(
        "Category",
        categories
    )

    p = perf.copy()

    if selected_category != "All":
        p = p[
            p["category"].astype(str) == selected_category
        ]

    st.subheader("Top Funds by 3-Year Return")

    cols = [
        "scheme_name",
        "fund_house",
        "category",
        "return_3yr_pct",
        "return_5yr_pct",
        "sharpe_ratio",
        "max_drawdown_pct",
        "expense_ratio_pct",
    ]

    available_cols = [
        c for c in cols if c in p.columns
    ]

    display_df = (
        p.sort_values(
            "return_3yr_pct",
            ascending=False
        )[available_cols]
        .head(15)
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("3-Year Return vs Sharpe Ratio")

    fig = px.scatter(
        p,
        x="sharpe_ratio",
        y="return_3yr_pct",
        hover_name="scheme_name",
        color="category" if "category" in p.columns else None,
        size="aum_crore" if "aum_crore" in p.columns else None,
        title="Risk-Adjusted Performance",
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.subheader("Performance Metrics")

    metric_cols = [
        "scheme_name",
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
        "benchmark_3yr_pct",
        "alpha",
        "sharpe_ratio",
        "sortino_ratio",
        "std_dev_ann_pct",
        "max_drawdown_pct",
    ]

    metric_cols = [
        c for c in metric_cols
        if c in p.columns
    ]

    st.dataframe(
        p[metric_cols].sort_values(
            "return_3yr_pct",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# PAGE 3: RISK ANALYTICS
# =========================================================

elif page == "Risk Analytics":

    st.title("⚠️ Risk Analytics")

    if "risk_grade" in perf.columns:
        risk_options = ["All"] + sorted(
            perf["risk_grade"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_risk = st.sidebar.selectbox(
            "Risk Grade",
            risk_options
        )
    else:
        selected_risk = "All"

    r = perf.copy()

    if selected_risk != "All" and "risk_grade" in r.columns:
        r = r[
            r["risk_grade"].astype(str) == selected_risk
        ]

    c1, c2, c3, c4 = st.columns(4)

    if not metrics.empty:

        c1.metric(
            "Average CAGR",
            f"{metrics['cagr'].mean() * 100:.2f}%"
            if "cagr" in metrics.columns
            else "N/A"
        )

        c2.metric(
            "Average Sharpe",
            f"{metrics['sharpe'].mean():.2f}"
            if "sharpe" in metrics.columns
            else "N/A"
        )

        c3.metric(
            "Average VaR 95%",
            f"{metrics['historical_var_95'].mean() * 100:.2f}%"
            if "historical_var_95" in metrics.columns
            else "N/A"
        )

        c4.metric(
            "Average Max Drawdown",
            f"{metrics['max_drawdown'].mean() * 100:.2f}%"
            if "max_drawdown" in metrics.columns
            else "N/A"
        )

    st.subheader("Risk vs Return")

    if not r.empty:

        fig = px.scatter(
            r,
            x="std_dev_ann_pct",
            y="return_3yr_pct",
            hover_name="scheme_name",
            color="category" if "category" in r.columns else None,
            title="Risk vs 3-Year Return",
        )

        fig.update_layout(
            xaxis_title="Annualised Volatility (%)",
            yaxis_title="3-Year Return (%)",
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.subheader("Historical VaR and Maximum Drawdown")

    risk_table = metrics.merge(
        funds[
            [
                c for c in [
                    "amfi_code",
                    "scheme_name",
                    "category",
                ]
                if c in funds.columns
            ]
        ],
        on="amfi_code",
        how="left",
    )

    risk_cols = [
        "scheme_name",
        "category",
        "cagr",
        "sharpe",
        "historical_var_95",
        "max_drawdown",
    ]

    risk_cols = [
        c for c in risk_cols
        if c in risk_table.columns
    ]

    st.dataframe(
        risk_table[risk_cols].sort_values(
            "sharpe",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# PAGE 4: INVESTOR ANALYTICS
# =========================================================

elif page == "Investor Analytics":

    st.title("👥 Investor Analytics")

    age_options = ["All"]

    if "age_group" in transactions.columns:
        age_options += sorted(
            transactions["age_group"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    tier_options = ["All"]

    if "city_tier" in transactions.columns:
        tier_options += sorted(
            transactions["city_tier"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    selected_age = st.sidebar.selectbox(
        "Age Group",
        age_options
    )

    selected_tier = st.sidebar.selectbox(
        "City Tier",
        tier_options
    )

    t = transactions.copy()

    if selected_age != "All":
        t = t[
            t["age_group"].astype(str) == selected_age
        ]

    if selected_tier != "All":
        t = t[
            t["city_tier"].astype(str) == selected_tier
        ]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Transactions",
        f"{len(t):,}"
    )

    c2.metric(
        "Total Transaction Value",
        f"₹{t['amount_inr'].sum() / 1e7:,.2f} Cr"
        if "amount_inr" in t.columns
        else "N/A"
    )

    c3.metric(
        "Average Transaction",
        f"₹{t['amount_inr'].mean():,.0f}"
        if "amount_inr" in t.columns
        else "N/A"
    )

    col1, col2 = st.columns(2)

    with col1:

        if "age_group" in t.columns:

            age_data = (
                t.groupby("age_group")
                .size()
                .reset_index(name="transactions")
            )

            fig = px.bar(
                age_data,
                x="age_group",
                y="transactions",
                title="Transactions by Age Group",
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    with col2:

        if "city_tier" in t.columns:

            tier_data = (
                t.groupby("city_tier")
                .size()
                .reset_index(name="transactions")
            )

            fig = px.bar(
                tier_data,
                x="city_tier",
                y="transactions",
                title="Transactions by City Tier",
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    col3, col4 = st.columns(2)

    with col3:

        if "payment_mode" in t.columns:

            payment = (
                t["payment_mode"]
                .fillna("Unknown")
                .value_counts()
                .reset_index()
            )

            payment.columns = [
                "payment_mode",
                "transactions"
            ]

            fig = px.pie(
                payment,
                names="payment_mode",
                values="transactions",
                title="Payment Mode Distribution",
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    with col4:

        if "transaction_type" in t.columns:

            tx = (
                t["transaction_type"]
                .fillna("Unknown")
                .value_counts()
                .reset_index()
            )

            tx.columns = [
                "transaction_type",
                "transactions"
            ]

            fig = px.pie(
                tx,
                names="transaction_type",
                values="transactions",
                title="Transaction Type Distribution",
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


# =========================================================
# PAGE 5: RECOMMENDATIONS
# =========================================================

elif page == "Recommendations":

    st.title("🏆 Fund Recommendations")

    st.caption(
        "Ranking based on 3-year return, Sharpe ratio, expense ratio "
        "and maximum drawdown."
    )

    rec = recommendations.copy()

    if "risk_category" not in rec.columns:
        rec["risk_category"] = "Not Available"

    if "expense_ratio" not in rec.columns:
        rec["expense_ratio"] = np.nan

    rec["risk_category"] = (
        rec["risk_category"]
        .fillna("Not Available")
    )

    st.subheader("Top 10 Recommended Funds")

    cols = [
        "scheme_name",
        "category",
        "risk_category",
        "return_3yr_pct",
        "sharpe_ratio",
        "expense_ratio",
        "max_drawdown_pct",
        "score",
    ]

    cols = [
        c for c in cols
        if c in rec.columns
    ]

    st.dataframe(
        rec[cols].head(10),
        use_container_width=True,
        hide_index=True,
    )

    if "score" in rec.columns:

        chart = rec.head(10).copy()

        fig = px.bar(
            chart,
            x="score",
            y="scheme_name",
            orientation="h",
            title="Top 10 Fund Scores",
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.subheader("Fund Selection Notes")

    st.markdown(
        """
        **Interpretation**

        - Higher 3-year return contributes positively.
        - Higher Sharpe ratio contributes positively.
        - Lower expense ratio is preferred.
        - Lower maximum drawdown is preferred.
        - The ranking is an analytical screening tool, not personalised investment advice.
        """
    )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.divider()

st.caption(
    "Bluestock Mutual Fund Analytics Capstone | "
    "Analytics based on supplied historical datasets."
)
