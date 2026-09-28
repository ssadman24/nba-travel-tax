from pathlib import Path
import json
import html

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FIG = ROOT / "figures"
DATA = ROOT / "data"
DASH = ROOT / "dashboard"
for p in (FIG, DATA, DASH):
    p.mkdir(parents=True, exist_ok=True)

ARENAS = {
    "ATL": (33.7573,-84.3963,"State Farm Arena","Atlanta"),
    "BOS": (42.3662,-71.0621,"TD Garden","Boston"),
    "BKN": (40.6826,-73.9754,"Barclays Center","Brooklyn"),
    "CHA": (35.2251,-80.8392,"Spectrum Center","Charlotte"),
    "CHI": (41.8807,-87.6742,"United Center","Chicago"),
    "CLE": (41.4965,-81.6882,"Rocket Arena","Cleveland"),
    "DAL": (32.7905,-96.8103,"American Airlines Center","Dallas"),
    "DEN": (39.7487,-105.0077,"Ball Arena","Denver"),
    "DET": (42.3411,-83.0553,"Little Caesars Arena","Detroit"),
    "GSW": (37.7680,-122.3877,"Chase Center","San Francisco"),
    "HOU": (29.7508,-95.3621,"Toyota Center","Houston"),
    "IND": (39.7640,-86.1555,"Gainbridge Fieldhouse","Indianapolis"),
    "LAC": (33.9459,-118.3392,"Intuit Dome","Inglewood"),
    "LAL": (34.0430,-118.2673,"Crypto.com Arena","Los Angeles"),
    "MEM": (35.1382,-90.0505,"FedExForum","Memphis"),
    "MIA": (25.7814,-80.1870,"Kaseya Center","Miami"),
    "MIL": (43.0451,-87.9172,"Fiserv Forum","Milwaukee"),
    "MIN": (44.9795,-93.2760,"Target Center","Minneapolis"),
    "NOP": (29.9490,-90.0821,"Smoothie King Center","New Orleans"),
    "NYK": (40.7505,-73.9934,"Madison Square Garden","New York"),
    "OKC": (35.4634,-97.5151,"Paycom Center","Oklahoma City"),
    "ORL": (28.5392,-81.3839,"Kia Center","Orlando"),
    "PHI": (39.9012,-75.1720,"Wells Fargo Center","Philadelphia"),
    "PHX": (33.4457,-112.0712,"Mortgage Matchup Center","Phoenix"),
    "POR": (45.5316,-122.6668,"Moda Center","Portland"),
    "SAC": (38.5802,-121.4997,"Golden 1 Center","Sacramento"),
    "SAS": (29.4269,-98.4375,"Frost Bank Center","San Antonio"),
    "TOR": (43.6435,-79.3791,"Scotiabank Arena","Toronto"),
    "UTA": (40.7683,-111.9011,"Delta Center","Salt Lake City"),
    "WAS": (38.8981,-77.0209,"Capital One Arena","Washington"),
}

teams = pd.read_csv(OUT / "team_burden.csv")
findings = json.loads((OUT / "findings.json").read_text())
road = pd.read_csv(OUT / "road_deciles.csv")

arena = pd.DataFrame([
    {"team_abbreviation": team, "latitude": v[0], "longitude": v[1], "arena": v[2], "city": v[3]}
    for team, v in ARENAS.items()
])
arena = arena.merge(teams, on="team_abbreviation", how="left")
arena.to_csv(DATA / "arena_locations.csv", index=False)

