import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).parent
teams = pd.read_csv(ROOT / "outputs" / "team_burden.csv")
road = pd.read_csv(ROOT / "outputs" / "road_deciles.csv")
arenas = pd.read_csv(ROOT / "data" / "arena_locations.csv")
findings = json.loads((ROOT / "outputs" / "findings.json").read_text())

st.set_page_config(page_title="NBA Travel Tax", layout="wide")
st.title("Travel Tax: NBA Schedule Friction")
st.caption("Five-season geospatial analysis | 2020-21 through 2024-25")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Regular-season games", f"{findings['games']:,}")
c2.metric("Team-game rows", f"{findings['team_game_rows']:,}")
c3.metric("Margin effect / +1 SFI", f"{findings['ols_coef']:.2f} pts")
c4.metric("Margin effect / +1 SD", f"{findings['ols_1sd_effect']:.2f} pts")

st.subheader("Arena geography & five-season schedule burden")
geo = px.scatter_geo(
    arenas,
    lat="latitude",
    lon="longitude",
    text="team_abbreviation",
    color="avg_friction_pct",
    size="total_travel_km",
    hover_name="team_abbreviation",
    hover_data={
        "arena": True,
        "city": True,
        "avg_friction_pct": ":.1f",
        "total_travel_km": ":,.0f",
        "back_to_backs": True,
        "latitude": False,
        "longitude": False,
    },
    scope="north america",
    labels={
        "avg_friction_pct": "Avg SFI percentile",
        "total_travel_km": "Modeled travel (km)",
        "back_to_backs": "Back-to-backs",
    },
)
geo.update_traces(textposition="top center")
geo.update_geos(showland=True, landcolor="rgb(235,238,242)", showlakes=True)
st.plotly_chart(geo, use_container_width=True)

st.subheader("Travel burden vs. schedule friction")
fig = px.scatter(
    teams,
    x="total_travel_km",
    y="avg_friction_pct",
    text="team_abbreviation",
    size="back_to_backs",
    hover_data=["win_pct", "avg_margin"],
    labels={
        "total_travel_km": "Modeled travel distance (km)",
        "avg_friction_pct": "Average SFI percentile",
        "back_to_backs": "Back-to-backs",
    },
)
fig.update_traces(textposition="top center")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Road-game performance by SFI decile")
road_plot = px.line(
    road,
    x="decile",
    y="avg_margin",
    markers=True,
    labels={"decile": "SFI decile", "avg_margin": "Average point differential"},
)
st.plotly_chart(road_plot, use_container_width=True)

st.subheader("Robustness")
st.write(
    f"Two-way clustered SE by home and away team: "
    f"{findings['clustered_se']:.3f}; p={findings['clustered_p']:.4g}. "
    f"A one-standard-deviation increase in relative SFI corresponds to "
    f"{findings['ols_1sd_effect']:.2f} points in adjusted margin and "
    f"{findings['avg_marginal_win_prob_change_1sd']*100:.1f} percentage points "
    f"in modeled win probability."
)

st.info(
    "Observational analysis: SFI uses pre-game schedule exposures only and "
    "does not use game outcomes to construct the index."
)
