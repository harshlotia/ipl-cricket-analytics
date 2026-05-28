import streamlit as st
import pandas as pd
import plotly.express as px
from databricks import sql as dbsql

st.set_page_config(
    page_title="IPL Cricket Analytics",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2rem; font-weight: bold; }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_conn():
    return dbsql.connect(
        server_hostname=st.secrets["DATABRICKS_HOST"],
        http_path=st.secrets["HTTP_PATH"],
        access_token=st.secrets["DATABRICKS_TOKEN"]
    )


def query(sql_str: str) -> pd.DataFrame:
    for attempt in range(2):
        try:
            conn = get_conn()
            with conn.cursor() as cur:
                cur.execute(sql_str)
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
            return pd.DataFrame(rows, columns=cols)
        except Exception:
            if attempt == 0:
                get_conn.clear()  # stale connection — force a fresh one
            else:
                raise


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🏏 IPL Analytics")
st.sidebar.caption("Seasons 2019–2024 | Databricks Gold Layer")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate to",
    ["Overview", "Team Stats", "Batting", "Bowling",
     "Season Records", "Head to Head", "Venues"]
)


# ── Pages ─────────────────────────────────────────────────────────────────────

if page == "Overview":
    st.title("🏏 IPL Cricket Analytics")
    st.caption("6 seasons · 10 teams · Powered by Databricks Delta Lake")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Seasons", "6")
    with c2:
        st.metric("Teams", "10")
    with c3:
        df = query("SELECT SUM(matches_played)/2 AS m FROM ipl_analytics.gold_team_stats")
        st.metric("Matches Played", int(df.iloc[0]["m"]))
    with c4:
        df = query("SELECT COUNT(*) AS p FROM ipl_analytics.gold_batting_career")
        st.metric("Players Tracked", int(df.iloc[0]["p"]))

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🟠 Orange Cap — Top Run Scorer Each Season")
        oc = query("SELECT * FROM ipl_analytics.gold_orange_cap ORDER BY season")
        st.dataframe(oc, use_container_width=True, hide_index=True)

    with c2:
        st.subheader("🟣 Purple Cap — Top Wicket Taker Each Season")
        pc = query("SELECT * FROM ipl_analytics.gold_purple_cap ORDER BY season")
        st.dataframe(pc, use_container_width=True, hide_index=True)


