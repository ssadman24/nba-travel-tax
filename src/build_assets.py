from pathlib import Path
import json

import matplotlib.pyplot as plt
import nbformat as nbf
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FIG = ROOT / "figures"
DOC = ROOT / "docs"
NB = ROOT / "notebooks"
for p in (FIG, DOC, NB):
    p.mkdir(parents=True, exist_ok=True)

findings = json.loads((OUT / "findings.json").read_text())
road = pd.read_csv(OUT / "road_deciles.csv")
teams = pd.read_csv(OUT / "team_burden.csv")

def save_both(fig, stem):
    fig.savefig(FIG / f"{stem}.png", dpi=200, bbox_inches="tight")
    fig.savefig(FIG / f"{stem}.svg", bbox_inches="tight")
    plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 5.4))
ax.plot(road["decile"], road["avg_margin"], marker="o", linewidth=2)
ax.axhline(0, linewidth=0.8)
ax.set_xlabel("Schedule Friction decile (road games)")
ax.set_ylabel("Average point differential")
ax.set_title("Road performance weakens at the highest schedule-friction levels")
ax.set_xticks(range(1, 11))
ax.grid(alpha=0.2)
fig.tight_layout()
save_both(fig, "road_friction_vs_margin")

coef = findings["ols_coef"]
lo, hi = findings["ols_ci"]
fig, ax = plt.subplots(figsize=(8.5, 4.4))
ax.errorbar([coef], [0], xerr=[[coef - lo], [hi - coef]], fmt="o", capsize=6)
ax.axvline(0, linewidth=0.8)
ax.set_yticks([0])
ax.set_yticklabels(["Relative Schedule Friction Index"])
ax.set_xlabel("Estimated change in home-team point margin")
ax.set_title("Adjusted association between relative schedule friction and margin")
ax.set_xlim(min(lo - 0.5, -2.5), max(hi + 0.5, 0.5))
fig.tight_layout()
save_both(fig, "primary_model_effect")

top = teams.sort_values("avg_friction_pct", ascending=False).head(12).sort_values("avg_friction_pct")
fig, ax = plt.subplots(figsize=(9, 6))
ax.barh(top["team_abbreviation"], top["avg_friction_pct"])
ax.set_xlabel("Five-season average SFI percentile")
ax.set_title("Teams with the highest average schedule friction, 2020-21 to 2024-25")
fig.tight_layout()
save_both(fig, "team_schedule_friction")

travel = teams.sort_values("total_travel_km", ascending=False).head(12).sort_values("total_travel_km")
fig, ax = plt.subplots(figsize=(9, 6))
ax.barh(travel["team_abbreviation"], travel["total_travel_km"] / 1000)
ax.set_xlabel("Modeled travel distance (thousand km)")
ax.set_title("Highest modeled travel burden across five NBA seasons")
fig.tight_layout()
save_both(fig, "team_travel_burden")

findings_md = f"""# Empirical Findings

## Headline result

Across **{findings['games']:,} NBA regular-season games** from 2020-21 through 2024-25, higher relative schedule burden is associated with weaker game performance after controlling for recent team form, season, and team fixed effects.

In the primary fixed-effects OLS model, a **+1 unit increase in the home team's Schedule Friction Index relative to its opponent** is associated with a **{findings['ols_coef']:.2f}-point change in home-team margin** (95% CI {findings['ols_ci'][0]:.2f} to {findings['ols_ci'][1]:.2f}; p={findings['ols_p']:.4g}).

The binomial model produces an odds ratio of **{findings['logit_odds_ratio']:.3f}** (95% CI {findings['logit_or_ci'][0]:.3f}-{findings['logit_or_ci'][1]:.3f}; p={findings['logit_p']:.4g}). Averaged across observed games, a +1 relative-SFI increase corresponds to about a **{abs(findings['avg_marginal_win_prob_change'])*100:.1f}-percentage-point decrease** in predicted home-win probability.

## Descriptive road-game contrast

Road teams in the lowest SFI decile:
- Win rate: {findings['road_low_decile']['win_pct']*100:.1f}%
- Average margin: {findings['road_low_decile']['avg_margin']:.2f}
- Average modeled travel: {findings['road_low_decile']['avg_travel_km']:.0f} km

Road teams in the highest SFI decile:
- Win rate: {findings['road_high_decile']['win_pct']*100:.1f}%
- Average margin: {findings['road_high_decile']['avg_margin']:.2f}
- Average modeled travel: {findings['road_high_decile']['avg_travel_km']:.0f} km

The high-friction road group won about {(findings['road_low_decile']['win_pct']-findings['road_high_decile']['win_pct'])*100:.1f} percentage points less often. This contrast is descriptive rather than causal.

## Interpretation

The evidence is consistent with schedule geography and recovery conditions having a measurable association with NBA game performance. The analysis remains observational and does not directly observe charter itineraries, player-specific sleep, injuries, lineup management, practice schedules, or other private team information.
"""
(OUT / "FINDINGS.md").write_text(findings_md)

