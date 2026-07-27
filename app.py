import glob, json, html, os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Diablos Analytics — Lineups", layout="wide", page_icon="🔴")
COLORS = {"DRM": "#e01023", "AGS": "#e3a400"}
TNAME = {"DRM": "DIABLOS ROJOS", "AGS": "PANTERAS"}
MIN_FLOOR = 3.0  # piso interno de minutos (antes era la barra)

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
            ".block-container{padding-top:1.1rem;max-width:1180px}"
            "div[data-testid='stVerticalBlock']{gap:.6rem}</style>", unsafe_allow_html=True)

if df.empty:
    st.warning("No hay datos. Sube un CSV de juego al repo."); st.stop()

c1, c2, c3 = st.columns([1.3, 1.7, 1.1])
team = c1.selectbox("Equipo", sorted(df["team_code"].unique(), key=lambda t: 0 if t == "DRM" else 1),
                    format_func=lambda t: TNAME.get(t, t))
size = c2.radio("Tamaño", [2, 3, 4, 5], index=3, horizontal=True)
view = c3.radio("Vista", ["Best", "Worst", "All"], index=0, horizontal=True)
pl_team = PLAYERS.get(team, {})
sel = st.multiselect("Filtrar por jugador (los incluye a todos)", list(pl_team.keys()),
                     format_func=lambda l: pl_team[l]["sn"])
acc = COLORS.get(team, "#e01023")

t = df[(df["team_code"] == team) & (df["size"] == size)]
agg = (t.groupby("lineup", as_index=False)
        .agg(GP=("date", "nunique"), SEC=("seconds", "sum"), PM=("plus_minus", "sum")))
agg["MIN"] = agg["SEC"] / 60
agg = agg[agg["MIN"] >= MIN_FLOOR]
agg["PM36"] = (agg["PM"] * 2160 / agg["SEC"]).round(0).astype(int)
agg["MIN"] = agg["MIN"].round(1)
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
    img = f'<img src="{p["img"]}">' if p.get("img") else ""
    return (f'<span class="pb"><span class="ring">{img}<span class="num">{p["num"]}</span></span>'
            f'<span class="pn">{html.escape(p["sn"])}</span></span>')

def unit(r, rank):
    rc = "pos" if r["PM"] > 0 else "neg" if r["PM"] < 0 else "zero"
    ac = "pos" if r["PM36"] > 0 else "neg" if r["PM36"] < 0 else "zero"
    circles = "".join(circle(l) for l in r["lineup"].split(" / "))
    return (f'<div class="unit"><span class="rk">{rank}</span><span class="metrics">'
            f'<span class="net {rc}"><b>{sg(r["PM"])}</b><small>+/-</small></span>'
            f'<span class="adj {ac}"><b>{sg(r["PM36"])}</b><small>ADJ36</small></span></span>'
            f'<span class="urow">{circles}</span>'
            f'<span class="umin"><b>{r["MIN"]}</b><small>MIN</small></span></div>')

rows_html = "".join(unit(r, i + 1) for i, (_, r) in enumerate(show.iterrows())) \
    or '<div class="cs">Sin combinaciones con esos filtros.</div>'
block = f"""
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:"Segoe UI",Arial,sans-serif}}
body{{background:transparent;overflow:hidden}}
.hd{{font-size:11px;letter-spacing:.32em;color:#8a929c;font-weight:700}}
.tn{{font-size:27px;font-weight:800;color:#e9ecef;border-bottom:3px solid {acc};display:inline-block;padding-bottom:4px;margin:3px 0 15px}}
.units{{display:flex;flex-direction:column;gap:10px}}
.unit{{display:flex;align-items:center;gap:14px;background:linear-gradient(180deg,#101318,#0c0e12);border:1px solid #1c2027;border-radius:16px;padding:14px 18px}}
.rk{{font-size:15px;font-weight:800;color:#5a6270;min-width:20px;text-align:center}}
.urow{{display:flex;gap:11px;flex:1;justify-content:center}}
.pb{{display:flex;flex-direction:column;align-items:center;gap:6px;width:78px}}
.ring{{position:relative;border-radius:50%;width:68px;height:68px;background:#15171b;box-shadow:0 0 0 2.5px {acc}}}
.ring img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center top;border-radius:50%}}
.ring .num{{position:absolute;bottom:-3px;right:-3px;background:#0c0c0e;box-shadow:0 0 0 2px {acc};color:#fff;font-size:11px;font-weight:800;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center}}
.pn{{font-size:10px;font-weight:700;text-align:center;color:#cfd4da;line-height:1.1}}
.metrics{{display:flex;flex-direction:column;gap:6px;min-width:64px}}
.net,.adj{{text-align:center;font-weight:800;border-radius:10px;padding:6px 5px}}
.net b{{font-size:23px;display:block;letter-spacing:-.5px}}.adj b{{font-size:14px;display:block}}
.net small,.adj small{{font-size:8px;letter-spacing:.1em;color:#8a929c;font-weight:700}}
.adj{{border:1px dashed #2a2f38}}
.pos b{{color:#2fe08a}}.neg b{{color:#ff5468}}.zero b{{color:#aab2bc}}
.net.pos{{background:rgba(47,224,138,.10)}}.net.neg{{background:rgba(255,84,104,.10)}}.net.zero{{background:rgba(170,178,188,.08)}}
.umin{{min-width:52px;text-align:center}}.umin b{{font-size:19px;font-weight:800;color:#e9ecef;display:block}}.umin small{{font-size:8px;letter-spacing:.14em;color:#6b7280;font-weight:700}}
.cs{{color:#8a929c;font-size:13px;padding:10px}}
</style>
<div class="hd">LNBP · LINEUP EXPLORER</div><div class="tn">{TNAME.get(team, team)}</div>
<div class="units">{rows_html}</div>
"""
h = 92 + max(1, len(show)) * 128
components.html(block, height=h, scrolling=False)
st.caption("+/- real · ADJ36 = extrapolado a 36 min · MIN = minutos juntos en cancha · mínimo 3 min juntos")
