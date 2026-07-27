import glob, json, html
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Diablos Analytics — Lineups", layout="wide", page_icon="🔴")

COLORS = {"DRM": "#e01023", "AGS": "#e3a400"}
TNAME = {"DRM": "DIABLOS ROJOS", "AGS": "PANTERAS"}

@st.cache_data
def load():
    import os
    seen=set(); files=[]
    for f in glob.glob("**/*", recursive=True):
        if f.lower().endswith(".csv"):
            b=os.path.basename(f).lower()
            if b not in seen: seen.add(b); files.append(f)
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True) if files else pd.DataFrame()
    try:
        players = json.load(open("players.json", encoding="utf-8"))
    except Exception:
        players = {}
    return df, players

df, PLAYERS = load()

CSS = """
<style>
.stApp{background:#08090b}
#MainMenu,header,footer{visibility:hidden}
.block-container{padding-top:1.4rem;max-width:1150px}
.dh{font-size:11px;letter-spacing:.3em;color:#8a929c;font-weight:700}
.dt{font-size:30px;font-weight:800;color:#e9ecef;letter-spacing:-.5px;margin:2px 0}
.units{display:flex;flex-direction:column;gap:8px;margin-top:6px}
.unit{display:flex;align-items:center;gap:12px;background:#0e1013;border:1px solid #1b1e24;border-radius:12px;padding:9px 12px}
.urow{display:flex;gap:7px;flex:1;flex-wrap:wrap}
.pb{display:flex;flex-direction:column;align-items:center;gap:4px;width:60px}
.ring{position:relative;border-radius:50%;width:50px;height:50px;background-color:#333;background-size:cover;background-position:center top}
.ring .num{position:absolute;bottom:-3px;right:-3px;background:#0c0c0e;color:#fff;font-size:9px;font-weight:800;border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center}
.pn{font-size:9px;font-weight:700;text-align:center;color:#cfd4da;line-height:1.05}
.metrics{display:flex;flex-direction:column;gap:5px;min-width:58px}
.net,.adj{text-align:center;font-weight:800;border-radius:9px;padding:5px 4px}
.net b{font-size:19px;display:block;letter-spacing:-.5px}.adj b{font-size:13px;display:block}
.net small,.adj small{font-size:8px;letter-spacing:.1em;color:#8a929c;font-weight:700}
.adj{border:1px dashed #2a2f38}
.pos b{color:#2fe08a}.neg b{color:#ff5468}.zero b{color:#aab2bc}
.net.pos{background:rgba(47,224,138,.10)}.net.neg{background:rgba(255,84,104,.10)}.net.zero{background:rgba(170,178,188,.08)}
.umin{min-width:46px;text-align:center}.umin b{font-size:16px;font-weight:800;color:#e9ecef;display:block}.umin small{font-size:8px;letter-spacing:.14em;color:#6b7280;font-weight:700}
.cs{color:#8a929c;font-size:12px;margin:8px 0}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

if df.empty:
    st.warning("No hay datos. Sube un CSV de juego al repo.")
    st.stop()

# ---- controls ----
c1, c2, c3 = st.columns([1.3, 1.6, 1.1])
team = c1.selectbox("Equipo", sorted(df["team_code"].unique(),
                    key=lambda t: 0 if t == "DRM" else 1),
                    format_func=lambda t: TNAME.get(t, t))
size = c2.radio("Tamaño", [2, 3, 4, 5], index=3, horizontal=True)
view = c3.radio("Vista", ["Best", "Worst", "All"], index=0, horizontal=True)

pl_team = PLAYERS.get(team, {})
sel = st.multiselect("Filtrar por jugador (los incluye a todos)",
                     options=list(pl_team.keys()),
                     format_func=lambda l: pl_team[l]["sn"])
min_min = st.slider("Minutos mínimos juntos", 0.0, 20.0, 3.0, 0.5)

acc = COLORS.get(team, "#e01023")
st.markdown(f'<div class="dh">LNBP · LINEUP EXPLORER</div>'
            f'<div class="dt" style="border-bottom:3px solid {acc};display:inline-block;padding-bottom:3px">{TNAME.get(team, team)}</div>',
            unsafe_allow_html=True)

# ---- aggregate ----
t = df[(df["team_code"] == team) & (df["size"] == size)]
agg = (t.groupby("lineup", as_index=False)
        .agg(GP=("date", "nunique"), MIN=("minutes", "sum"), PM=("plus_minus", "sum")))
agg = agg[agg["MIN"] >= min_min]
agg["PM36"] = (agg["PM"] * 36 / agg["MIN"]).round(0).astype(int)
agg["MIN"] = agg["MIN"].round(1)
if sel:
    for lab in sel:
        agg = agg[agg["lineup"].str.contains(lab, regex=False)]
agg = agg.sort_values("PM", ascending=False)

if view == "Best":
    show = agg[agg["PM"] > 0].head(4)
elif view == "Worst":
    show = agg[agg["PM"] < 0].tail(4).iloc[::-1]
else:
    show = agg

def sg(x): return f"+{x}" if x > 0 else str(x)

def circle(label):
    p = pl_team.get(label, {"num": label.split(" ", 1)[0].lstrip("#"),
                            "sn": label.split(" ", 1)[-1].upper(), "img": None})
    bg = f'background-image:url({p["img"]})' if p.get("img") else ""
    return (f'<span class="pb"><span class="ring" style="{bg};box-shadow:0 0 0 2px {acc};background-color:{acc}">'
            f'<span class="num" style="box-shadow:0 0 0 2px {acc}">{p["num"]}</span></span>'
            f'<span class="pn">{html.escape(p["sn"])}</span></span>')

def unit(r):
    rc = "pos" if r["PM"] > 0 else "neg" if r["PM"] < 0 else "zero"
    ac = "pos" if r["PM36"] > 0 else "neg" if r["PM36"] < 0 else "zero"
    circles = "".join(circle(l) for l in r["lineup"].split(" / "))
    return (f'<div class="unit"><span class="metrics">'
            f'<span class="net {rc}"><b>{sg(r["PM"])}</b><small>+/-</small></span>'
            f'<span class="adj {ac}"><b>{sg(r["PM36"])}</b><small>ADJ36</small></span></span>'
            f'<span class="urow">{circles}</span>'
            f'<span class="umin"><b>{r["MIN"]}</b><small>MIN</small></span></div>')

if len(show):
    rows = "".join(unit(r) for _, r in show.iterrows())
    st.markdown(f'<div class="units">{rows}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="cs">Sin combinaciones con esos filtros.</div>', unsafe_allow_html=True)
st.caption("+/- real · ADJ36 = extrapolado a 36 min · MIN = minutos juntos en cancha")