elif page == "Team Stats":
    st.title("📊 Team Performance")

    df = query("""
        SELECT team, matches_played, matches_won, matches_lost,
               ROUND(matches_won * 100.0 / matches_played, 1) AS win_pct
        FROM ipl_analytics.gold_team_stats
        ORDER BY win_pct DESC
    """)

    fig = px.bar(
        df, x="team", y="win_pct",
        title="Win Percentage by Team",
        color="win_pct",
        color_continuous_scale="Viridis",
        labels={"win_pct": "Win %", "team": "Team"},
        text="win_pct"
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(xaxis_tickangle=-35, yaxis_title="Win %", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Full Standings")
    df_display = df.copy()
    df_display["win_pct"] = df_display["win_pct"].map(lambda x: f"{x}%")
    st.dataframe(df_display, use_container_width=True, hide_index=True)


elif page == "Batting":
    st.title("🏏 Batting Analytics")

    df = query("""
        SELECT * FROM ipl_analytics.gold_batting_career
        ORDER BY rank_by_runs
        LIMIT 20
    """)

    # detect run column name
    run_col = "total_runs" if "total_runs" in df.columns else df.select_dtypes("number").columns[1]
    avg_col = "batting_avg" if "batting_avg" in df.columns else None
    sr_col  = "avg_strike_rate" if "avg_strike_rate" in df.columns else None
    name_col = "batsman" if "batsman" in df.columns else df.columns[0]

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            df.head(10), x=run_col, y=name_col,
            orientation="h",
            title="Top 10 Run Scorers (Career)",
            color=run_col,
            color_continuous_scale="Oranges",
            labels={run_col: "Runs", name_col: "Player"}
        )
        fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        if avg_col and sr_col:
            fig = px.scatter(
                df, x=avg_col, y=sr_col,
                hover_data=[name_col, run_col],
                title="Batting Average vs Strike Rate",
                color=run_col,
                color_continuous_scale="Oranges",
                size=run_col, size_max=28,
                labels={avg_col: "Batting Avg", sr_col: "Strike Rate"}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(df[[name_col, run_col]].head(10), use_container_width=True, hide_index=True)

    st.subheader("Career Stats — Top 20 Batsmen")
    st.dataframe(df, use_container_width=True, hide_index=True)


elif page == "Bowling":
    st.title("🎯 Bowling Analytics")

    df = query("""
        SELECT * FROM ipl_analytics.gold_bowling_career
        ORDER BY rank_by_wickets
        LIMIT 20
    """)

    wkt_col  = "total_wickets" if "total_wickets" in df.columns else df.select_dtypes("number").columns[1]
    eco_col  = "avg_economy"   if "avg_economy"   in df.columns else None
    bavg_col = "bowling_avg"   if "bowling_avg"   in df.columns else None
    name_col = "bowler"        if "bowler"        in df.columns else df.columns[0]

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            df.head(10), x=wkt_col, y=name_col,
            orientation="h",
            title="Top 10 Wicket Takers (Career)",
            color=wkt_col,
            color_continuous_scale="Purples",
            labels={wkt_col: "Wickets", name_col: "Bowler"}
        )
        fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        if eco_col and bavg_col:
            fig = px.scatter(
                df, x=eco_col, y=bavg_col,
                hover_data=[name_col, wkt_col],
                title="Economy vs Bowling Average",
                color=wkt_col,
                color_continuous_scale="Purples",
                size=wkt_col, size_max=28,
                labels={eco_col: "Economy Rate", bavg_col: "Bowling Avg"}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(df[[name_col, wkt_col]].head(10), use_container_width=True, hide_index=True)

    st.subheader("Career Stats — Top 20 Bowlers")
    st.dataframe(df, use_container_width=True, hide_index=True)


elif page == "Season Records":
    st.title("📅 Season-by-Season Records")

    df = query("""
        SELECT season, total_matches, avg_first_innings_score,
               avg_second_innings_score, close_matches, toss_win_pct
        FROM ipl_analytics.gold_season_summary
        ORDER BY season
    """)

    fig = px.line(
        df, x="season",
        y=["avg_first_innings_score", "avg_second_innings_score"],
        title="Average Innings Scores by Season",
        markers=True,
        labels={"value": "Avg Score", "variable": "Innings"}
    )
    fig.update_layout(legend_title="Innings")
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig2 = px.bar(
            df, x="season", y="close_matches",
            title="Close Matches Per Season",
            color="close_matches", color_continuous_scale="Blues",
            labels={"close_matches": "Close Matches"}
        )
        st.plotly_chart(fig2, use_container_width=True)

    with c2:
        fig3 = px.line(
            df, x="season", y="toss_win_pct",
            title="Toss Win % Per Season", markers=True,
            labels={"toss_win_pct": "Toss Win %"}
        )
        fig3.add_hline(y=50, line_dash="dash", line_color="gray",
                       annotation_text="50% baseline")
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Full Season Summary")
    st.dataframe(df, use_container_width=True, hide_index=True)


elif page == "Head to Head":
    st.title("⚔️ Head to Head")

    df = query("SELECT * FROM ipl_analytics.gold_head_to_head")

    # detect column names dynamically
    cols = df.columns.tolist()
    t1_col = cols[0]
    t2_col = cols[1]
    num_cols = df.select_dtypes("number").columns.tolist()
    matches_col  = next((c for c in num_cols if "match" in c.lower()), num_cols[0] if num_cols else None)
    t1wins_col   = next((c for c in num_cols if "1" in c and "win" in c.lower()), num_cols[1] if len(num_cols) > 1 else None)
    t2wins_col   = next((c for c in num_cols if "2" in c and "win" in c.lower()), num_cols[2] if len(num_cols) > 2 else None)

    teams = sorted(df[t1_col].unique().tolist())
    c1, c2 = st.columns(2)
    with c1:
        team1 = st.selectbox("Team 1", teams)
    with c2:
        team2 = st.selectbox("Team 2", [t for t in teams if t != team1])

    mask = (
        ((df[t1_col] == team1) & (df[t2_col] == team2)) |
        ((df[t1_col] == team2) & (df[t2_col] == team1))
    )
    row_df = df[mask]

    if len(row_df) > 0 and t1wins_col and t2wins_col and matches_col:
        row = row_df.iloc[0]
        t1 = row[t1_col]
        t2 = row[t2_col]
        w1 = int(row[t1wins_col])
        w2 = int(row[t2wins_col])
        total = int(row[matches_col])

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(f"{t1} Wins", w1)
        with c2:
            st.metric("Total Matches", total)
        with c3:
            st.metric(f"{t2} Wins", w2)

        fig = px.pie(
            values=[w1, w2],
            names=[t1, t2],
            title=f"{t1} vs {t2} — Win Share",
            color_discrete_sequence=["#636EFA", "#EF553B"]
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data found for this matchup.")

    with st.expander("Full Head-to-Head Table"):
        st.dataframe(df, use_container_width=True, hide_index=True)


elif page == "Venues":
    st.title("🏟️ Venue Analysis")

    df = query("SELECT * FROM ipl_analytics.gold_venue_stats ORDER BY matches_played DESC")

    venue_col = "venue" if "venue" in df.columns else df.columns[0]
    num_cols  = df.select_dtypes("number").columns.tolist()

    win_col  = next((c for c in num_cols if "win_pct" in c or "batting_first" in c.lower()), None)
    avg1_col = next((c for c in num_cols if "1st" in c or "first" in c.lower() or "avg_1" in c.lower()), None)
    avg2_col = next((c for c in num_cols if "2nd" in c or "second" in c.lower() or "avg_2" in c.lower()), None)

    if win_col:
        fig = px.bar(
            df, x=venue_col, y=win_col,
            title="Batting First Win % by Venue",
            color=win_col, color_continuous_scale="RdYlGn",
            text=win_col,
            labels={win_col: "Win %", venue_col: "Venue"}
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50%")
        fig.update_layout(xaxis_tickangle=-40, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    if avg1_col and avg2_col:
        fig2 = px.bar(
            df, x=venue_col, y=[avg1_col, avg2_col],
            title="Average Innings Scores by Venue",
            barmode="group",
            labels={"value": "Avg Score", venue_col: "Venue", "variable": "Innings"}
        )
        fig2.update_layout(xaxis_tickangle=-40)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Full Venue Stats")
    st.dataframe(df, use_container_width=True, hide_index=True)