# Static recruiter-facing map for the README.
geo_url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
geo = requests.get(geo_url, timeout=60).json()
fig, ax = plt.subplots(figsize=(11, 6.8))
for feat in geo["features"]:
    name = feat["properties"].get("ADMIN")
    if name not in {"United States of America", "Canada", "Mexico"}:
        continue
    geom = feat["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        ring = poly[0]
        patch = Polygon(ring, closed=True, facecolor="0.94", edgecolor="0.65", linewidth=0.6)
        ax.add_patch(patch)

sizes = 25 + (arena["total_travel_km"] - arena["total_travel_km"].min()) / (
    arena["total_travel_km"].max() - arena["total_travel_km"].min()
) * 85
sc = ax.scatter(
    arena["longitude"], arena["latitude"],
    c=arena["avg_friction_pct"], s=sizes,
    cmap="viridis", edgecolor="black", linewidth=0.35, zorder=3
)
for _, r in arena.iterrows():
    ax.text(r["longitude"] + 0.5, r["latitude"] + 0.25, r["team_abbreviation"], fontsize=7, zorder=4)
ax.set_xlim(-128, -65)
ax.set_ylim(23, 51)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("NBA arena geography and five-season schedule friction")
cb = fig.colorbar(sc, ax=ax, shrink=0.78)
cb.set_label("Average SFI percentile")
ax.grid(alpha=0.12)
fig.tight_layout()
fig.savefig(FIG / "arena_geography.png", dpi=200, bbox_inches="tight")
fig.savefig(FIG / "arena_geography.svg", bbox_inches="tight")
plt.close(fig)

markers = arena.to_dict("records")
road_rows = road.to_dict("records")

dashboard_html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NBA Travel Tax — Schedule Friction Dashboard</title>
<meta name="description" content="Five-season geospatial analysis of 6,000 NBA games examining how travel, time zones, rest, schedule density and altitude relate to performance.">
<meta property="og:type" content="website">
<meta property="og:title" content="NBA Travel Tax — Interactive Dashboard">
<meta property="og:description" content="Five-season geospatial analysis of 6,000 NBA games examining how schedule friction relates to performance.">
<meta property="og:url" content="https://ssadman24.github.io/nba-travel-tax/">
<meta property="og:image" content="https://raw.githubusercontent.com/ssadman24/nba-travel-tax/main/figures/arena_geography.png">
<meta property="og:image:alt" content="Map of NBA arena geography and schedule friction">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
:root{--bg:#0b1020;--card:#141b2d;--muted:#97a3b6;--text:#f4f7fb;--line:#28324a;--accent:#7dd3fc}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Arial}
main{max-width:1220px;margin:auto;padding:34px 22px 50px} h1{font-size:36px;margin:0 0 6px}.sub{color:var(--muted);margin-bottom:24px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}
.kpi{font-size:27px;font-weight:750}.label{font-size:12px;color:var(--muted);margin-top:5px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;margin-top:14px}.panel h2{font-size:17px;margin:0 0 12px}
#map{height:530px;border-radius:12px}.charts{display:grid;grid-template-columns:1fr 1fr;gap:14px}.chart{height:390px}
.note{font-size:13px;line-height:1.55;color:var(--muted)} a{color:var(--accent)}
@media(max-width:820px){.grid{grid-template-columns:1fr 1fr}.charts{grid-template-columns:1fr}h1{font-size:29px}}
</style>
</head>
<body><main>
<h1>Travel Tax: NBA Schedule Friction</h1>
<div class="sub">Five-season geospatial analysis · 2020-21 through 2024-25 · Samir Sadman</div>
<div class="grid">
  <div class="card"><div class="kpi" id="games"></div><div class="label">regular-season games</div></div>
  <div class="card"><div class="kpi" id="rows"></div><div class="label">team-game observations</div></div>
  <div class="card"><div class="kpi" id="margin"></div><div class="label">margin effect / +1 relative SFI</div></div>
  <div class="card"><div class="kpi" id="sdmargin"></div><div class="label">margin effect / +1 SD relative SFI</div></div>
</div>
<div class="panel"><h2>Arena geography & schedule burden</h2><div id="map"></div></div>
<div class="charts">
  <div class="panel"><h2>Road performance by friction decile</h2><div id="road" class="chart"></div></div>
  <div class="panel"><h2>Travel burden vs. schedule friction</h2><div id="scatter" class="chart"></div></div>
</div>
<div class="panel note">
<b>Inference.</b> Primary coefficient uses HC3 robust standard errors; a two-way clustered robustness check by home and away team is reported in the repository. 
The analysis is observational and does not establish that schedule fatigue causes a specific game result.
<br><br><a href="https://github.com/ssadman24/nba-travel-tax">View source, methodology, model outputs and reproducibility workflow on GitHub</a>.
</div>
</main>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<script>
const findings = __FINDINGS__;
const arenas = __ARENAS__;
const road = __ROAD__;
document.getElementById("games").textContent = findings.games.toLocaleString();
document.getElementById("rows").textContent = findings.team_game_rows.toLocaleString();
document.getElementById("margin").textContent = findings.ols_coef.toFixed(2) + " pts";
document.getElementById("sdmargin").textContent = findings.ols_1sd_effect.toFixed(2) + " pts";

const map = L.map("map", {scrollWheelZoom:false}).setView([38.5,-96],4);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom:19, attribution:"&copy; OpenStreetMap contributors"
}).addTo(map);

