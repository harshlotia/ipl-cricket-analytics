# 🏏 IPL Cricket Analytics

A full-stack data engineering project built on **Databricks** with an interactive **Streamlit** dashboard, analyzing 6 seasons (2019–2024) of IPL cricket data across 10 teams using a Delta Lake medallion architecture.

[![Live App](https://img.shields.io/badge/Live%20App-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://ipl-cricket-analytics-mlrqbmsazxrc4irsh6bftq.streamlit.app/)
[![Databricks](https://img.shields.io/badge/Built%20with-Databricks-FF3621?style=for-the-badge&logo=databricks)](https://databricks.com)

---

## Databricks Dashboard

> AI/BI Dashboard built on the Gold Layer — auto-generated with Databricks Genie

**Team Win Percentages · Top Run Scorers · Top Wicket Takers**

![Dashboard - Team Stats and Player Rankings](screenshots/dashboard_1.png)

**Average Scores by Season · Orange & Purple Cap Winners**

![Dashboard - Season Trends and Cap Winners](screenshots/dashboard_2.png)

---

## Databricks Workspace

> Medallion architecture notebooks: Bronze → Silver → Gold

![Databricks Workspace](screenshots/workspace.png)

---

## Features

| Page | Description |
|---|---|
| Team Stats | Win percentages and records for all 10 teams |
| Batting | Career runs, averages, and strike rates |
| Bowling | Career wickets, economy, and bowling averages |
| Season Records | Scoring trends and close match analysis per season |
| Head to Head | Win/loss breakdown for any two-team matchup |
| Venues | Batting-first win % across 12 stadiums |
| Orange & Purple Cap | Top run scorer and wicket taker each season |

---

## Architecture

```
Bronze Layer          Silver Layer          Gold Layer
─────────────         ────────────          ──────────
Raw match data   →    Cleaned + joined  →   Aggregated stats
Batting scores        Enriched features     Career totals
Bowling scores        Match context         Team rankings
                                            Season summaries
```

All layers stored as **Delta Lake tables** on Databricks Free Edition with Serverless compute.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data Storage | Databricks Delta Lake |
| Processing | Apache Spark (PySpark) on Serverless |
| Dashboarding | Databricks AI/BI Dashboard (Genie) |
| Frontend App | Streamlit |
| Deployment | Streamlit Community Cloud |
| Language | Python |

---

## Project Structure

```
├── app.py              # Streamlit application
├── requirements.txt    # Python dependencies
└── .streamlit/
    └── secrets.toml    # Databricks credentials (not committed)
```

Databricks notebooks live in the workspace under `ipl_analytics/`:
- `01_bronze_ingestion` — generates and loads raw synthetic data
- `02_silver_layer` — cleans, enriches, and joins tables
- `03_gold_layer` — builds career stats, rankings, and summaries

---

## Running Locally

1. Clone the repo
   ```bash
   git clone https://github.com/harshlotia/ipl-cricket-analytics.git
   cd ipl-cricket-analytics
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.streamlit/secrets.toml` with your Databricks credentials:
   ```toml
   DATABRICKS_HOST = "your-workspace.cloud.databricks.com"
   HTTP_PATH = "/sql/1.0/warehouses/your-warehouse-id"
   DATABRICKS_TOKEN = "your-personal-access-token"
   ```

4. Run
   ```bash
   streamlit run app.py
   ```

---

## Data

Synthetic IPL data generated with realistic distributions:
- **222 matches** across 6 seasons
- **2,952 batting scorecards**
- **2,220 bowling scorecards**
- 10 teams · 12 venues · ~130 players
