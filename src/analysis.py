from __future__ import annotations
import io, json, math
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd, requests
import statsmodels.formula.api as smf
import statsmodels.api as sm

YEARS=[2021,2022,2023,2024,2025]
LABELS={2021:"2020-21",2022:"2021-22",2023:"2022-23",2024:"2023-24",2025:"2024-25"}
BASE="https://raw.githubusercontent.com/llimllib/nba_data/main/data/gamelog_{year}.parquet"
OUT=Path("outputs"); OUT.mkdir(parents=True, exist_ok=True)
RAW=Path("data/raw"); RAW.mkdir(parents=True, exist_ok=True)

NEUTRAL_GAMES={
 "0022200439":(19.4966,-99.1754,2240,"America/Mexico_City","Arena CDMX"),
 "0022200678":(48.8386,2.3786,35,"Europe/Paris","Accor Arena"),
 "0022300172":(19.4966,-99.1754,2240,"America/Mexico_City","Arena CDMX"),
 "0022300527":(48.8386,2.3786,35,"Europe/Paris","Accor Arena"),
 "0022400147":(19.4966,-99.1754,2240,"America/Mexico_City","Arena CDMX"),
 "0022400621":(48.8386,2.3786,35,"Europe/Paris","Accor Arena"),
 "0022400633":(48.8386,2.3786,35,"Europe/Paris","Accor Arena"),
 "0022401229":(36.1029,-115.1784,620,"America/Los_Angeles","T-Mobile Arena"),
 "0022401230":(36.1029,-115.1784,620,"America/Los_Angeles","T-Mobile Arena"),
}

VEN="""team,latitude,longitude,elevation_m,timezone,valid_from,valid_to
ATL,33.7573,-84.3963,320,America/New_York,2020-12-01,2025-06-30
BOS,42.3662,-71.0621,6,America/New_York,2020-12-01,2025-06-30
BKN,40.6826,-73.9754,10,America/New_York,2020-12-01,2025-06-30
CHA,35.2251,-80.8392,229,America/New_York,2020-12-01,2025-06-30
CHI,41.8807,-87.6742,181,America/Chicago,2020-12-01,2025-06-30
CLE,41.4965,-81.6882,199,America/New_York,2020-12-01,2025-06-30
DAL,32.7905,-96.8103,131,America/Chicago,2020-12-01,2025-06-30
DEN,39.7487,-105.0077,1580,America/Denver,2020-12-01,2025-06-30
DET,42.3411,-83.0553,183,America/Detroit,2020-12-01,2025-06-30
GSW,37.7680,-122.3877,4,America/Los_Angeles,2020-12-01,2025-06-30
HOU,29.7508,-95.3621,15,America/Chicago,2020-12-01,2025-06-30
IND,39.7640,-86.1555,218,America/Indiana/Indianapolis,2020-12-01,2025-06-30
LAC,34.0430,-118.2673,71,America/Los_Angeles,2020-12-01,2024-06-30
LAC,33.9459,-118.3392,32,America/Los_Angeles,2024-07-01,2025-06-30
LAL,34.0430,-118.2673,71,America/Los_Angeles,2020-12-01,2025-06-30
MEM,35.1382,-90.0505,85,America/Chicago,2020-12-01,2025-06-30
MIA,25.7814,-80.1870,2,America/New_York,2020-12-01,2025-06-30
MIL,43.0451,-87.9172,188,America/Chicago,2020-12-01,2025-06-30
MIN,44.9795,-93.2760,253,America/Chicago,2020-12-01,2025-06-30
NOP,29.9490,-90.0821,-2,America/Chicago,2020-12-01,2025-06-30
NYK,40.7505,-73.9934,10,America/New_York,2020-12-01,2025-06-30
OKC,35.4634,-97.5151,366,America/Chicago,2020-12-01,2025-06-30
ORL,28.5392,-81.3839,30,America/New_York,2020-12-01,2025-06-30
PHI,39.9012,-75.1720,12,America/New_York,2020-12-01,2025-06-30
PHX,33.4457,-112.0712,331,America/Phoenix,2020-12-01,2025-06-30
POR,45.5316,-122.6668,15,America/Los_Angeles,2020-12-01,2025-06-30
SAC,38.5802,-121.4997,9,America/Los_Angeles,2020-12-01,2025-06-30
SAS,29.4269,-98.4375,198,America/Chicago,2020-12-01,2025-06-30
TOR,27.9427,-82.4518,3,America/New_York,2020-12-01,2021-06-30
TOR,43.6435,-79.3791,76,America/Toronto,2021-07-01,2025-06-30
UTA,40.7683,-111.9011,1300,America/Denver,2020-12-01,2025-06-30
WAS,38.8981,-77.0209,15,America/New_York,2020-12-01,2025-06-30
"""

def hv(a,b,c,d):
    r=6371.0088; p1=np.radians(a); p2=np.radians(c)
    x=np.sin(np.radians(c-a)/2)**2+np.cos(p1)*np.cos(p2)*np.sin(np.radians(d-b)/2)**2
    return 2*r*np.arcsin(np.sqrt(x))

