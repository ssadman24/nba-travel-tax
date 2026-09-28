# Methodology

This project treats the NBA schedule as a spatial exposure problem rather than a direct winner-prediction task.

The Schedule Friction Index is constructed only from pre-game conditions: modeled travel distance, absolute time-zone change, rest deficit, seven-day game density, consecutive road games, and positive altitude gain. Components are standardized within season and equally weighted.

The primary game-level model compares the home team's SFI with the away team's SFI in the same matchup while controlling for recent 10-game form, season fixed effects, and team fixed effects. Neutral-site games are retained in travel construction but excluded from the home-vs-away regression.

See data/DATA_LOG.md and src/analysis.py for the complete reproducible implementation.
