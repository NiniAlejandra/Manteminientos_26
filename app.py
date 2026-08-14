"""
Mapa de Mantenimientos ESIP SAS ESP 2026
Tablero interactivo (Streamlit) — acumulado Enero-Julio 2026.
Un color por variable: Mantenimiento Correctivo, Mantenimiento Preventivo, Podas.

Para publicar en Streamlit Community Cloud:
1. Sube esta carpeta (app.py, requirements.txt, los 3 CSV y logo_esip.png) a un repo de GitHub.
2. Entra a https://share.streamlit.io -> "New app" -> selecciona el repo, branch y este archivo (app.py).
3. Deploy. Streamlit te entrega la URL pública lista para compartir.
"""

import base64
import csv
import os

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MESES_ORDEN = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio"]

COLOR = {"Correctivo": "#2A78D6", "Preventivo": "#EB6834", "Podas": "#1BAF7A"}

FUENTES = {
    "Correctivo": "bd_mantenimientos_jul.csv",
    "Preventivo": "Preventivos_jul.csv",
    "Podas": "podas_jul.csv",
}

st.set_page_config(
    page_title="Mapa de Mantenimientos ESIP SAS ESP 2026",
    page_icon="🗺️",
    layout="wide",
)


@st.cache_data
def cargar_datos():
    frames = []
    for categoria, archivo in FUENTES.items():
        ruta = os.path.join(BASE_DIR, archivo)
        df = pd.read_csv(
            ruta,
            sep=";",
            encoding="cp1252",
            engine="python",
            quoting=csv.QUOTE_MINIMAL,
        )
        df["Categoria"] = categoria
        df["Latitud"] = pd.to_numeric(
            df["Latitud"].astype(str).str.replace(",", ".", regex=False),
            errors="coerce",
        )
        df["Longitud"] = pd.to_numeric(
            df["Longitud"].astype(str).str.replace(",", ".", regex=False),
            errors="coerce",
        )
        frames.append(df)

    data = pd.concat(frames, ignore_index=True, sort=False)
    data = data.dropna(subset=["Latitud", "Longitud"])

    # Filtro geográfico de saneamiento (área de Neiva, Huila) y filas con datos inválidos (p.ej. "#N/D")
    data = data[
        data["Latitud"].between(2.5, 3.3) & data["Longitud"].between(-75.6, -74.9)
    ]
    data = data[data["Mes"].isin(MESES_ORDEN)]
    return data


data = cargar_datos()

logo_path = os.path.join(BASE_DIR, "logo_esip.png")
logo_b64 = ""
if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("ascii")

header_l, header_r = st.columns([0.12, 0.88])
with header_l:
    if logo_b64:
        st.markdown(
            f'<img src="data:image/png;base64,{logo_b64}" style="height:64px">',
            unsafe_allow_html=True,
        )
with header_r:
    st.markdown(
        "## Mapa de Mantenimientos ESIP SAS ESP 2026\n"
        "Alumbrado Público · Neiva, Huila · Seguimiento operativo integral  \n"
        "**Corte: 31 de julio de 2026 · Acumulado Enero – Julio 2026**"
    )

st.divider()

# ── Sidebar: filtros ──
st.sidebar.header("Filtros")
categorias_sel = st.sidebar.multiselect(
    "Variables a mostrar",
    options=list(FUENTES.keys()),
    default=list(FUENTES.keys()),
)
meses_sel = st.sidebar.multiselect(
    "Meses (vista acumulada por defecto)",
    options=MESES_ORDEN,
    default=MESES_ORDEN,
)
mostrar_calor = st.sidebar.checkbox("Mostrar mapa de calor (acumulado)", value=False)

data_f = data[data["Categoria"].isin(categorias_sel) & data["Mes"].isin(meses_sel)]