def voff(tz,dt):
    z=ZoneInfo(tz)
    return datetime.combine(dt.date(),time(12),tzinfo=z).utcoffset().total_seconds()/3600

def venue(team,date,v):
    q=v[(v.team==team)&(v.valid_from<=date)&(v.valid_to>=date)]
    if q.empty: raise ValueError(f"venue missing {team} {date}")
    return q.iloc[-1]

frames=[]
for y in YEARS:
    p=RAW/f"gamelog_{y}.parquet"
    if not p.exists():
        u=BASE.format(year=y); print("GET",u,flush=True)
        r=requests.get(u,timeout=120); r.raise_for_status(); p.write_bytes(r.content)
    x=pd.read_parquet(p); x["season"]=LABELS[y]; frames.append(x)
df=pd.concat(frames,ignore_index=True); df.columns=[c.lower() for c in df.columns]
print("SOURCE COLUMNS",df.columns.tolist(),flush=True)
df["game_date"]=pd.to_datetime(df.game_date)
gid=df.game_id.astype(str).str.zfill(10); m=gid.str.startswith("002")
if m.sum()>1000: df=df[m].copy()
df["gid_norm"]=df.game_id.astype(str).str.zfill(10)
df["neutral_site"]=df.gid_norm.isin(NEUTRAL_GAMES).astype(int)
df["is_home"]=df.matchup.str.contains(r"vs\.",regex=True).astype(int)
df["opponent"]=df.matchup.str.split().str[-1]
df["venue_team"]=np.where(df.is_home.eq(1),df.team_abbreviation,df.opponent)

v=pd.read_csv(io.StringIO(VEN),parse_dates=["valid_from","valid_to"])
vr=[]; hr=[]
for gid,vt,tm,dt in df[["gid_norm","venue_team","team_abbreviation","game_date"]].itertuples(index=False):
    h=venue(tm,dt,v)
    if gid in NEUTRAL_GAMES:
        lat,lon,elev,tz,_=NEUTRAL_GAMES[gid]
        vr.append((lat,lon,elev,tz))
    else:
        a=venue(vt,dt,v)
        vr.append((a.latitude,a.longitude,a.elevation_m,a.timezone))
    hr.append((h.latitude,h.longitude,h.elevation_m,h.timezone))
df[["lat","lon","elevation_m","timezone"]]=pd.DataFrame(vr,index=df.index)
df[["home_lat","home_lon","home_elevation_m","home_timezone"]]=pd.DataFrame(hr,index=df.index)
df=df.sort_values(["season","team_abbreviation","game_date","game_id"]).reset_index(drop=True)
g=df.groupby(["season","team_abbreviation"],group_keys=False)
df["prev_date"]=g.game_date.shift(); df["gap"]=(df.game_date-df.prev_date).dt.days
df["rest_days"]=(df.gap-1).clip(lower=0); df["back_to_back"]=df.rest_days.eq(0).astype(int)
for c in ["lat","lon","elevation_m","timezone"]: df["prev_"+c]=g[c].shift()
reset=df.prev_date.isna()|df.gap.gt(4)
df.loc[reset,"prev_lat"]=df.loc[reset,"home_lat"]; df.loc[reset,"prev_lon"]=df.loc[reset,"home_lon"]
df.loc[reset,"prev_elevation_m"]=df.loc[reset,"home_elevation_m"]; df.loc[reset,"prev_timezone"]=df.loc[reset,"home_timezone"]
df["travel_km"]=hv(df.prev_lat,df.prev_lon,df.lat,df.lon)
df["altitude_gain_m"]=(df.elevation_m-df.prev_elevation_m).clip(lower=0)
df["tz"]= [voff(t,d) for t,d in zip(df.timezone,df.game_date)]
df["prev_tz"]=[voff(t,d) for t,d in zip(df.prev_timezone,df.game_date)]
df["timezone_shift_hours"]=df.tz-df.prev_tz; df["abs_timezone_shift"]=df.timezone_shift_hours.abs()

st=[]
for _,q in df.groupby(["season","team_abbreviation"],sort=False):
    s=0
    for h in q.is_home:
        s=0 if h else s+1; st.append(s)
df["road_streak"]=st

den=pd.Series(index=df.index,dtype=float)
for _,idx in df.groupby(["season","team_abbreviation"]).groups.items():
    q=df.loc[idx,["game_date"]].sort_values("game_date"); dates=q.game_date.to_numpy(dtype="datetime64[D]"); vals=[]
    for i,d in enumerate(dates):
        z=dates[:i+1]; vals.append(int(((z>=d-np.timedelta64(6,"D"))&(z<=d)).sum()))
    den.loc[q.index]=vals
df["games_last_7d"]=den.astype(int)
df["win"]=df.wl.eq("W").astype(int); df["point_diff"]=pd.to_numeric(df.plus_minus,errors="coerce")
df["team_form_10"]=df.groupby(["season","team_abbreviation"]).win.transform(lambda s:s.shift(1).rolling(10,min_periods=5).mean())

