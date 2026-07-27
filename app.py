import glob, json, html, os
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Diablos Analytics — Lineups", layout="wide", page_icon="🔴")
COLORS = {"DRM": "#e01023", "AGS": "#e3a400"}
TNAME = {"DRM": "DIABLOS ROJOS", "AGS": "PANTERAS"}
MIN_FLOOR = 3.0
BOX = ['pts','fgm','fga','tpm','tpa','ftm','fta','orb','drb','ast','tov','stl','blk']

@st.cache_data
def load():
    seen, files = set(), []
    for f in glob.glob("**/*", recursive=True):
        if f.lower().endswith(".csv"):
            b = os.path.basename(f).lower()
            if b not in seen:
                seen.add(b); files.append(f)
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True) if files else pd.DataFrame()
    players = {}
    for f in glob.glob("**/*", recursive=True):
        if not os.path.isfile(f) or f.lower().endswith((".csv", ".py", ".toml", ".md", ".txt")):
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
            if isinstance(d, dict) and any(k in d for k in ("DRM", "AGS")):
                players = d; break
        except Exception:
            pass
    return df, players

df, PLAYERS = load()
if not df.empty:
    df = df[df["team_code"] == "DRM"].reset_index(drop=True)
if df.empty:
    st.warning("No data yet. Upload a game CSV to the repo."); st.stop()
if "seconds" not in df.columns:
    df["seconds"] = df["minutes"] * 60
df["seconds"] = df["seconds"].fillna(df["minutes"] * 60).round().astype(int)
for c in BOX + ["opp_"+c for c in BOX]:
    if c not in df.columns: df[c] = np.nan
has_box_col = df["pts"].notna()
df["bsec"] = np.where(has_box_col, df["seconds"], 0)   # seconds from games that have full box score

st.markdown("<style>#MainMenu,header,footer{visibility:hidden}.stApp{background:#08090b}"
            ".block-container{padding-top:1rem;max-width:1400px}</style>", unsafe_allow_html=True)

team = "DRM"  # Diablos Rojos only
c1, c2, c3 = st.columns([1.25, 1.2, 1.1])
size = c1.radio("Lineup size", [2, 3, 4, 5], index=3, horizontal=True)
mode = c2.radio("Stats", ["Traditional", "Advanced"], index=0, horizontal=True)
view = c3.radio("View", ["Totals", "Per Game"], index=0, horizontal=True)
per_game = (view == "Per Game")
pl_team = PLAYERS.get(team, {})
acc = COLORS.get(team, "#e01023")

t = df[(df["team_code"] == team) & (df["size"] == size)].copy()
g = t.groupby("lineup")
agg = g.agg(
    GP=("date", lambda s: t.loc[s.index][t["pts"].notna()]["date"].nunique() if False else 0),
).reset_index()
# aggregate manually
sumcols = ["bsec", "plus_minus"] + BOX + ["opp_"+c for c in BOX]
A = t.groupby("lineup")[sumcols].sum(min_count=1).reset_index()
GP = t[t["pts"].notna()].groupby("lineup")["date"].nunique().reindex(A["lineup"]).fillna(0).astype(int).values
A["GP"] = GP
A = A[A["bsec"] >= MIN_FLOOR*60].reset_index(drop=True)

if A.empty:
    st.info("No lineups with full box-score stats yet for this selection (need games with play-by-play).")
    st.stop()

def sd(a, b):
    return (a / b) if (b not in (0, None) and not pd.isna(b) and b != 0) else None