function markerColor(v){
  const t=Math.max(0,Math.min(1,(v-35)/30));
  const h=220-(170*t);
  return "hsl("+h+",75%,52%)";
}
arenas.forEach(r=>{
  const radius=6 + (r.total_travel_km-300000)/90000*6;
  L.circleMarker([r.latitude,r.longitude],{
    radius:Math.max(6,Math.min(13,radius)),color:"#0b1020",weight:1,
    fillColor:markerColor(r.avg_friction_pct),fillOpacity:.9
  }).addTo(map).bindPopup(
    "<b>"+r.team_abbreviation+" — "+r.arena+"</b><br>"+r.city+
    "<br>Avg SFI percentile: "+r.avg_friction_pct.toFixed(1)+
    "<br>Modeled five-year travel: "+Math.round(r.total_travel_km).toLocaleString()+" km"+
    "<br>Back-to-backs: "+r.back_to_backs
  );
});

const common={paper_bgcolor:"#141b2d",plot_bgcolor:"#141b2d",font:{color:"#dce5f2"},margin:{l:58,r:20,t:20,b:50}};
Plotly.newPlot("road",[{
  x:road.map(d=>d.decile),y:road.map(d=>d.avg_margin),mode:"lines+markers",
  line:{width:3,color:"#7dd3fc"},marker:{size:8}
}],Object.assign({},common,{xaxis:{title:"SFI decile",gridcolor:"#28324a"},yaxis:{title:"Average point differential",gridcolor:"#28324a"}}),{displayModeBar:false,responsive:true});

Plotly.newPlot("scatter",[{
  x:arenas.map(d=>d.total_travel_km),y:arenas.map(d=>d.avg_friction_pct),
  text:arenas.map(d=>d.team_abbreviation),mode:"markers+text",textposition:"top center",
  marker:{size:arenas.map(d=>8+d.back_to_backs/10),color:arenas.map(d=>d.avg_friction_pct),colorscale:"Viridis",showscale:true,colorbar:{title:"SFI pct."}},
  hovertemplate:"%{text}<br>Travel: %{x:,.0f} km<br>SFI pct.: %{y:.1f}<extra></extra>"
}],Object.assign({},common,{xaxis:{title:"Modeled five-year travel (km)",gridcolor:"#28324a"},yaxis:{title:"Average SFI percentile",gridcolor:"#28324a"}}),{displayModeBar:false,responsive:true});
</script></body></html>"""

dashboard_html = dashboard_html.replace("__FINDINGS__", json.dumps(findings))
dashboard_html = dashboard_html.replace("__ARENAS__", json.dumps(markers))
dashboard_html = dashboard_html.replace("__ROAD__", json.dumps(road_rows))
(DASH / "index.html").write_text(dashboard_html)
print("Geospatial assets and live dashboard built")