nb = nbf.v4.new_notebook()
nb.cells = [
    nbf.v4.new_markdown_cell("# Travel Tax: NBA Schedule Friction & Competitive Equity\n\nFive-season geospatial study of 6,000 NBA regular-season games."),
    nbf.v4.new_markdown_cell("## Research question\nDoes relative pre-game schedule burden predict game performance after accounting for recent team form, season, and team effects?"),
    nbf.v4.new_markdown_cell("## Schedule Friction Index\nThe SFI combines travel distance, time-zone movement, rest deficit, seven-day game density, road streak, and altitude gain. All components are measured before the game and standardized within season."),
    nbf.v4.new_code_cell('''from pathlib import Path
import json
import pandas as pd

ROOT = Path("..")
findings = json.loads((ROOT/"outputs"/"findings.json").read_text())
road = pd.read_csv(ROOT/"outputs"/"road_deciles.csv")
teams = pd.read_csv(ROOT/"outputs"/"team_burden.csv")
findings'''),
    nbf.v4.new_markdown_cell(f"## Main result\nThe verified fixed-effects model estimates **{findings['ols_coef']:.2f} points** per +1 unit of relative SFI (95% CI {findings['ols_ci'][0]:.2f} to {findings['ols_ci'][1]:.2f}; p={findings['ols_p']:.4g}).\n\nThe average modeled change in win probability is **{findings['avg_marginal_win_prob_change']*100:.1f} percentage points**."),
    nbf.v4.new_code_cell('road[["decile","games","win_pct","avg_margin","avg_travel_km"]]'),
    nbf.v4.new_code_cell('teams.sort_values("avg_friction_pct", ascending=False).head(10)'),
    nbf.v4.new_markdown_cell("## Reproducibility\nThe full data-engineering and modeling pipeline is in src/analysis.py."),
]
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata["language_info"] = {"name": "python", "version": "3"}
nbf.write(nb, NB / "NBA_Travel_Tax_Findings.ipynb")

pdf_path = DOC / "NBA_Travel_Tax_Findings_Brief.pdf"
styles = getSampleStyleSheet()
doc = SimpleDocTemplate(
    str(pdf_path),
    pagesize=letter,
    rightMargin=0.65 * inch,
    leftMargin=0.65 * inch,
    topMargin=0.55 * inch,
    bottomMargin=0.55 * inch,
)
story = [
    Paragraph("Travel Tax: NBA Schedule Friction & Competitive Equity", styles["Title"]),
    Paragraph("Five-season geospatial analysis by Samir Sadman", styles["Heading2"]),
    Spacer(1, 8),
    Paragraph(
        f"Dataset: {findings['games']:,} NBA regular-season games / "
        f"{findings['team_game_rows']:,} team-game observations, 2020-21 through 2024-25.",
        styles["BodyText"],
    ),
    Spacer(1, 8),
    Paragraph(
        f"Primary result: +1 unit of relative Schedule Friction Index is associated "
        f"with a {findings['ols_coef']:.2f}-point change in home-team margin "
        f"(95% CI {findings['ols_ci'][0]:.2f} to {findings['ols_ci'][1]:.2f}; "
        f"p={findings['ols_p']:.4g}).",
        styles["BodyText"],
    ),
    Spacer(1, 8),
    Paragraph(
        f"Win-probability model: average "
        f"{findings['avg_marginal_win_prob_change']*100:.1f} percentage-point change "
        f"in predicted home-win probability per +1 relative-SFI unit.",
        styles["BodyText"],
    ),
    Spacer(1, 10),
    Paragraph("Schedule Friction Index components", styles["Heading2"]),
    Paragraph(
        "Log travel distance; absolute time-zone shift; rest deficit; games in the "
        "previous seven days; consecutive road-game streak; positive altitude gain. "
        "Components are standardized within season and outcomes are not used to construct the index.",
        styles["BodyText"],
    ),
    Spacer(1, 10),
    Paragraph("Primary specification", styles["Heading2"]),
    Paragraph(
        "home margin ~ relative SFI + pre-game 10-game form differential + season fixed "
        "effects + home-team fixed effects + away-team fixed effects; HC3 robust standard errors.",
        styles["BodyText"],
    ),
    Spacer(1, 10),
    Paragraph("Interpretation", styles["Heading2"]),
    Paragraph(
        "The results are observational. They are consistent with schedule geography and "
        "recovery burden having a measurable association with game performance, but they "
        "are not a causal estimate of fatigue.",
        styles["BodyText"],
    ),
]
doc.build(story)
print("Assets built")