# ── KPIs ──
total = len(data_f)
n_corr = len(data_f[data_f["Categoria"] == "Correctivo"])
n_prev = len(data_f[data_f["Categoria"] == "Preventivo"])
n_poda = len(data_f[data_f["Categoria"] == "Podas"])

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total registros", f"{total:,}".replace(",", "."))
k2.metric("Mtto. Correctivo", f"{n_corr:,}".replace(",", "."))
k3.metric("Mtto. Preventivo", f"{n_prev:,}".replace(",", "."))
k4.metric("Podas", f"{n_poda:,}".replace(",", "."))

tab_mapa, tab_resumen = st.tabs(["🗺️ Mapa interactivo", "📊 Resumen mensual"])

with tab_mapa:
    m = folium.Map(
        location=[2.945, -75.275],
        zoom_start=12,
        tiles="CartoDB positron",
        prefer_canvas=True,
    )

    for _, row in data_f.iterrows():
        cat = row["Categoria"]
        color = COLOR[cat]
        tip_html = (
            f"<b>{cat}</b><br>"
            f"Incidencia: {row.get('Incidencia','—')}<br>"
            f"Farola: {row.get('Farola','—')}<br>"
            f"Mes: {row.get('Mes','—')}<br>"
            f"Tipo: {row.get('Tipo','—')}<br>"
            f"Estado: {row.get('Estado','—')}"
        )
        if cat == "Podas":
            folium.RegularPolygonMarker(
                location=[row["Latitud"], row["Longitud"]],
                number_of_sides=3,
                radius=6,
                rotation=0,
                color="#ffffff",
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.9,
                tooltip=tip_html,
            ).add_to(m)
        elif cat == "Preventivo":
            folium.RegularPolygonMarker(
                location=[row["Latitud"], row["Longitud"]],
                number_of_sides=4,
                radius=5,
                rotation=45,
                color="#ffffff",
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.9,
                tooltip=tip_html,
            ).add_to(m)
        else:
            folium.CircleMarker(
                location=[row["Latitud"], row["Longitud"]],
                radius=3.2,
                color="#ffffff",
                weight=0.6,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                tooltip=tip_html,
            ).add_to(m)

    if mostrar_calor:
        from folium.plugins import HeatMap

        heat_pts = data_f[["Latitud", "Longitud"]].values.tolist()
        if heat_pts:
            HeatMap(heat_pts, radius=16, blur=20).add_to(m)

    legend_html = f"""
    <div style="position: fixed; bottom: 30px; right: 30px; z-index:9999;
        background:white; padding:10px 14px; border-radius:8px;
        box-shadow:0 2px 10px rgba(0,0,0,.15); font-size:12px; font-family:sans-serif; line-height:2">
      <b style="display:block;margin-bottom:4px;color:#0D2B6B">Referencias</b>
      <span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{COLOR['Correctivo']}"></span> Mantenimiento Correctivo</span><br>
      <span><span style="display:inline-block;width:9px;height:9px;background:{COLOR['Preventivo']}"></span> Mantenimiento Preventivo</span><br>
      <span><span style="display:inline-block;width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:9px solid {COLOR['Podas']}"></span> Podas</span>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, width=None, height=560, returned_objects=[])

with tab_resumen:
    resumen = (
        data.groupby(["Mes", "Categoria"]).size().unstack(fill_value=0).reindex(MESES_ORDEN)
    )
    for cat in FUENTES:
        if cat not in resumen.columns:
            resumen[cat] = 0
    resumen = resumen[list(FUENTES.keys())]
    resumen["Total"] = resumen.sum(axis=1)

    st.bar_chart(
        resumen[list(FUENTES.keys())],
        color=[COLOR["Correctivo"], COLOR["Preventivo"], COLOR["Podas"]],
    )
    st.dataframe(
        resumen.style.format("{:,.0f}"),
        use_container_width=True,
    )

st.caption(
    "Desarrollado por A.V. · 2026 | ESIP SAS ESP · Alumbrado Público Neiva · "
    "Jefatura de Investigaciones y Desarrollo Social"
)
