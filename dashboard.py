"""
dashboard.py — Streamlit tracking dashboard for all job applications.

Run with:
    streamlit run dashboard.py
"""

import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

from config import DB_PATH


# ── Page Config ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Job Application Tracker", layout="wide")

st.title("🤖 Autonomous Job Application Agent")
st.subheader("Application Tracking Dashboard")


# ── Load Data ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_data() -> pd.DataFrame:
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM applications ORDER BY date DESC", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


df = load_data()

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()


# ── KPI Cards ──────────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Applications", len(df))

with col2:
    if len(df) > 0:
        avg_score = (
            df["match_score"]
            .str.replace("%", "", regex=False)
            .apply(pd.to_numeric, errors="coerce")
            .mean()
        )
        st.metric("Avg Match Score", f"{avg_score:.1f}%" if pd.notna(avg_score) else "N/A")
    else:
        st.metric("Avg Match Score", "N/A")

with col3:
    st.metric("Unique Companies", df["company"].nunique() if len(df) > 0 else 0)

with col4:
    if len(df) > 0:
        interviews = (df["status"] == "Interview").sum()
        st.metric("Interviews", interviews)
    else:
        st.metric("Interviews", 0)


st.divider()


# ── Applications Table ─────────────────────────────────────────────────────────

st.markdown("### 📋 All Applications")

if len(df) > 0:
    display_cols = ["id", "date", "job_title", "company", "match_score", "status"]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("No applications logged yet. Run the pipeline to get started!")


# ── Charts ─────────────────────────────────────────────────────────────────────

if len(df) > 0:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("### 🥧 Status Breakdown")
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig_pie = px.pie(
            status_counts,
            names="Status",
            values="Count",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with chart_col2:
        st.markdown("### 📈 Applications Over Time")
        df["date"] = pd.to_datetime(df["date"])
        timeline = df.groupby("date").size().reset_index(name="Count")
        fig_line = px.bar(
            timeline,
            x="date",
            y="Count",
            color_discrete_sequence=["#2E75B6"],
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # Match score histogram
    st.markdown("### 🎯 Match Score Distribution")
    scores = (
        df["match_score"]
        .str.replace("%", "", regex=False)
        .apply(pd.to_numeric, errors="coerce")
        .dropna()
    )
    if len(scores) > 0:
        fig_hist = px.histogram(
            scores,
            nbins=10,
            labels={"value": "Match Score (%)"},
            color_discrete_sequence=["#1F3864"],
        )
        st.plotly_chart(fig_hist, use_container_width=True)


# ── Status Updater ─────────────────────────────────────────────────────────────

if len(df) > 0:
    st.divider()
    st.markdown("### ✏️ Update Application Status")
    app_options = {
        f"[{row['id']}] {row['company']} — {row['job_title']}": row["id"]
        for _, row in df.iterrows()
    }
    selected_label = st.selectbox("Select Application", list(app_options.keys()))
    new_status = st.selectbox(
        "New Status",
        ["Applied", "Phone Screen", "Interview", "Technical Test", "Offer", "Rejected"],
    )
    if st.button("Update Status"):
        import sqlite3 as _sqlite3
        conn = _sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE applications SET status=? WHERE id=?",
            (new_status, app_options[selected_label]),
        )
        conn.commit()
        conn.close()
        st.success(f"✅ Status updated to '{new_status}'!")
        st.cache_data.clear()
        st.rerun()