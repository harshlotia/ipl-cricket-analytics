import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from databricks import sql as dbsql

st.set_page_config(
    page_title="IPL Cricket Analytics",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Palette ───────────────────────────────────────────────────────────────────
BLUE   = "#38bdf8"
AMBER  = "#f59e0b"
GREEN  = "#10b981"
MUTED  = "#64748b"
CARD   = "#111827"
BORDER = "#1e293b"

BLUE_SCALE  = [[0, "#0c2340"], [0.5, "#0369a1"], [1, "#38bdf8"]]
AMBER_SCALE = [[0, "#451a03"], [0.5, "#b45309"], [1, "#f59e0b"]]
GREEN_SCALE = [[0, "#022c22"], [0.5, "#065f46"], [1, "#10b981"]]

def chart(fig, title="", height=370):
    fig.update_layout(
        template="plotly_dark",
        title=dict(text=f"<b>{title}</b>", font=dict(size=14, color="#cbd5e1"), x=0),
        paper_bgcolor="rgba(17,24,39,0.8)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=48, b=10),
        height=height,
        font=dict(color="#94a3b8", size=12),
        xaxis=dict(gridcolor="#1e293b", zeroline=False, showline=False),
        yaxis=dict(gridcolor="#1e293b", zeroline=False, showline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
        hoverlabel=dict(bgcolor="#1e293b", bordercolor="#334155", font_color="#e2e8f0"),
    )
    fig.update_layout(height=height)
    return fig

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Hide sidebar toggle */
[data-testid="collapsedControl"] { display: none; }

/* Top header bar */
.top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0 1.5rem 0;
    border-bottom: 1px solid #1e293b;
    margin-bottom: 1.5rem;
}
.top-bar .brand { font-size: 1.4rem; font-weight: 800; color: #38bdf8; letter-spacing: -0.02em; }
.top-bar .sub   { font-size: 0.8rem; color: #64748b; margin-top: 2px; }

/* KPI strip */
.kpi-strip { display: flex; gap: 1rem; margin-bottom: 1.8rem; }
.kpi {
    flex: 1;
    background: #111827;
    border: 1px solid #1e293b;
    border-top: 3px solid #38bdf8;
    border-radius: 0 0 10px 10px;
    padding: 1.1rem 1rem 0.9rem;
    text-align: center;
}
.kpi .n { font-size: 2rem; font-weight: 800; color: #38bdf8; line-height: 1; }
.kpi .l { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px; }

/* Section label */
.slabel {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #38bdf8;
    margin-bottom: 0.6rem;
    margin-top: 1.2rem;
}

/* Filter pill row */
.filter-row {
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 1.2rem;
    display: flex;
    gap: 2rem;
    align-items: center;
}

/* Stat badge inline */
.badge {
    display: inline-block;
    background: #1e293b;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.8rem;
    color: #94a3b8;
    margin: 2px;
}
</style>
""", unsafe_allow_html=True)

# ── DB helpers ────────────────────────────────────────────────────────────────
@st.cache_resource
def get_conn():
    return dbsql.connect(
        server_hostname=st.secrets["DATABRICKS_HOST"],
        http_path=st.secrets["HTTP_PATH"],
        access_token=st.secrets["DATABRICKS_TOKEN"]
    )

def query(sql: str) -> pd.DataFrame:
    for attempt in range(2):
        try:
            conn = get_conn()
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
            return pd.DataFrame(rows, columns=cols)
        except Exception:
            if attempt == 0:
                get_conn.clear()
            else:
                raise

def kpi(n, l, color=BLUE):
    return f'<div class="kpi"><div class="n" style="color:{color}">{n}</div><div class="l">{l}</div></div>'

def slabel(t):
    st.markdown(f'<div class="slabel">{t}</div>', unsafe_allow_html=True)

# ── Top bar ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-bar">
  <div>
    <div class="brand">🏏 IPL Cricket Analytics</div>
    <div class="sub">Seasons 2019–2024 &nbsp;·&nbsp; 10 Teams &nbsp;·&nbsp; Databricks Delta Lake</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Top navigation ────────────────────────────────────────────────────────────
nav = st.tabs(["Overview", "Teams", "Batting", "Bowling", "Seasons", "Head to Head", "Venues"])


# ── Overview ──────────────────────────────────────────────────────────────────
with nav[0]:
    t_df = query("SELECT SUM(matches_played)/2 AS m FROM ipl_analytics.gold_team_stats")
    p_df = query("SELECT COUNT(*) AS p FROM ipl_analytics.gold_batting_career")

    st.markdown(
        '<div class="kpi-strip">'
        + kpi("6",  "Seasons")
        + kpi("10", "Teams")
        + kpi(int(t_df.iloc[0]["m"]), "Matches")
        + kpi(int(p_df.iloc[0]["p"]), "Players")
        + '</div>', unsafe_allow_html=True
    )

    # Quick team chart + caps side by side
    col_a, col_b = st.columns([3, 2])

    with col_a:
        slabel("Team Win %")
        df_teams = query("""
            SELECT team,
                   ROUND(matches_won * 100.0 / matches_played, 1) AS win_pct
            FROM ipl_analytics.gold_team_stats ORDER BY win_pct DESC
        """)
        fig = go.Figure(go.Bar(
            x=df_teams["win_pct"], y=df_teams["team"],
            orientation="h",
            marker=dict(color=df_teams["win_pct"], colorscale=BLUE_SCALE, showscale=False),
            text=df_teams["win_pct"].map(lambda x: f"{x}%"),
            textposition="outside", textfont=dict(color="#cbd5e1"),
            hovertemplate="<b>%{y}</b>  %{x}%<extra></extra>"
        ))
        chart(fig, "", 340)
        fig.update_layout(yaxis=dict(autorange="reversed"), xaxis_title="Win %")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        slabel("Orange Cap Winners")
        oc = query("SELECT * FROM ipl_analytics.gold_orange_cap ORDER BY season")
        st.dataframe(oc, use_container_width=True, hide_index=True, height=160)

        slabel("Purple Cap Winners")
        pc = query("SELECT * FROM ipl_analytics.gold_purple_cap ORDER BY season")
        st.dataframe(pc, use_container_width=True, hide_index=True, height=160)

    # Season trend full width
    slabel("Season Scoring Trend")
    ss = query("""
        SELECT season, avg_first_innings_score, avg_second_innings_score
        FROM ipl_analytics.gold_season_summary ORDER BY season
    """)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=ss["season"], y=ss["avg_first_innings_score"],
        name="1st Innings", mode="lines+markers",
        line=dict(color=BLUE, width=2.5), marker=dict(size=8),
        hovertemplate="Season %{x}<br>1st Innings: %{y:.0f}<extra></extra>"))
    fig2.add_trace(go.Scatter(x=ss["season"], y=ss["avg_second_innings_score"],
        name="2nd Innings", mode="lines+markers",
        line=dict(color=AMBER, width=2.5, dash="dot"), marker=dict(size=8),
        hovertemplate="Season %{x}<br>2nd Innings: %{y:.0f}<extra></extra>"))
    chart(fig2, "", 260)
    fig2.update_layout(legend=dict(orientation="h", y=1.1), xaxis=dict(tickmode="linear"))
    st.plotly_chart(fig2, use_container_width=True)


# ── Teams ─────────────────────────────────────────────────────────────────────
with nav[1]:
    df = query("""
        SELECT team, matches_played, matches_won, matches_lost,
               ROUND(matches_won * 100.0 / matches_played, 1) AS win_pct
        FROM ipl_analytics.gold_team_stats ORDER BY win_pct DESC
    """)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        slabel("Win Percentage by Team")
        fig = go.Figure(go.Bar(
            x=df["team"], y=df["win_pct"],
            marker=dict(color=df["win_pct"], colorscale=BLUE_SCALE, showscale=False,
                        line=dict(width=0)),
            text=df["win_pct"].map(lambda x: f"{x}%"),
            textposition="outside", textfont=dict(color="#cbd5e1"),
            hovertemplate="<b>%{x}</b><br>Win Rate: %{y}%<extra></extra>"
        ))
        fig.add_hline(y=50, line_dash="dot", line_color=AMBER,
                      annotation_text="50%", annotation_font_color=AMBER)
        chart(fig, "", 380)
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        slabel("Wins vs Losses")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Wins",   x=df["team"], y=df["matches_won"],
                              marker_color=GREEN, hovertemplate="<b>%{x}</b><br>Wins: %{y}<extra></extra>"))
        fig2.add_trace(go.Bar(name="Losses", x=df["team"], y=df["matches_lost"],
                              marker_color="#ef4444", hovertemplate="<b>%{x}</b><br>Losses: %{y}<extra></extra>"))
        chart(fig2, "", 380)
        fig2.update_layout(barmode="stack", xaxis_tickangle=-30,
                           legend=dict(orientation="h", y=1.05))
        st.plotly_chart(fig2, use_container_width=True)

    slabel("Full Standings")
    st.dataframe(df, use_container_width=True, hide_index=True)


# ── Batting ───────────────────────────────────────────────────────────────────
with nav[2]:
    df = query("SELECT * FROM ipl_analytics.gold_batting_career ORDER BY rank_by_runs")
    run_col  = "total_runs"     if "total_runs"     in df.columns else df.select_dtypes("number").columns[0]
    avg_col  = "batting_avg"    if "batting_avg"    in df.columns else None
    sr_col   = "avg_strike_rate"if "avg_strike_rate"in df.columns else None
    name_col = "batsman"        if "batsman"        in df.columns else df.columns[0]

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        run_min = st.slider("Min career runs", int(df[run_col].min()), int(df[run_col].max()),
                            int(df[run_col].quantile(0.25)), step=25, key="bat_slider")
    with c2:
        top_n = st.selectbox("Show top N", [10, 15, 20, 30], key="bat_n")
    with c3:
        chart_type = st.selectbox("Chart", ["Bar", "Scatter", "Bubble"], key="bat_chart")

    filtered = df[df[run_col] >= run_min].head(top_n)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        slabel(f"Top {len(filtered)} Run Scorers")
        if chart_type == "Bar":
            fig = go.Figure(go.Bar(
                x=filtered[run_col], y=filtered[name_col], orientation="h",
                marker=dict(color=filtered[run_col], colorscale=AMBER_SCALE, showscale=False),
                text=filtered[run_col], textposition="outside", textfont=dict(color="#cbd5e1"),
                hovertemplate="<b>%{y}</b><br>Runs: %{x}<extra></extra>"
            ))
            chart(fig, "", max(340, len(filtered) * 28))
            fig.update_layout(yaxis=dict(autorange="reversed"))
        elif chart_type == "Scatter" and avg_col and sr_col:
            fig = px.scatter(filtered, x=avg_col, y=sr_col, hover_data=[name_col, run_col],
                             color=run_col, color_continuous_scale=AMBER_SCALE,
                             labels={avg_col: "Average", sr_col: "Strike Rate"})
            chart(fig, "", 380)
        else:
            fig = px.scatter(filtered, x=avg_col or run_col, y=sr_col or run_col,
                             size=run_col, hover_data=[name_col],
                             color=run_col, color_continuous_scale=AMBER_SCALE, size_max=40)
            chart(fig, "", 380)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        slabel("Career Stats Table")
        display_cols = [c for c in [name_col, run_col, avg_col, sr_col] if c]
        st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True, height=420)


# ── Bowling ───────────────────────────────────────────────────────────────────
with nav[3]:
    df = query("SELECT * FROM ipl_analytics.gold_bowling_career ORDER BY rank_by_wickets")
    wkt_col  = "total_wickets" if "total_wickets" in df.columns else df.select_dtypes("number").columns[0]
    eco_col  = "avg_economy"   if "avg_economy"   in df.columns else None
    bavg_col = "bowling_avg"   if "bowling_avg"   in df.columns else None
    name_col = "bowler"        if "bowler"        in df.columns else df.columns[0]

    c1, c2 = st.columns([3, 1])
    with c1:
        wkt_min = st.slider("Min career wickets", int(df[wkt_col].min()), int(df[wkt_col].max()),
                            int(df[wkt_col].quantile(0.25)), step=2, key="bowl_slider")
    with c2:
        top_n = st.selectbox("Show top N", [10, 15, 20, 30], key="bowl_n")

    filtered = df[df[wkt_col] >= wkt_min].head(top_n)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        slabel(f"Top {len(filtered)} Wicket Takers")
        fig = go.Figure(go.Bar(
            x=filtered[wkt_col], y=filtered[name_col], orientation="h",
            marker=dict(color=filtered[wkt_col], colorscale=GREEN_SCALE, showscale=False),
            text=filtered[wkt_col], textposition="outside", textfont=dict(color="#cbd5e1"),
            hovertemplate="<b>%{y}</b><br>Wickets: %{x}<extra></extra>"
        ))
        chart(fig, "", max(340, len(filtered) * 28))
        fig.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if eco_col and bavg_col:
            slabel("Economy vs Bowling Average")
            fig2 = px.scatter(filtered, x=eco_col, y=bavg_col,
                              hover_data=[name_col, wkt_col],
                              color=wkt_col, color_continuous_scale=GREEN_SCALE,
                              size=wkt_col, size_max=28,
                              labels={eco_col: "Economy", bavg_col: "Bowling Avg"})
            chart(fig2, "", 380)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.dataframe(filtered, use_container_width=True, hide_index=True)


# ── Seasons ───────────────────────────────────────────────────────────────────
with nav[4]:
    df = query("""
        SELECT season, total_matches, avg_first_innings_score,
               avg_second_innings_score, close_matches, toss_win_pct
        FROM ipl_analytics.gold_season_summary ORDER BY season
    """)

    col_a, col_b = st.columns(2)

    with col_a:
        slabel("Average Innings Scores")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["season"], y=df["avg_first_innings_score"],
            name="1st Innings", mode="lines+markers",
            line=dict(color=BLUE, width=2.5), marker=dict(size=9),
            hovertemplate="Season %{x}<br>1st: %{y:.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=df["season"], y=df["avg_second_innings_score"],
            name="2nd Innings", mode="lines+markers",
            line=dict(color=AMBER, width=2.5, dash="dot"), marker=dict(size=9),
            hovertemplate="Season %{x}<br>2nd: %{y:.0f}<extra></extra>"))
        chart(fig, "", 320)
        fig.update_layout(xaxis=dict(tickmode="linear"), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        slabel("Close Matches & Toss Win %")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=df["season"], y=df["close_matches"],
            name="Close Matches", marker_color=BLUE, opacity=0.85,
            hovertemplate="Season %{x}<br>Close Matches: %{y}<extra></extra>"))
        fig2.add_trace(go.Scatter(x=df["season"], y=df["toss_win_pct"],
            name="Toss Win %", yaxis="y2", mode="lines+markers",
            line=dict(color=AMBER, width=2), marker=dict(size=8),
            hovertemplate="Season %{x}<br>Toss Win: %{y:.1f}%<extra></extra>"))
        chart(fig2, "", 320)
        fig2.update_layout(
            yaxis2=dict(overlaying="y", side="right", gridcolor="rgba(0,0,0,0)",
                        tickfont=dict(color=AMBER)),
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig2, use_container_width=True)

    slabel("Season Summary Table")
    st.dataframe(df, use_container_width=True, hide_index=True)


# ── Head to Head ──────────────────────────────────────────────────────────────
with nav[5]:
    df = query("SELECT * FROM ipl_analytics.gold_head_to_head")
    cols     = df.columns.tolist()
    t1_col   = cols[0]; t2_col = cols[1]
    num_cols = df.select_dtypes("number").columns.tolist()
    m_col  = next((c for c in num_cols if "match" in c.lower()), num_cols[0] if num_cols else None)
    w1_col = next((c for c in num_cols if "1" in c and "win" in c.lower()), num_cols[1] if len(num_cols) > 1 else None)
    w2_col = next((c for c in num_cols if "2" in c and "win" in c.lower()), num_cols[2] if len(num_cols) > 2 else None)

    teams = sorted(df[t1_col].unique().tolist())
    col1, col2 = st.columns(2)
    with col1:
        team1 = st.selectbox("Select Team 1", teams)
    with col2:
        team2 = st.selectbox("Select Team 2", [t for t in teams if t != team1])

    mask = (
        ((df[t1_col] == team1) & (df[t2_col] == team2)) |
        ((df[t1_col] == team2) & (df[t2_col] == team1))
    )
    row_df = df[mask]

    if len(row_df) > 0 and w1_col and w2_col and m_col:
        row = row_df.iloc[0]
        t1, t2 = row[t1_col], row[t2_col]
        w1, w2, total = int(row[w1_col]), int(row[w2_col]), int(row[m_col])

        st.markdown(
            '<div class="kpi-strip">'
            + kpi(w1, f"{t1} Wins", BLUE)
            + kpi(total, "Matches Played", MUTED)
            + kpi(w2, f"{t2} Wins", AMBER)
            + '</div>', unsafe_allow_html=True
        )

        col_a, col_b = st.columns(2)
        with col_a:
            fig = go.Figure(go.Pie(
                labels=[t1, t2], values=[w1, w2], hole=0.6,
                marker=dict(colors=[BLUE, AMBER], line=dict(color="#0a0f1e", width=3)),
                textinfo="label+percent", textfont=dict(color="#e2e8f0"),
                hovertemplate="<b>%{label}</b><br>%{value} wins (%{percent})<extra></extra>"
            ))
            fig.add_annotation(text=f"<b>{total}</b><br>matches", x=0.5, y=0.5,
                               font=dict(size=15, color="#e2e8f0"), showarrow=False)
            chart(fig, f"{t1} vs {t2}", 340)
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            fig2 = go.Figure(go.Bar(
                x=[t1, t2], y=[w1, w2],
                marker=dict(color=[BLUE, AMBER], line=dict(width=0)),
                text=[w1, w2], textposition="outside",
                textfont=dict(color="#e2e8f0", size=16),
                hovertemplate="<b>%{x}</b><br>Wins: %{y}<extra></extra>"
            ))
            chart(fig2, "Wins Comparison", 340)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data found for this matchup.")

    with st.expander("Full Head-to-Head Table"):
        st.dataframe(df, use_container_width=True, hide_index=True)


# ── Venues ────────────────────────────────────────────────────────────────────
with nav[6]:
    df = query("SELECT * FROM ipl_analytics.gold_venue_stats ORDER BY matches_played DESC")
    venue_col = "venue" if "venue" in df.columns else df.columns[0]
    num_cols  = df.select_dtypes("number").columns.tolist()
    win_col  = next((c for c in num_cols if "win_pct" in c or "batting_first" in c.lower()), None)
    avg1_col = next((c for c in num_cols if "1st" in c or ("first" in c.lower() and "avg" in c.lower()) or "avg_1" in c.lower()), None)
    avg2_col = next((c for c in num_cols if "2nd" in c or ("second" in c.lower() and "avg" in c.lower()) or "avg_2" in c.lower()), None)

    col_a, col_b = st.columns(2)

    with col_a:
        slabel("Batting First Win % by Venue")
        if win_col:
            fig = go.Figure(go.Bar(
                x=df[venue_col], y=df[win_col],
                marker=dict(color=df[win_col],
                            colorscale=[[0, "#7f1d1d"], [0.5, AMBER], [1, GREEN]],
                            showscale=True,
                            colorbar=dict(thickness=12, tickfont=dict(color="#94a3b8"))),
                text=df[win_col].map(lambda x: f"{x:.0f}%"),
                textposition="outside", textfont=dict(color="#cbd5e1"),
                hovertemplate="<b>%{x}</b><br>Batting First Win %: %{y:.1f}%<extra></extra>"
            ))
            fig.add_hline(y=50, line_dash="dot", line_color=AMBER,
                          annotation_text="50%", annotation_font_color=AMBER)
            chart(fig, "", 380)
            fig.update_layout(xaxis_tickangle=-35)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        slabel("Avg Innings Scores by Venue")
        if avg1_col and avg2_col:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name="1st Innings", x=df[venue_col], y=df[avg1_col],
                                  marker_color=BLUE, opacity=0.9,
                                  hovertemplate="<b>%{x}</b><br>1st Innings: %{y:.0f}<extra></extra>"))
            fig2.add_trace(go.Bar(name="2nd Innings", x=df[venue_col], y=df[avg2_col],
                                  marker_color=AMBER, opacity=0.9,
                                  hovertemplate="<b>%{x}</b><br>2nd Innings: %{y:.0f}<extra></extra>"))
            chart(fig2, "", 380)
            fig2.update_layout(barmode="group", xaxis_tickangle=-35,
                               legend=dict(orientation="h", y=1.08))
            st.plotly_chart(fig2, use_container_width=True)

    slabel("Full Venue Stats")
    st.dataframe(df, use_container_width=True, hide_index=True)
