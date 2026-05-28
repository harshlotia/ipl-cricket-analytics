import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from databricks import sql as dbsql

st.set_page_config(
    page_title="IPL Cricket Analytics",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }

.stApp { background-color: #07071a; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0c29 0%, #1a1040 100%);
    border-right: 1px solid rgba(249,115,22,0.2);
}
[data-testid="stSidebar"] * { color: #c0c0e0 !important; }

.block-container { padding: 1.5rem 2.5rem 2rem; }

.hero {
    background: linear-gradient(135deg, #1a0a3e 0%, #2d1060 50%, #1a0a3e 100%);
    border: 1px solid rgba(249,115,22,0.3);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "🏏";
    position: absolute;
    right: 2rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 5rem;
    opacity: 0.15;
}
.hero h1 {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(90deg, #f97316, #facc15);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.4rem 0;
}
.hero p { color: #9090b0; margin: 0; font-size: 1rem; }

.kpi-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.kpi-card {
    flex: 1;
    background: linear-gradient(135deg, rgba(249,115,22,0.12), rgba(239,68,68,0.06));
    border: 1px solid rgba(249,115,22,0.25);
    border-radius: 14px;
    padding: 1.2rem 1rem;
    text-align: center;
}
.kpi-card .val {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #f97316, #facc15);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
}
.kpi-card .lbl {
    color: #7070a0;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.4rem;
}

.section-title {
    color: #e0e0ff;
    font-size: 1.15rem;
    font-weight: 700;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid rgba(249,115,22,0.35);
    margin-bottom: 1rem;
    margin-top: 0.5rem;
}

.stTabs [data-baseweb="tab-list"] { gap: 6px; background: transparent; border-bottom: 1px solid rgba(255,255,255,0.07); padding-bottom: 0; }
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.04);
    border-radius: 8px 8px 0 0;
    border: 1px solid rgba(255,255,255,0.08);
    border-bottom: none;
    color: #7070a0;
    padding: 0.45rem 1.3rem;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(249,115,22,0.25), rgba(239,68,68,0.15)) !important;
    color: #f97316 !important;
    border-color: rgba(249,115,22,0.4) !important;
}

[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
[data-testid="stDataFrame"] td { font-size: 0.85rem !important; }

.filter-bar {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 1rem;
}

hr { border-color: rgba(255,255,255,0.05); }
</style>
""", unsafe_allow_html=True)

# ── DB ────────────────────────────────────────────────────────────────────────
DARK = "plotly_dark"
PAPER_BG = "rgba(255,255,255,0.02)"
PLOT_BG  = "rgba(0,0,0,0)"
GRID_COL = "rgba(255,255,255,0.06)"
MARGIN   = dict(l=10, r=10, t=45, b=10)

def base_layout(fig, title="", height=370):
    fig.update_layout(
        template=DARK, title=dict(text=title, font=dict(size=15, color="#d0d0f0"), x=0),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        margin=MARGIN, height=height,
        font=dict(color="#9090b0"),
        xaxis=dict(gridcolor=GRID_COL, zeroline=False),
        yaxis=dict(gridcolor=GRID_COL, zeroline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig

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
                get_conn.clear()
            else:
                raise

def kpi(val, label):
    return f'<div class="kpi-card"><div class="val">{val}</div><div class="lbl">{label}</div></div>'

def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏏 IPL Analytics")
    st.markdown("---")
    page = st.radio("", ["Overview", "Team Stats", "Batting", "Bowling",
                          "Season Records", "Head to Head", "Venues"],
                    label_visibility="collapsed")
    st.markdown("---")
    st.caption("Seasons 2019–2024 · 10 Teams · Databricks Delta Lake")


# ── Overview ──────────────────────────────────────────────────────────────────
if page == "Overview":
    st.markdown("""
    <div class="hero">
        <h1>IPL Cricket Analytics</h1>
        <p>6 seasons · 10 teams · 222 matches · Powered by Databricks Delta Lake & Streamlit</p>
    </div>
    """, unsafe_allow_html=True)

    t_df   = query("SELECT SUM(matches_played)/2 AS m FROM ipl_analytics.gold_team_stats")
    p_df   = query("SELECT COUNT(*) AS p FROM ipl_analytics.gold_batting_career")
    oc_cnt = query("SELECT COUNT(DISTINCT season) AS s FROM ipl_analytics.gold_orange_cap")

    st.markdown(
        '<div class="kpi-row">'
        + kpi("6", "Seasons")
        + kpi("10", "Teams")
        + kpi(int(t_df.iloc[0]["m"]), "Matches Played")
        + kpi(int(p_df.iloc[0]["p"]), "Players Tracked")
        + '</div>',
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)
    with c1:
        section("🟠 Orange Cap — Top Run Scorer Each Season")
        oc = query("SELECT * FROM ipl_analytics.gold_orange_cap ORDER BY season")
        st.dataframe(oc, use_container_width=True, hide_index=True)

    with c2:
        section("🟣 Purple Cap — Top Wicket Taker Each Season")
        pc = query("SELECT * FROM ipl_analytics.gold_purple_cap ORDER BY season")
        st.dataframe(pc, use_container_width=True, hide_index=True)


# ── Team Stats ────────────────────────────────────────────────────────────────
elif page == "Team Stats":
    st.markdown('<div class="hero"><h1>Team Performance</h1><p>Win rates and match records across all 10 IPL teams</p></div>', unsafe_allow_html=True)

    df = query("""
        SELECT team, matches_played, matches_won, matches_lost,
               ROUND(matches_won * 100.0 / matches_played, 1) AS win_pct
        FROM ipl_analytics.gold_team_stats ORDER BY win_pct DESC
    """)

    tab1, tab2 = st.tabs(["📊 Bar Chart", "🎯 Full Table"])

    with tab1:
        colors = [f"rgba(249,115,22,{0.4 + 0.06*i})" for i in range(len(df))]
        fig = go.Figure(go.Bar(
            x=df["team"], y=df["win_pct"],
            marker=dict(color=df["win_pct"], colorscale=[[0,"#7c3aed"],[0.5,"#f97316"],[1,"#facc15"]],
                        showscale=False, line=dict(width=0)),
            text=df["win_pct"].map(lambda x: f"{x}%"),
            textposition="outside", textfont=dict(color="#e0e0ff", size=12),
            hovertemplate="<b>%{x}</b><br>Win Rate: %{y}%<extra></extra>"
        ))
        fig.add_hline(y=50, line_dash="dash", line_color="rgba(249,115,22,0.4)",
                      annotation_text="50%", annotation_font_color="#f97316")
        base_layout(fig, "Team Win Percentages", 420)
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        section("Full Standings")
        df_d = df.copy()
        df_d["win_pct"] = df_d["win_pct"].map(lambda x: f"{x}%")
        st.dataframe(df_d, use_container_width=True, hide_index=True, height=380)


# ── Batting ───────────────────────────────────────────────────────────────────
elif page == "Batting":
    st.markdown('<div class="hero"><h1>Batting Analytics</h1><p>Career run totals, averages and strike rates across all players</p></div>', unsafe_allow_html=True)

    df = query("SELECT * FROM ipl_analytics.gold_batting_career ORDER BY rank_by_runs")

    run_col  = "total_runs"    if "total_runs"    in df.columns else df.select_dtypes("number").columns[0]
    avg_col  = "batting_avg"   if "batting_avg"   in df.columns else None
    sr_col   = "avg_strike_rate" if "avg_strike_rate" in df.columns else None
    name_col = "batsman"       if "batsman"       in df.columns else df.columns[0]
    hun_col  = "hundreds"      if "hundreds"      in df.columns else None
    fif_col  = "fifties"       if "fifties"       in df.columns else None

    # Filter bar
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    fc1, fc2 = st.columns([3, 1])
    with fc1:
        max_runs = int(df[run_col].max())
        min_runs = int(df[run_col].min())
        run_filter = st.slider("Minimum career runs", min_runs, max_runs,
                               min_runs + (max_runs - min_runs) // 4, step=50)
    with fc2:
        top_n = st.selectbox("Show top", [10, 15, 20, 30], index=1)
    st.markdown('</div>', unsafe_allow_html=True)

    filtered = df[df[run_col] >= run_filter].head(top_n)

    tab1, tab2, tab3 = st.tabs(["🏆 Top Scorers", "📈 Avg vs SR", "📋 Full Table"])

    with tab1:
        fig = go.Figure(go.Bar(
            x=filtered[run_col], y=filtered[name_col],
            orientation="h",
            marker=dict(color=filtered[run_col],
                        colorscale=[[0,"#7c2d12"],[0.5,"#f97316"],[1,"#facc15"]],
                        showscale=False),
            text=filtered[run_col], textposition="outside",
            textfont=dict(color="#e0e0ff"),
            hovertemplate="<b>%{y}</b><br>Runs: %{x}<extra></extra>"
        ))
        base_layout(fig, f"Top {len(filtered)} Run Scorers", max(380, len(filtered) * 30))
        fig.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if avg_col and sr_col:
            fig = px.scatter(
                filtered, x=avg_col, y=sr_col,
                hover_data=[name_col, run_col],
                size=run_col, size_max=30,
                color=run_col, color_continuous_scale=[[0,"#7c2d12"],[0.5,"#f97316"],[1,"#facc15"]],
                labels={avg_col: "Batting Average", sr_col: "Strike Rate", run_col: "Runs"}
            )
            base_layout(fig, "Batting Average vs Strike Rate", 430)
            fig.update_traces(
                hovertemplate="<b>%{customdata[0]}</b><br>Avg: %{x}<br>SR: %{y}<br>Runs: %{customdata[1]}<extra></extra>"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Strike rate / average data not available.")

    with tab3:
        section(f"Career Stats ({len(filtered)} players)")
        st.dataframe(filtered, use_container_width=True, hide_index=True, height=420)


# ── Bowling ───────────────────────────────────────────────────────────────────
elif page == "Bowling":
    st.markdown('<div class="hero"><h1>Bowling Analytics</h1><p>Career wickets, economy rates and bowling averages</p></div>', unsafe_allow_html=True)

    df = query("SELECT * FROM ipl_analytics.gold_bowling_career ORDER BY rank_by_wickets")

    wkt_col  = "total_wickets" if "total_wickets" in df.columns else df.select_dtypes("number").columns[0]
    eco_col  = "avg_economy"   if "avg_economy"   in df.columns else None
    bavg_col = "bowling_avg"   if "bowling_avg"   in df.columns else None
    name_col = "bowler"        if "bowler"        in df.columns else df.columns[0]

    # Filter bar
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    fc1, fc2 = st.columns([3, 1])
    with fc1:
        max_w = int(df[wkt_col].max())
        min_w = int(df[wkt_col].min())
        wkt_filter = st.slider("Minimum career wickets", min_w, max_w,
                               min_w + (max_w - min_w) // 4, step=2)
    with fc2:
        top_n = st.selectbox("Show top", [10, 15, 20, 30], index=1)
    st.markdown('</div>', unsafe_allow_html=True)

    filtered = df[df[wkt_col] >= wkt_filter].head(top_n)

    tab1, tab2, tab3 = st.tabs(["🎯 Top Wicket Takers", "📈 Economy vs Avg", "📋 Full Table"])

    with tab1:
        fig = go.Figure(go.Bar(
            x=filtered[wkt_col], y=filtered[name_col],
            orientation="h",
            marker=dict(color=filtered[wkt_col],
                        colorscale=[[0,"#2e1065"],[0.5,"#7c3aed"],[1,"#c084fc"]],
                        showscale=False),
            text=filtered[wkt_col], textposition="outside",
            textfont=dict(color="#e0e0ff"),
            hovertemplate="<b>%{y}</b><br>Wickets: %{x}<extra></extra>"
        ))
        base_layout(fig, f"Top {len(filtered)} Wicket Takers", max(380, len(filtered) * 30))
        fig.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if eco_col and bavg_col:
            fig = px.scatter(
                filtered, x=eco_col, y=bavg_col,
                hover_data=[name_col, wkt_col],
                size=wkt_col, size_max=30,
                color=wkt_col, color_continuous_scale=[[0,"#2e1065"],[0.5,"#7c3aed"],[1,"#c084fc"]],
                labels={eco_col: "Economy Rate", bavg_col: "Bowling Average", wkt_col: "Wickets"}
            )
            base_layout(fig, "Economy Rate vs Bowling Average", 430)
            fig.update_traces(
                hovertemplate="<b>%{customdata[0]}</b><br>Economy: %{x}<br>Avg: %{y}<br>Wickets: %{customdata[1]}<extra></extra>"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Economy / average data not available.")

    with tab3:
        section(f"Career Stats ({len(filtered)} bowlers)")
        st.dataframe(filtered, use_container_width=True, hide_index=True, height=420)


# ── Season Records ────────────────────────────────────────────────────────────
elif page == "Season Records":
    st.markdown('<div class="hero"><h1>Season Records</h1><p>Year-by-year scoring trends, close matches and toss analysis</p></div>', unsafe_allow_html=True)

    df = query("""
        SELECT season, total_matches, avg_first_innings_score,
               avg_second_innings_score, close_matches, toss_win_pct
        FROM ipl_analytics.gold_season_summary ORDER BY season
    """)

    tab1, tab2, tab3 = st.tabs(["📈 Scoring Trends", "⚡ Close Matches", "🎲 Toss Impact"])

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["season"], y=df["avg_first_innings_score"],
            name="1st Innings", mode="lines+markers",
            line=dict(color="#f97316", width=3),
            marker=dict(size=10, symbol="circle"),
            hovertemplate="Season %{x}<br>1st Innings Avg: %{y:.1f}<extra></extra>"
        ))
        fig.add_trace(go.Scatter(
            x=df["season"], y=df["avg_second_innings_score"],
            name="2nd Innings", mode="lines+markers",
            line=dict(color="#7c3aed", width=3),
            marker=dict(size=10, symbol="diamond"),
            hovertemplate="Season %{x}<br>2nd Innings Avg: %{y:.1f}<extra></extra>"
        ))
        base_layout(fig, "Average Innings Scores by Season", 400)
        fig.update_layout(xaxis=dict(tickmode="linear"), legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = go.Figure(go.Bar(
            x=df["season"], y=df["close_matches"],
            marker=dict(color=df["close_matches"],
                        colorscale=[[0,"#164e63"],[0.5,"#0ea5e9"],[1,"#7dd3fc"]],
                        showscale=False),
            text=df["close_matches"], textposition="outside",
            textfont=dict(color="#e0e0ff"),
            hovertemplate="Season %{x}<br>Close Matches: %{y}<extra></extra>"
        ))
        base_layout(fig, "Close Matches Per Season", 380)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[["season", "total_matches", "close_matches"]], use_container_width=True, hide_index=True)

    with tab3:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["season"], y=df["toss_win_pct"],
            mode="lines+markers+text",
            line=dict(color="#16a34a", width=3),
            marker=dict(size=10),
            text=df["toss_win_pct"].map(lambda x: f"{x:.1f}%"),
            textposition="top center",
            textfont=dict(color="#86efac"),
            hovertemplate="Season %{x}<br>Toss Win %: %{y:.1f}%<extra></extra>"
        ))
        fig.add_hline(y=50, line_dash="dash", line_color="rgba(249,115,22,0.5)",
                      annotation_text="50% baseline", annotation_font_color="#f97316")
        base_layout(fig, "Toss Win % Per Season", 380)
        st.plotly_chart(fig, use_container_width=True)


# ── Head to Head ──────────────────────────────────────────────────────────────
elif page == "Head to Head":
    st.markdown('<div class="hero"><h1>Head to Head</h1><p>Win/loss breakdown between any two IPL teams</p></div>', unsafe_allow_html=True)

    df = query("SELECT * FROM ipl_analytics.gold_head_to_head")
    cols     = df.columns.tolist()
    t1_col   = cols[0]
    t2_col   = cols[1]
    num_cols = df.select_dtypes("number").columns.tolist()
    m_col  = next((c for c in num_cols if "match" in c.lower()), num_cols[0] if num_cols else None)
    w1_col = next((c for c in num_cols if "1" in c and "win" in c.lower()), num_cols[1] if len(num_cols) > 1 else None)
    w2_col = next((c for c in num_cols if "2" in c and "win" in c.lower()), num_cols[2] if len(num_cols) > 2 else None)

    teams = sorted(df[t1_col].unique().tolist())
    c1, c2 = st.columns(2)
    with c1:
        team1 = st.selectbox("🔵 Select Team 1", teams)
    with c2:
        team2 = st.selectbox("🔴 Select Team 2", [t for t in teams if t != team1])

    mask = (
        ((df[t1_col] == team1) & (df[t2_col] == team2)) |
        ((df[t1_col] == team2) & (df[t2_col] == team1))
    )
    row_df = df[mask]

    if len(row_df) > 0 and w1_col and w2_col and m_col:
        row   = row_df.iloc[0]
        t1    = row[t1_col]
        t2    = row[t2_col]
        w1    = int(row[w1_col])
        w2    = int(row[w2_col])
        total = int(row[m_col])

        st.markdown(
            f'<div class="kpi-row">'
            + kpi(w1, f"{t1} Wins")
            + kpi(total, "Matches Played")
            + kpi(w2, f"{t2} Wins")
            + '</div>',
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure(go.Pie(
                labels=[t1, t2],
                values=[w1, w2],
                hole=0.55,
                marker=dict(colors=["#f97316", "#7c3aed"],
                            line=dict(color="#07071a", width=3)),
                textinfo="label+percent",
                textfont=dict(color="#e0e0ff", size=13),
                hovertemplate="<b>%{label}</b><br>Wins: %{value}<br>%{percent}<extra></extra>"
            ))
            fig.add_annotation(text=f"{total}<br>Matches", x=0.5, y=0.5,
                               font=dict(size=16, color="#e0e0ff"), showarrow=False)
            base_layout(fig, f"{t1} vs {t2}", 350)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig2 = go.Figure(go.Bar(
                x=[t1, t2], y=[w1, w2],
                marker=dict(color=["#f97316", "#7c3aed"],
                            line=dict(width=0)),
                text=[w1, w2], textposition="outside",
                textfont=dict(color="#e0e0ff", size=14),
                hovertemplate="<b>%{x}</b><br>Wins: %{y}<extra></extra>"
            ))
            base_layout(fig2, "Wins Comparison", 350)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data found for this matchup.")

    with st.expander("📋 Full Head-to-Head Table"):
        st.dataframe(df, use_container_width=True, hide_index=True)


# ── Venues ────────────────────────────────────────────────────────────────────
elif page == "Venues":
    st.markdown('<div class="hero"><h1>Venue Analysis</h1><p>Batting-first win rates and average scores across 12 IPL stadiums</p></div>', unsafe_allow_html=True)

    df = query("SELECT * FROM ipl_analytics.gold_venue_stats ORDER BY matches_played DESC")
    venue_col = "venue" if "venue" in df.columns else df.columns[0]
    num_cols  = df.select_dtypes("number").columns.tolist()
    win_col  = next((c for c in num_cols if "win_pct" in c or "batting_first" in c.lower()), None)
    avg1_col = next((c for c in num_cols if "1st" in c or "first" in c.lower() or "avg_1" in c.lower()), None)
    avg2_col = next((c for c in num_cols if "2nd" in c or "second" in c.lower() or "avg_2" in c.lower()), None)

    tab1, tab2 = st.tabs(["🏟️ Batting First Win %", "📊 Average Scores"])

    with tab1:
        if win_col:
            fig = go.Figure(go.Bar(
                x=df[venue_col], y=df[win_col],
                marker=dict(color=df[win_col],
                            colorscale=[[0,"#7f1d1d"],[0.5,"#f97316"],[1,"#16a34a"]],
                            showscale=True,
                            colorbar=dict(title="Win %", tickfont=dict(color="#9090b0"))),
                text=df[win_col].map(lambda x: f"{x:.1f}%"),
                textposition="outside", textfont=dict(color="#e0e0ff"),
                hovertemplate="<b>%{x}</b><br>Batting First Win %: %{y:.1f}%<extra></extra>"
            ))
            fig.add_hline(y=50, line_dash="dash", line_color="rgba(249,115,22,0.5)",
                          annotation_text="50%", annotation_font_color="#f97316")
            base_layout(fig, "Batting First Win % by Venue", 420)
            fig.update_layout(xaxis_tickangle=-35)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if avg1_col and avg2_col:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                name="1st Innings Avg", x=df[venue_col], y=df[avg1_col],
                marker_color="#f97316",
                hovertemplate="<b>%{x}</b><br>1st Innings Avg: %{y:.1f}<extra></extra>"
            ))
            fig2.add_trace(go.Bar(
                name="2nd Innings Avg", x=df[venue_col], y=df[avg2_col],
                marker_color="#7c3aed",
                hovertemplate="<b>%{x}</b><br>2nd Innings Avg: %{y:.1f}<extra></extra>"
            ))
            base_layout(fig2, "Average Scores by Venue", 420)
            fig2.update_layout(barmode="group", xaxis_tickangle=-35,
                               legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig2, use_container_width=True)

    section("Full Venue Stats")
    st.dataframe(df, use_container_width=True, hide_index=True)
