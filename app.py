import glob, json, html, os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Diablos Analytics — Lineups", layout="wide", page_icon="🔴")
COLORS = {"DRM": "#e01023", "AGS": "#e3a400"}
TNAME = {"DRM": "DIABLOS ROJOS", "AGS": "PANTERAS"}
MIN_FLOOR = 3.0

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
    if "seconds" not in df.columns:
        df["seconds"] = df["minutes"] * 60
    df["seconds"] = df["seconds"].fillna(df["minutes"] * 60).round().astype(int)

st.markdown("<style>#MainMenu,header,footer{visibility:hidden}.stApp{background:#08090b}"
            ".block-container{padding-top:1.1rem;max-width:1180px}</style>", unsafe_allow_html=True)

if df.empty:
    st.warning("No data yet. Upload a game CSV to the repo."); st.stop()

c1, c2 = st.columns([1.1, 1.9])
team = c1.selectbox("Team", sorted(df["team_code"].unique(), key=lambda t: 0 if t == "DRM" else 1),
                    format_func=lambda t: TNAME.get(t, t))
size = c2.radio("Size", [2, 3, 4, 5], index=3, horizontal=True)
pl_team = PLAYERS.get(team, {})
sel = st.multiselect("Filter by player (includes them all)", list(pl_team.keys()),
                     format_func=lambda l: pl_team[l]["sn"])
acc = COLORS.get(team, "#e01023")

t = df[(df["team_code"] == team) & (df["size"] == size)]
agg = (t.groupby("lineup", as_index=False)
        .agg(SEC=("seconds", "sum"), PM=("plus_minus", "sum")))
agg["MIN"] = agg["SEC"] / 60
agg = agg[agg["MIN"] >= MIN_FLOOR]
agg["PM36"] = (agg["PM"] * 2160 / agg["SEC"]).round(0).astype(int)
agg["MIN"] = agg["MIN"].round(1)
for lab in sel:
    agg = agg[agg["lineup"].str.contains(lab, regex=False)]

def circle(label):
    p = pl_team.get(label, {"num": label.split(" ", 1)[0].lstrip("#"),
                            "sn": label.split(" ", 1)[-1].upper(), "img": None})
    cls = ("im" + str(p["num"])) if p.get("img") else ""
    return ('<span class="pb"><span class="ring"><span class="ph ' + cls + '"></span>'
            '<span class="num">' + str(p["num"]) + '</span></span>'
            '<span class="pn">' + html.escape(p["sn"]) + '</span></span>')

rows = [{"c": "".join(circle(l) for l in r["lineup"].split(" / ")),
         "min": float(r["MIN"]), "pm": int(r["PM"]), "pm36": int(r["PM36"])}
        for _, r in agg.iterrows()]

im_css = "".join(".im%s{background-image:url(%s)}" % (p["num"], p["img"])
                 for p in pl_team.values() if p.get("img"))

