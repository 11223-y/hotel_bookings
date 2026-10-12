import streamlit as st
import pandas as pd
import numpy as np

# ------------------------------------------------------------
# Page config
# ------------------------------------------------------------
st.set_page_config(
    page_title="Hotel Booking Dashboard",
    page_icon="🏨",
    layout="wide",
)

# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------
@st.cache_data
def load_data(path: str = "data/hotel_bookings.csv") -> pd.DataFrame:
    df = pd.read_csv(path)

    # --- basic cleaning ---
    # children missing -> 0
    df["children"] = df["children"].fillna(0)

    # company / agent missing -> "None"
    df["company"] = df["company"].fillna("None").astype(str)
    df["agent"] = df["agent"].fillna("None").astype(str)

    # country missing -> "Unknown"
    df["country"] = df["country"].fillna("Unknown")

    # ADR: remove negative and extreme outliers for averages
    # keep them in the raw table but flag them
    df["adr_clean"] = df["adr"].where((df["adr"] > 0) & (df["adr"] < 1000), np.nan)

    # arrival date as datetime
    df["arrival_date"] = pd.to_datetime(
        df["arrival_date_year"].astype(str)
        + "-"
        + df["arrival_date_month"]
        + "-"
        + df["arrival_date_day_of_month"].astype(str),
        format="%Y-%B-%d",
        errors="coerce",
    )

    # month order for sorting
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    df["arrival_date_month"] = pd.Categorical(
        df["arrival_date_month"], categories=month_order, ordered=True
    )

    return df


df = load_data()

# ------------------------------------------------------------
# Sidebar filters
# ------------------------------------------------------------
st.sidebar.header("Filters")

hotel_options = sorted(df["hotel"].unique())
selected_hotels = st.sidebar.multiselect(
    "Hotel",
    options=hotel_options,
    default=hotel_options,
)

month_options = list(df["arrival_date_month"].cat.categories)
selected_months = st.sidebar.multiselect(
    "Arrival month",
    options=month_options,
    default=month_options,
)

segment_options = sorted(df["market_segment"].dropna().unique())
selected_segments = st.sidebar.multiselect(
    "Market segment",
    options=segment_options,
    default=segment_options,
)

# apply filters
mask = (
    df["hotel"].isin(selected_hotels)
    & df["arrival_date_month"].isin(selected_months)
    & df["market_segment"].isin(selected_segments)
)
fdf = df[mask].copy()

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
st.title("🏨 Hotel Booking Dashboard")
st.caption(
    "For the **Revenue Manager** — monitor cancellation rate, ADR and booking volume "
    "to decide on pricing, channel quotas and cancellation policy."
)

# data period + refresh line
st.markdown(
    "**Data:** Jul 2015 – Aug 2017, Kaggle snapshot · "
    "**In production:** refreshed nightly from PMS/booking system; "
    "revenue manager reviews daily, weekly deep-dive on Mondays."
)

st.divider()

# ------------------------------------------------------------
# Headline metrics
# ------------------------------------------------------------
total_bookings = len(fdf)
cancel_rate = fdf["is_canceled"].mean() if total_bookings else 0
avg_adr = fdf["adr_clean"].mean()
net_bookings = int((fdf["is_canceled"] == 0).sum())

col1, col2, col3 = st.columns(3)
col1.metric("Total bookings", f"{total_bookings:,}")
col2.metric("Cancellation rate", f"{cancel_rate:.1%}")
col3.metric("Avg daily rate (ADR)", f"€{avg_adr:,.2f}" if pd.notna(avg_adr) else "n/a")

st.divider()

# ------------------------------------------------------------
# Supporting charts
# ------------------------------------------------------------
st.subheader("Why did the numbers move?")

chart_col1, chart_col2 = st.columns(2)

# --- Chart 1: cancellation rate by month ---
with chart_col1:
    st.markdown("**Cancellation rate by arrival month**")
    monthly = (
        fdf.groupby("arrival_date_month", observed=True)["is_canceled"]
        .mean()
        .reset_index()
        .rename(columns={"is_canceled": "cancel_rate"})
    )
    monthly = monthly.sort_values("arrival_date_month")
    if not monthly.empty:
        st.line_chart(monthly.set_index("arrival_date_month")["cancel_rate"])
    else:
        st.info("No data for the current filters.")

# --- Chart 2: cancellation rate by market segment ---
with chart_col2:
    st.markdown("**Cancellation rate by market segment**")
    by_segment = (
        fdf.groupby("market_segment")["is_canceled"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"is_canceled": "cancel_rate"})
    )
    if not by_segment.empty:
        st.bar_chart(by_segment.set_index("market_segment")["cancel_rate"])
    else:
        st.info("No data for the current filters.")

st.divider()

# ------------------------------------------------------------
# Detail table (bottom)
# ------------------------------------------------------------
with st.expander("Detail: underlying bookings (first 500 rows)"):
    show_cols = [
        "hotel", "arrival_date", "arrival_date_month", "market_segment",
        "distribution_channel", "country", "lead_time", "adr",
        "is_canceled", "reservation_status",
    ]
    st.dataframe(fdf[show_cols].head(500), use_container_width=True)

# ------------------------------------------------------------
# Footer notes
# ------------------------------------------------------------
st.caption(
    "Notes: ADR averages exclude negative and extreme (>1000) values. "
    "`deposit_type = Non Refund` can still cancel — read with care. "
    "Country/agent/company fields contain missing or anonymised values."
)
