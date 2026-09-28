# Data Engineering Log

## Study window

Five completed NBA regular seasons:

- 2020-21
- 2021-22
- 2022-23
- 2023-24
- 2024-25

## Source and coverage

The pipeline uses public team game logs from the `llimllib/nba_data` repository, stored as season-level Parquet files.

Expected and verified coverage after the build:

| Season | Games | Team-game rows |
|---|---:|---:|
| 2020-21 | 1,080 | 2,160 |
| 2021-22 | 1,230 | 2,460 |
| 2022-23 | 1,230 | 2,460 |
| 2023-24 | 1,230 | 2,460 |
| 2024-25 | 1,230 | 2,460 |
| **Total** | **6,000** | **12,000** |

## Geography corrections

The analysis does not assume that every game occurs at a team's normal home arena.

Historical/venue logic includes:

- Toronto's temporary 2020-21 home base in Tampa.
- The Clippers' move to Intuit Dome for 2024-25.
- Neutral/global regular-season games in Mexico City, Paris, and Las Vegas.

Nine neutral/global games are geocoded to the actual host venue. They remain in travel-burden calculations but are excluded from the primary home-vs-away regression because ordinary home-court status is not comparable.

## Schedule Friction Index

For every team-game, six pre-game exposures are calculated:

1. Log travel distance since the previous game
2. Absolute time-zone shift
3. Rest deficit
4. Games played in the previous seven days
5. Consecutive road-game streak
6. Positive altitude gain

Each component is standardized within season. SFI is the equal-weighted mean of the standardized components.

Game outcomes are never used to construct the index.

## Primary model

```text
home margin ~ relative SFI
            + pre-game 10-game form differential
            + season fixed effects
            + home-team fixed effects
            + away-team fixed effects
```

- One row per non-neutral game
- HC3 robust standard errors
- Separate binomial model for home-win probability
- Early-season games without sufficient lagged-form history are excluded from the main regression

## Reproducibility

Run:

```bash
pip install -r requirements.txt
python src/analysis.py
python src/build_assets.py
```

The GitHub Actions workflow runs the same build automatically and commits the generated outputs and figures.
