import glob, os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Diablos Analytics — Lineups", layout="wide", page_icon="🔴")

@st.cache_data
def load_data():
    files = [f for f in glob.glob("**/*", recursive=True) if f.lower().endswith(".csv")]
    if not files:
        return pd.DataFrame()
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    return df

df = load_data()

st.title("🔴 Diablos Analytics — Lineup Explorer")
st.caption("LNBP · +/- and minutes by lineup (2–5 players) · data accumulates as you add games")

if df.empty:
    st.warning("No hay datos en la carpeta /data. Sube un CSV de juego para empezar.")
    st.stop()

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
teams = sorted(df["team"].unique())
team = st.sidebar.selectbox("Team", teams, index=0)
size = st.sidebar.radio("Lineup size", [2, 3, 4, 5], index=3, horizontal=True)
min_minutes = st.sidebar.slider("Min. minutes together", 0.0, 20.0, 3.0, 0.5)

tdf = df[(df["team"] == team) & (df["size"] == size)].copy()

# players available in this team (from size-1 rows)
players = sorted(df[(df["team"] == team) & (df["size"] == 1)]["lineup"].unique())
sel_players = st.sidebar.multiselect("Filter by player (must include all)", players)

# ---------- Aggregate across games ----------
agg = (tdf.groupby(["team", "lineup", "size"], as_index=False)
          .agg(GP=("date", "nunique"), MIN=("minutes", "sum"), PM=("plus_minus", "sum")))
agg = agg[agg["MIN"] >= min_minutes]
agg["PM_per36"] = (agg["PM"] * 36 / agg["MIN"]).round(1)
agg["MIN"] = agg["MIN"].round(1)

if sel_players:
    for p in sel_players:
        agg = agg[agg["lineup"].str.contains(p.split(" ", 1)[0] + " ", regex=False) |
                  agg["lineup"].str.contains(p, regex=False)]

agg = agg.sort_values("PM", ascending=False).reset_index(drop=True)

# ---------- KPIs ----------
c1, c2, c3 = st.columns(3)
c1.metric("Lineups shown", len(agg))
c2.metric("Best +/-", f'{agg["PM"].max():+d}' if len(agg) else "—")
c3.metric("Worst +/-", f'{agg["PM"].min():+d}' if len(agg) else "—")

# ---------- Table ----------
show = agg.rename(columns={"lineup": "Lineup"})[["Lineup", "GP", "MIN", "PM", "PM_per36"]]
st.dataframe(
    show,
    use_container_width=True, hide_index=True,
    column_config={
        "MIN": st.column_config.NumberColumn("MIN", format="%.1f"),
        "PM": st.column_config.NumberColumn("+/-", format="%d"),
        "PM_per36": st.column_config.NumberColumn("+/- per 36", format="%.1f"),
    },
)
st.caption("Sortable: click a column header. +/- per 36 = differential extrapolated to 36 minutes.")

with st.expander("ℹ️ Cómo agregar más juegos"):
    st.markdown(
        "1. Corre el notebook (Colab) para el partido nuevo.\n"
        "2. Exporta el CSV con el mismo formato (columns: date, team, team_code, opponent, size, lineup, minutes, plus_minus, pm_per36).\n"
        "3. Súbelo a la carpeta **data/** de tu repo en GitHub.\n"
        "4. El dashboard se actualiza solo (agrega la temporada)."
    )
