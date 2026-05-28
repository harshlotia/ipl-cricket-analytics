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
    [data-testid="stSidebar"] { background-color: #0e1117; }
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
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(sql_str)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return pd.DataFrame(rows, columns=cols)


# ── Sidebar ──────────────────────────────────────────────────────────────────
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
        oc = query("""
            SELECT season, batsman AS player, team, season_runs AS runs
            FROM ipl_analytics.gold_orange_cap
            ORDER BY season
        """)
        st.dataframe(oc, use_container_width=True, hide_index=True)

    with c2:
        st.subheader("🟣 Purple Cap — Top Wicket Taker Each Season")
        pc = query("""
            SELECT season, bowler AS player, team, season_wickets AS wickets
            FROM ipl_analytics.gold_purple_cap
            ORDER BY season
        """)
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
        SELECT batsman, team, innings, total_runs, highest_score,
               batting_avg, avg_strike_rate, fifties, hundreds, rank_by_runs
        FROM ipl_analytics.gold_batting_career
        ORDER BY rank_by_runs
        LIMIT 20
    """)

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            df.head(10), x="total_runs", y="batsman",
            orientation="h",
            title="Top 10 Run Scorers (Career)",
            color="total_runs",
            color_continuous_scale="Oranges",
            labels={"total_runs": "Runs", "batsman": "Player"}
        )
        fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.scatter(
            df, x="batting_avg", y="avg_strike_rate",
            hover_data=["batsman", "team", "total_runs"],
            title="Average vs Strike Rate",
            color="total_runs",
            color_continuous_scale="Oranges",
            size="total_runs", size_max=28,
            labels={"batting_avg": "Batting Avg", "avg_strike_rate": "Strike Rate"}
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Career Stats — Top 20 Batsmen")
    st.dataframe(df, use_container_width=True, hide_index=True)


elif page == "Bowling":
    st.title("🎯 Bowling Analytics")

    df = query("""
        SELECT bowler, team, matches, total_wickets, avg_economy,
               bowling_avg, three_fers, rank_by_wickets
        FROM ipl_analytics.gold_bowling_career
        ORDER BY rank_by_wickets
        LIMIT 20
    """)

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            df.head(10), x="total_wickets", y="bowler",
            orientation="h",
            title="Top 10 Wicket Takers (Career)",
            color="total_wickets",
            color_continuous_scale="Purples",
            labels={"total_wickets": "Wickets", "bowler": "Bowler"}
        )
        fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.scatter(
            df, x="avg_economy", y="bowling_avg",
            hover_data=["bowler", "team", "total_wickets"],
            title="Economy vs Bowling Average",
            color="total_wickets",
            color_continuous_scale="Purples",
            size="total_wickets", size_max=28,
            labels={"avg_economy": "Economy Rate", "bowling_avg": "Bowling Avg"}
        )
        st.plotly_chart(fig, use_container_width=True)

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
        labels={"value": "Avg Score", "variable": "Innings",
                "avg_first_innings_score": "1st Innings",
                "avg_second_innings_score": "2nd Innings"}
    )
    fig.update_layout(legend_title="Innings")
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        fig2 = px.bar(
            df, x="season", y="close_matches",
            title="Close Matches Per Season",
            color="close_matches",
            color_continuous_scale="Blues",
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

    teams = sorted(df["team1"].unique().tolist())
    c1, c2 = st.columns(2)
    with c1:
        team1 = st.selectbox("Team 1", teams)
    with c2:
        team2 = st.selectbox("Team 2", [t for t in teams if t != team1])

    mask = (
        ((df["team1"] == team1) & (df["team2"] == team2)) |
        ((df["team1"] == team2) & (df["team2"] == team1))
    )
    row_df = df[mask]

    if len(row_df) > 0:
        row = row_df.iloc[0]
        t1, t2 = row["team1"], row["team2"]
        w1, w2 = int(row["team1_wins"]), int(row["team2_wins"])
        total = int(row["matches"])

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

    df = query("""
        SELECT venue, matches_played, avg_1st_innings, avg_2nd_innings,
               batting_first_win_pct
        FROM ipl_analytics.gold_venue_stats
        ORDER BY matches_played DESC
    """)

    fig = px.bar(
        df, x="venue", y="batting_first_win_pct",
        title="Batting First Win % by Venue",
        color="batting_first_win_pct",
        color_continuous_scale="RdYlGn",
        text="batting_first_win_pct",
        labels={"batting_first_win_pct": "Win %", "venue": "Venue"}
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.add_hline(y=50, line_dash="dash", line_color="gray",
                  annotation_text="50%")
    fig.update_layout(xaxis_tickangle=-40, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.bar(
        df, x="venue",
        y=["avg_1st_innings", "avg_2nd_innings"],
        title="Average Innings Scores by Venue",
        barmode="group",
        labels={"value": "Avg Score", "venue": "Venue", "variable": "Innings"},
        color_discrete_map={"avg_1st_innings": "#636EFA", "avg_2nd_innings": "#EF553B"}
    )
    fig2.update_layout(xaxis_tickangle=-40)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Full Venue Stats")
    st.dataframe(df, use_container_width=True, hide_index=True)
