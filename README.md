# IPL Cricket Analytics

A full-stack data engineering project built on **Databricks** with an interactive **Streamlit** dashboard.

Analyzes 6 seasons (2019–2024) of IPL cricket data across 10 teams using a Delta Lake medallion architecture.

**Live App:** [View on Streamlit Community Cloud](https://ipl-cricket-analytics-mlrqbmsazxrc4irsh6bftq.streamlit.app/)

---

## Features

- **Team Stats** — win percentages and season records for all 10 teams
- **Batting Analytics** — career run totals, batting averages, and strike rates
- **Bowling Analytics** — career wickets, economy rates, and bowling averages
- **Season Records** — innings scoring trends and close match analysis (2019–2024)
- **Head to Head** — win/loss breakdown for any two team matchup
- **Venue Analysis** — batting-first win % and average scores across 12 stadiums
- **Orange & Purple Cap** — top run scorer and wicket taker for each season

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
| Dashboarding | Databricks AI/BI Dashboard |
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

The Databricks notebooks (Bronze → Silver → Gold) live inside the Databricks workspace under `ipl_analytics/`.

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

4. Run the app
   ```bash
   streamlit run app.py
   ```

---

## Data

Synthetic IPL data generated with realistic distributions:
- **222 matches** across 6 seasons
- **2,952 batting scorecards**
- **2,220 bowling scorecards**
- 10 teams, 12 venues, ~130 players
