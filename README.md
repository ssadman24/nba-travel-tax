# Travel Tax: NBA Schedule Friction & Competitive Equity

### A five-season geospatial analysis of whether NBA schedule geography is associated with game performance

**Python · pandas · geospatial distance modeling · statsmodels · Plotly · Streamlit**

**[Open the live interactive dashboard](https://raw.githack.com/ssadman24/nba-travel-tax/main/dashboard/index.html)**

![Road friction and margin](figures/road_friction_vs_margin.svg)

## Research question

NBA teams do not experience the schedule equally. A road game can follow a short regional trip or a cross-country flight, a full-rest day or a back-to-back, a stable time zone or a multi-zone shift.

> **Does relative schedule burden predict NBA game performance after accounting for recent team strength, season, and team effects?**

This project analyzes **five completed NBA seasons (2020-21 through 2024-25)**: **6,000 regular-season games and 12,000 team-game observations**.

## Schedule Friction Index

I built an original, outcome-independent **Schedule Friction Index (SFI)** from six pre-game exposures:

- travel distance since the previous game
- absolute time-zone shift
- rest deficit
- games played in the previous seven days
- consecutive road-game streak
- positive altitude gain

Each component is standardized within season and equally weighted. **Game outcomes are not used to construct the index.**

## Main result

In the primary fixed-effects model, a **+1 unit increase in relative SFI** is associated with a **1.35-point lower home-team margin**.

- Estimate: **-1.35 points**
- HC3 95% CI: **-2.06 to -0.63**
- HC3 p-value: **0.00023**
- Primary model sample: **5,596 games**

A separate win-probability model estimates an average **4.0 percentage-point decline in predicted win probability** for a +1 relative-SFI increase.

Because a full +1 SFI unit is a fairly large matchup shift, I also report a standardized interpretation. The observed SD of the relative SFI differential is **0.540**:

- **+1 SD relative SFI → -0.73 points** in adjusted game margin
- **+1 SD relative SFI → -2.1 percentage points** in modeled win probability

### Robustness

The main result also survives a more conservative **two-way clustered standard-error check by home team and away team**:

- Clustered SE: **0.379**
- Clustered 95% CI: **-2.09 to -0.60**
- Clustered p-value: **0.00037**

That robustness check is saved in `outputs/ols_two_way_clustered.txt`.

Road-game performance also weakens at the extremes:

| Road-game group | Win rate | Avg. margin | Avg. modeled travel |
|---|---:|---:|---:|
| Lowest SFI decile | 44.5% | -1.62 | 725 km |
| Highest SFI decile | 37.9% | -4.27 | 1,600 km |

These are observational associations, not proof that travel or fatigue causes a specific game result.

## Why the geography matters

The pipeline explicitly handles changing and neutral venues rather than assigning every game to a team's normal arena.

Examples include:

- Toronto's temporary 2020-21 home base in Tampa
- the Clippers' move to Intuit Dome in 2024-25
- NBA regular-season games in Mexico City and Paris
- the 2024 NBA Cup semifinals in Las Vegas

Nine neutral/global regular-season games are geocoded to their actual host venue and retained in travel calculations, but excluded from the primary home-vs-away regression.

![NBA arena geography](figures/arena_geography.svg)

The **live dashboard** adds an interactive arena map where marker size reflects modeled five-year travel and marker color reflects average SFI percentile.

## Model design

Primary specification:

~~~text
home margin ~ relative SFI
            + pre-game 10-game form differential
            + season fixed effects
            + home-team fixed effects
            + away-team fixed effects
~~~

- HC3 robust standard errors for the primary reported specification
- two-way clustered team-level robustness check
- 5,991 non-neutral games available for home/away pairing
- 5,596 games in the primary model after lagged-form requirements
- separate binomial model for win probability

## Selected results

![Adjusted model effect](figures/primary_model_effect.svg)

![Team schedule friction](figures/team_schedule_friction.svg)

![Modeled travel burden](figures/team_travel_burden.svg)

## Repository structure

~~~text
.
├── README.md
├── app.py
├── requirements.txt
├── dashboard/
│   └── index.html
├── data/
│   ├── DATA_LOG.md
│   └── arena_locations.csv
├── docs/
│   ├── METHODOLOGY.md
│   ├── NBA_Travel_Tax_Findings_Brief.pdf
│   └── PROJECT_DESCRIPTION.md
├── figures/
│   ├── arena_geography.svg
│   ├── primary_model_effect.svg
│   ├── road_friction_vs_margin.svg
│   ├── team_schedule_friction.svg
│   └── team_travel_burden.svg
├── notebooks/
│   └── NBA_Travel_Tax_Findings.ipynb
├── outputs/
│   ├── FINDINGS.md
│   ├── findings.json
│   ├── ols_two_way_clustered.txt
│   ├── road_deciles.csv
│   ├── team_burden.csv
│   └── model_games.csv
└── src/
    ├── analysis.py
    ├── build_assets.py
    └── build_dashboard.py
~~~

## Reproduce

~~~bash
pip install -r requirements.txt
python src/analysis.py
python src/build_assets.py
python src/build_dashboard.py
streamlit run app.py
~~~

The GitHub Actions workflow reruns the five-season analysis and rebuilds the outputs, figures, notebook, PDF, arena map, and live dashboard.

## Data note

The source game logs are public NBA-derived team-game data. This repository does **not** contain private team travel, medical, sleep, or player-tracking information.

## About

Built by **Samir Sadman**, HBSc candidate at the University of Toronto studying **Geospatial Data Science and Economics**.

[LinkedIn](https://www.linkedin.com/in/samir-sadman-085bb8222/) · [GitHub](https://github.com/ssadman24)