def derive(r):
    o = {c: (0 if pd.isna(r[c]) else r[c]) for c in BOX}
    op = {c: (0 if pd.isna(r["opp_"+c]) else r["opp_"+c]) for c in BOX}
    mn = r["bsec"] / 60.0
    reb = o["orb"] + o["drb"]; oreb2 = op["orb"] + op["drb"]
    tmposs = o["fga"] + 0.475*o["fta"] - o["orb"] + o["tov"]
    opposs = op["fga"] + 0.475*op["fta"] - op["orb"] + op["tov"]
    def pct(a, b): 
        v = sd(a, b); return round(v*100, 1) if v is not None else None
    d = dict(
        GP=int(r["GP"]), MIN=round(mn, 1), PTS=int(o["pts"]),
        FGM=int(o["fgm"]), FGA=int(o["fga"]), FGp=pct(o["fgm"], o["fga"]),
        TPM=int(o["tpm"]), TPA=int(o["tpa"]), TPp=pct(o["tpm"], o["tpa"]),
        FTM=int(o["ftm"]), FTA=int(o["fta"]), FTp=pct(o["ftm"], o["fta"]),
        OREB=int(o["orb"]), DREB=int(o["drb"]), REB=int(reb),
        AST=int(o["ast"]), TOV=int(o["tov"]), STL=int(o["stl"]), BLK=int(o["blk"]),
        PM=int(r["plus_minus"]) if not pd.isna(r["plus_minus"]) else 0,
        ADJ36=round((r["plus_minus"]*36/mn), 1) if (mn>0 and not pd.isna(r["plus_minus"])) else None,
        POSS=round((tmposs+opposs)/2),
        ORTG=round(sd(o["pts"]*100, tmposs), 1) if sd(o["pts"], tmposs) is not None else None,
        DRTG=round(sd(op["pts"]*100, opposs), 1) if sd(op["pts"], opposs) is not None else None,
        ASTp=pct(o["ast"], o["fgm"]), ASTTO=round(sd(o["ast"], o["tov"]), 2) if sd(o["ast"], o["tov"]) is not None else None,
        ASTr=pct(o["ast"], o["fga"]+0.475*o["fta"]+o["ast"]+o["tov"]),
        OREBp=pct(o["orb"], o["orb"]+op["drb"]), DREBp=pct(o["drb"], o["drb"]+op["orb"]),
        REBp=pct(reb, reb+oreb2), TOr=pct(o["tov"], o["fga"]+0.475*o["fta"]+o["ast"]+o["tov"]),
        eFG=pct(o["fgm"]+0.5*o["tpm"], o["fga"]), TS=pct(o["pts"], 2*(o["fga"]+0.44*o["fta"])),
        PACE=round(sd(40*(tmposs+opposs)/2, mn), 1) if sd(1, mn) is not None else None,
    )
    d["NETRTG"] = round(d["ORTG"]-d["DRTG"], 1) if (d["ORTG"] is not None and d["DRTG"] is not None) else None
    d["lineup"] = r["lineup"]
    return d

recs = [derive(r) for _, r in A.iterrows()]
COUNT = {"PTS","FGM","FGA","TPM","TPA","FTM","FTA","OREB","DREB","REB","AST","TOV","STL","BLK","PM","POSS","MIN"}
if per_game:
    for d in recs:
        gp = d["GP"] or 1
        for k in COUNT:
            if d.get(k) is not None:
                d[k] = round(d[k] / gp, 1)

def circle(label):
    p = pl_team.get(label, {"num": label.split(" ", 1)[0].lstrip("#"),
                            "sn": label.split(" ", 1)[-1].upper(), "img": None})
    cls = ("im"+str(p["num"])) if p.get("img") else ""
    return f'<span class="ph {cls}"></span><span class="pn">{str(p["num"])}</span>'

def lucell(lineup):
    return "".join(f'<span class="pc">{circle(l)}</span>' for l in lineup.split(" / "))

TRAD = [("GP","GP","i"),("MIN","MIN","1"),("PM","+/-","pm"),("ADJ36","ADJ36","1"),("PTS","PTS","i"),
        ("FGM","FGM","i"),("FGA","FGA","i"),("FGp","FG%","p"),("TPM","3PM","i"),("TPA","3PA","i"),("TPp","3P%","p"),
        ("FTM","FTM","i"),("FTA","FTA","i"),("FTp","FT%","p"),("OREB","OREB","i"),("DREB","DREB","i"),("REB","REB","i"),
        ("AST","AST","i"),("TOV","TOV","i"),("STL","STL","i"),("BLK","BLK","i")]
ADV = [("GP","GP","i"),("MIN","MIN","1"),("POSS","POSS","i"),("ORTG","ORTG","1"),("DRTG","DRTG","1"),("NETRTG","NET","pm"),("ADJ36","ADJ36","1"),
       ("eFG","eFG%","p"),("TS","TS%","p"),("ASTp","AST%","p"),("ASTTO","AST/TO","2"),("ASTr","AST RATIO","1"),
       ("TOr","TO RATIO","1"),("OREBp","OREB%","p"),("DREBp","DREB%","p"),("REBp","REB%","p"),("PACE","PACE","1")]
base_cols = TRAD if mode == "Traditional" else ADV
CNT = {"PTS","FGM","FGA","TPM","TPA","FTM","FTA","OREB","DREB","REB","AST","TOV","STL","BLK","POSS"}
def _fmt(k, f):
    if per_game and k in CNT: return "1"
    if per_game and k == "PM": return "s1"
    return f
cols = [(k, l, _fmt(k, f)) for k, l, f in base_cols]

data = []
for d in recs:
    data.append({"lu": lucell(d["lineup"]), "v": {k: d[k] for k, _, _ in cols}})

im_css = "".join(".im%s{background-image:url(%s)}" % (p["num"], p["img"]) for p in pl_team.values() if p.get("img"))
coljson = json.dumps([{"k": k, "l": l, "f": f} for k, l, f in cols])
datajson = json.dumps(data, ensure_ascii=False)
defsort = "MIN"