STYLE = """
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:"Segoe UI",Arial,sans-serif}
body{background:transparent;overflow:hidden}
.hd{font-size:11px;letter-spacing:.32em;color:#8a929c;font-weight:700}
.tn{font-size:27px;font-weight:800;color:#e9ecef;border-bottom:3px solid ACC;display:inline-block;padding-bottom:4px;margin:3px 0 14px}
.hrow{display:flex;align-items:flex-end;gap:14px;padding:0 20px 8px 18px}
.hrow .rk{min-width:20px}
.htitle{flex:1;font-size:10px;letter-spacing:.18em;color:#6b7280;font-weight:700}
.hcol{width:78px;text-align:center;background:none;border:0;cursor:pointer;color:#8a929c;font-size:10px;letter-spacing:.1em;font-weight:800;padding:6px 2px;border-radius:8px}
.hcol:hover{color:#e9ecef;background:#14171c}
.hcol.act{color:ACC}
.hcol .ar{font-size:9px}
.panel{max-height:PANELPX;overflow-y:auto;padding:2px 6px 2px 0;display:flex;flex-direction:column;gap:9px}
.panel::-webkit-scrollbar{width:11px}
.panel::-webkit-scrollbar-track{background:#0b0d10;border-radius:8px}
.panel::-webkit-scrollbar-thumb{background:#333a45;border-radius:8px;border:2px solid #0b0d10}
.panel::-webkit-scrollbar-thumb:hover{background:#454e5c}
.unit{display:flex;align-items:center;gap:14px;background:linear-gradient(180deg,#101318,#0c0e12);border:1px solid #1c2027;border-radius:16px;padding:13px 14px}
.rk{font-size:15px;font-weight:800;color:#5a6270;min-width:20px;text-align:center}
.urow{display:flex;gap:11px;flex:1;justify-content:center}
.pb{display:flex;flex-direction:column;align-items:center;gap:6px;width:76px}
.ring{position:relative;border-radius:50%;width:66px;height:66px;background:#15171b;box-shadow:0 0 0 2.5px ACC}
.ph{position:absolute;inset:0;border-radius:50%;background-size:cover;background-position:center top}
.num{position:absolute;bottom:-3px;right:-3px;background:#0c0c0e;box-shadow:0 0 0 2px ACC;color:#fff;font-size:11px;font-weight:800;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center}
.pn{font-size:10px;font-weight:700;text-align:center;color:#cfd4da;line-height:1.1}
.mcol{width:78px;text-align:center;font-weight:800;font-size:20px}
.mcol small{display:block;font-size:8px;letter-spacing:.14em;color:#6b7280;font-weight:700;margin-top:2px}
.mmin{color:#e9ecef}
.pos{color:#2fe08a}.neg{color:#ff5468}.zero{color:#aab2bc}
IMCSS
</style>
""".replace("ACC", "%ACC%").replace("IMCSS", im_css).replace("PANELPX", "PANELVAL")

HTMLHEAD = ('<div class="hd">LNBP · LINEUP EXPLORER</div><div class="tn">TEAMNAME</div>'
            '<div class="hrow"><span class="rk"></span><span class="htitle">LINEUP</span>'
            '<button class="hcol" id="h-min" onclick="setSort(\'min\')">MIN <span class="ar" id="ar-min"></span></button>'
            '<button class="hcol" id="h-pm" onclick="setSort(\'pm\')">+/- <span class="ar" id="ar-pm"></span></button>'
            '<button class="hcol" id="h-pm36" onclick="setSort(\'pm36\')">ADJ36 <span class="ar" id="ar-pm36"></span></button>'
            '</div><div class="panel" id="panel"></div>')

SCRIPT = """
<script>
const DATA = __DATA__;
let key="min", dir=-1;
function fmt(x){return x>0?("+"+x):(""+x);}
function cl(x){return x>0?"pos":(x<0?"neg":"zero");}
function render(){
  DATA.sort((a,b)=> dir*(a[key]-b[key]) || (b.min-a.min));
  const p=document.getElementById("panel");
  p.innerHTML=DATA.map((r,i)=>
    '<div class="unit"><span class="rk">'+(i+1)+'</span>'+
    '<span class="urow">'+r.c+'</span>'+
    '<span class="mcol mmin">'+r.min+'<small>MIN</small></span>'+
    '<span class="mcol '+cl(r.pm)+'">'+fmt(r.pm)+'<small>+/-</small></span>'+
    '<span class="mcol '+cl(r.pm36)+'">'+fmt(r.pm36)+'<small>ADJ36</small></span></div>').join('');
  ["min","pm","pm36"].forEach(k=>{
    document.getElementById("h-"+k).classList.toggle("act", k===key);
    document.getElementById("ar-"+k).textContent = k===key ? (dir<0?"▼":"▲") : "";
  });
}
function setSort(k){ if(k===key){dir=-dir;} else {key=k; dir=-1;} render(); }
render();
</script>
"""
data_json = json.dumps(rows, ensure_ascii=False)
if rows:
    panel_px = min(len(rows) * 116, 520)
    block = (STYLE.replace("%ACC%", acc).replace("PANELVAL", str(panel_px) + "px")
             + HTMLHEAD.replace("TEAMNAME", TNAME.get(team, team))
             + SCRIPT.replace("__DATA__", data_json))
    height = 150 + panel_px
    components.html(block, height=height, scrolling=False)
else:
    st.info("No lineups match these filters (minimum 3 min together).")

st.caption("Click MIN · +/- · ADJ36 to sort (high↔low) · ADJ36 = +/- extrapolated to 36 min · minimum 3 min together")
