# 🔴 Diablos Analytics — Lineup Explorer

Dashboard de lineups (LNBP) construido con **Streamlit**. Muestra +/- y minutos por
alineación (grupos de 2 a 5 jugadores), y agrega automáticamente todos los juegos que
subas a la carpeta `data/`.

## 🚀 Publicarlo gratis (sin instalar nada)

1. Crea cuenta en **GitHub**: https://github.com/signup
2. Crea un repositorio nuevo (botón **New** → nombre p.ej. `diablos-analytics` → **Create**).
3. Sube estos archivos al repo (botón **Add file → Upload files**, arrastra todo:
   `app.py`, `requirements.txt`, `README.md` y la carpeta `data/`). Commit.
4. Entra a **Streamlit Community Cloud**: https://share.streamlit.io → *Continue with GitHub*.
5. Clic en **Create app** → elige tu repo → *Main file path* = `app.py` → **Deploy**.
6. En ~1 min tienes tu link público. (Para hacerlo privado: Settings → Sharing.)

## ➕ Agregar un juego nuevo

1. Corre tu notebook (Colab) del partido nuevo.
2. Exporta un CSV con estas columnas exactas:
   `date, team, team_code, opponent, size, lineup, minutes, plus_minus, pm_per36`
   (una fila por cada combinación de 1 a 5 jugadores por equipo).
3. Súbelo a la carpeta **data/** del repo (Add file → Upload files).
4. El dashboard se actualiza solo.

## 🗺️ Siguientes niveles (roadmap)
- Nivel 1: Diablos (listo).
- Nivel 2: toda la liga (agregar más equipos a los CSV).
- Métricas avanzadas: posesiones, eFG%, TS%, ORtg/DRtg, Net, Pace por lineup.