STYLE = """
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:"Segoe UI",Arial,sans-serif}
body{background:transparent;overflow:hidden}
.hd{font-size:11px;letter-spacing:.3em;color:#8a929c;font-weight:700}
.tn{font-size:24px;font-weight:800;color:#e9ecef;border-bottom:3px solid ACC;display:inline-block;padding-bottom:3px;margin:3px 0 12px}
.scrollx{overflow:auto;max-height:MAXH;border:1px solid #1c2027;border-radius:14px;background:#0b0d10}
table{border-collapse:separate;border-spacing:0;width:100%;font-size:13px}
thead th{position:sticky;top:0;z-index:3;background:#12151b;color:#8a929c;font-size:10px;letter-spacing:.06em;font-weight:800;
  padding:10px 8px;text-align:center;cursor:pointer;white-space:nowrap;border-bottom:1px solid #232830;user-select:none}
thead th:hover{color:#e9ecef}
thead th.act{color:ACC}
th.lu,td.lu{position:sticky;left:0;z-index:2;background:#0f1216;text-align:left;min-width:270px;border-right:1px solid #232830}
thead th.lu{z-index:4}
tbody td{padding:8px;text-align:center;color:#dfe3e8;font-weight:600;white-space:nowrap;border-bottom:1px solid #161a20}
tbody tr:hover td{background:#12161c}
tbody tr:hover td.lu{background:#141821}
.rk{color:#5a6270;font-weight:800;padding-right:8px}
.luwrap{display:flex;align-items:center;gap:5px}
.pc{position:relative;display:inline-block;width:40px;text-align:center}
.ph{display:block;width:38px;height:38px;border-radius:50%;background-color:#15171b;box-shadow:0 0 0 2px ACC;background-size:cover;background-position:center top;margin:0 auto}
.pn{position:absolute;bottom:-2px;right:2px;background:#0c0c0e;box-shadow:0 0 0 1.5px ACC;color:#fff;font-size:8px;font-weight:800;border-radius:50%;width:15px;height:15px;line-height:15px;text-align:center}
.pos{color:#2fe08a}.neg{color:#ff5468}
.ar{font-size:8px}
</style>
""".replace("ACC", acc).replace("MAXH", "MAXHVAL")

SCRIPT = """
<script>
const COLS=__COLS__, DATA=__DATA__;
let key="__DEF__", dir=-1;
function fmt(v,f){ if(v===null||v===undefined) return "-";
  if(f==="pm"){const s=v>0?"+"+v:""+v; return '<span class="'+(v>0?"pos":(v<0?"neg":""))+'">'+s+'</span>';}
  if(f==="s1"){const n=(Math.round(v*10)/10).toFixed(1); const s=v>0?"+"+n:n; return '<span class="'+(v>0?"pos":(v<0?"neg":""))+'">'+s+'</span>';}
  if(f==="i") return v;
  if(f==="1") return (Math.round(v*10)/10).toFixed(1);
  if(f==="2") return (Math.round(v*100)/100).toFixed(2);
  if(f==="p") return (Math.round(v*10)/10).toFixed(1);
  return v; }
function render(){
  DATA.sort((a,b)=>{const x=a.v[key],y=b.v[key];
    const xn=(x===null||x===undefined), yn=(y===null||y===undefined);
    if(xn&&yn)return 0; if(xn)return 1; if(yn)return -1; return dir*(x-y);});
  const th=COLS.map(c=>'<th class="'+(c.k===key?"act":"")+'" onclick="ss(\\''+c.k+'\\')">'+c.l+' <span class="ar">'+(c.k===key?(dir<0?"▼":"▲"):"")+'</span></th>').join('');
  document.getElementById("hd").innerHTML='<th class="lu">LINEUP</th>'+th;
  document.getElementById("tb").innerHTML=DATA.map((r,i)=>{
    const cells=COLS.map(c=>'<td>'+fmt(r.v[c.k],c.f)+'</td>').join('');
    return '<tr><td class="lu"><span class="luwrap"><span class="rk">'+(i+1)+'</span>'+r.lu+'</span></td>'+cells+'</tr>';}).join('');
}
function ss(k){ if(k===key)dir=-dir; else {key=k;dir=-1;} render(); }
render();
</script>
"""
TABLE = ('<div class="hd">LNBP · LINEUP EXPLORER · ' + mode.upper() + '</div>'
         '<div class="tn">' + TNAME.get(team, team) + '</div>'
         '<div class="scrollx"><table><thead><tr id="hd"></tr></thead><tbody id="tb"></tbody></table></div>')
maxh = min(120 + len(data)*54, 620)
block = (STYLE.replace("MAXHVAL", str(maxh)+"px") + "<style>" + im_css + "</style>" + TABLE
         + SCRIPT.replace("__COLS__", coljson).replace("__DATA__", datajson).replace("__DEF__", defsort))
components.html(block, height=maxh + 90, scrolling=False)
st.caption(f"{view} · counting stats accumulate across games (Per Game divides by GP; percentages & ratings are rate stats) · "
           "click any column header to sort · min 3 min together · ORTG/DRTG = points per 100 poss")