df["rest_deficit"]=(2-df.rest_days.fillna(2)).clip(0,2)
df["log_travel_km"]=np.log1p(df.travel_km); df["altitude_gain_km"]=df.altitude_gain_m/1000
cols=["log_travel_km","abs_timezone_shift","rest_deficit","games_last_7d","road_streak","altitude_gain_km"]; zs=[]
for c in cols:
    n="z_"+c
    df[n]=df.groupby("season")[c].transform(lambda x:(x-x.mean())/(x.std(ddof=0) if x.std(ddof=0) else 1))
    zs.append(n)
df["sfi"]=df[zs].mean(axis=1); df["sfi_pct"]=df.groupby("season").sfi.rank(pct=True)*100

keep=["game_id","season","game_date","team_abbreviation","sfi","sfi_pct","travel_km","abs_timezone_shift","back_to_back","games_last_7d","road_streak","altitude_gain_m","team_form_10","point_diff","win"]
model_rows=df[df.neutral_site.eq(0)].copy()
h=model_rows[model_rows.is_home.eq(1)][keep].copy(); a=model_rows[model_rows.is_home.eq(0)][keep].copy()
h=h.rename(columns={c:"home_"+c for c in keep if c not in ["game_id","season"]})
a=a.rename(columns={c:"away_"+c for c in keep if c not in ["game_id","season"]})
gm=h.merge(a,on=["game_id","season"],validate="one_to_one")
gm["game_date"]=gm["home_game_date"]
gm["home_margin"]=gm.home_point_diff; gm["home_win"]=gm.home_win.astype(int)
gm["friction_diff"]=gm.home_sfi-gm.away_sfi
gm["friction_pct_diff"]=gm.home_sfi_pct-gm.away_sfi_pct
gm["strength_diff"]=gm.home_team_form_10-gm.away_team_form_10

expected={"2020-21":1080,"2021-22":1230,"2022-23":1230,"2023-24":1230,"2024-25":1230}
audit=[]
for s,n in expected.items():
    games=int(df.loc[df.season.eq(s),"game_id"].nunique())
    audit.append({"season":s,"games":games,"expected":n,"pass":games==n})
aud=pd.DataFrame(audit); aud.to_csv(OUT/"audit.csv",index=False); print(aud.to_string(index=False),flush=True)

mod=gm.dropna(subset=["home_margin","friction_diff","strength_diff"]).copy()
f="home_margin ~ friction_diff + strength_diff + C(season) + C(home_team_abbreviation) + C(away_team_abbreviation)"
ols=smf.ols(f,data=mod).fit(cov_type="HC3")
logit=smf.glm(f.replace("home_margin","home_win"),data=mod,family=sm.families.Binomial()).fit(cov_type="HC3")

coef=float(ols.params["friction_diff"]); p=float(ols.pvalues["friction_diff"]); ci=ols.conf_int().loc["friction_diff"].tolist()
lc=float(logit.params["friction_diff"]); lp=float(logit.pvalues["friction_diff"]); orci=np.exp(logit.conf_int().loc["friction_diff"]).tolist()
m1=mod.copy(); m1["friction_diff"]=m1.friction_diff+1
ame=float((logit.predict(m1)-logit.predict(mod)).mean())

road=df[(df.is_home.eq(0)) & (df.neutral_site.eq(0))].copy()
road["decile"]=pd.qcut(road.sfi_pct,10,labels=False,duplicates="drop")+1
dec=road.groupby("decile").agg(games=("game_id","size"),win_pct=("win","mean"),avg_margin=("point_diff","mean"),avg_travel_km=("travel_km","mean")).reset_index()
team=df.groupby("team_abbreviation").agg(games=("game_id","size"),total_travel_km=("travel_km","sum"),avg_friction_pct=("sfi_pct","mean"),back_to_backs=("back_to_back","sum"),win_pct=("win","mean"),avg_margin=("point_diff","mean")).reset_index().sort_values("avg_friction_pct",ascending=False)

result={
 "games":int(df.game_id.nunique()),"non_neutral_paired_games":int(gm.game_id.nunique()),"neutral_games":int(df.loc[df.neutral_site.eq(1),"game_id"].nunique()),"team_game_rows":int(len(df)),"model_games":int(len(mod)),
 "ols_coef":coef,"ols_p":p,"ols_ci":ci,
 "logit_odds_ratio":float(np.exp(lc)),"logit_p":lp,"logit_or_ci":orci,"avg_marginal_win_prob_change":ame,
 "road_low_decile":dec.iloc[0].to_dict(),"road_high_decile":dec.iloc[-1].to_dict(),
 "top_friction_teams":team.head(10).to_dict("records")
}
(OUT/"findings.json").write_text(json.dumps(result,indent=2))
dec.to_csv(OUT/"road_deciles.csv",index=False); team.to_csv(OUT/"team_burden.csv",index=False)
mod[["game_id","season","game_date","home_team_abbreviation","away_team_abbreviation","home_margin","home_win","friction_diff","friction_pct_diff","strength_diff"]].to_csv(OUT/"model_games.csv",index=False)
(OUT/"ols.txt").write_text(ols.summary().as_text()); (OUT/"logit.txt").write_text(logit.summary().as_text())
print("RESULT_JSON",json.dumps(result),flush=True)
