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

import pandas as pd
import pydeck as pdk
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MESES_ORDEN = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio"]

COLOR = {"Correctivo": "#2A78D6", "Preventivo": "#EB6834", "Podas": "#1BAF7A"}
COLOR_RGB = {"Correctivo": [42, 120, 214], "Preventivo": [235, 104, 52], "Podas": [27, 175, 122]}

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
    layers = []

    if mostrar_calor:
        layers.append(
            pdk.Layer(
                "HeatmapLayer",
                data=data_f,
                get_position=["Longitud", "Latitud"],
                aggregation="MEAN",
                opacity=0.55,
            )
        )
    else:
        # Una capa por variable = un color por variable, sin distinción por mes.
        for cat in FUENTES:
            sub = data_f[data_f["Categoria"] == cat]
            if sub.empty:
                continue
            layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    data=sub,
                    get_position=["Longitud", "Latitud"],
                    get_fill_color=COLOR_RGB[cat] + [200],
                    get_line_color=[255, 255, 255, 180],
                    line_width_min_pixels=0.5,
                    stroked=True,
                    get_radius=25,
                    radius_min_pixels=2.5,
                    radius_max_pixels=7,
                    pickable=True,
                )
            )

    view_state = pdk.ViewState(latitude=2.945, longitude=-75.275, zoom=12)
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style=None,
        tooltip={
            "html": "<b>{Categoria}</b><br/>Incidencia: {Incidencia}<br/>"
            "Farola: {Farola}<br/>Mes: {Mes}<br/>Estado: {Estado}",
            "style": {"backgroundColor": "#0D2B6B", "color": "white", "fontSize": "12px"},
        },
    )
    st.pydeck_chart(deck, height=560, use_container_width=True)

    leg1, leg2, leg3, _ = st.columns([1, 1, 1, 3])
    leg1.markdown(
        f'<span style="color:{COLOR["Correctivo"]}">●</span> Mantenimiento Correctivo',
        unsafe_allow_html=True,
    )
    leg2.markdown(
        f'<span style="color:{COLOR["Preventivo"]}">●</span> Mantenimiento Preventivo',
        unsafe_allow_html=True,
    )
    leg3.markdown(
        f'<span style="color:{COLOR["Podas"]}">●</span> Podas',
        unsafe_allow_html=True,
    )

with tab_resumen:
    resumen = (
        data.groupby(["Mes", "Categoria"]).size().unstack(fill_value=0).reindex(MESES_ORDEN)
    )
    for cat in FUENTES:
        if cat not in resumen.columns:
            resumen[cat] = 0
    resumen = resumen[list(FUENTES.keys())]
    resumen["Total"] = resumen.sum(axis=1)

    # Prefijo numérico para forzar orden cronológico en el eje del gráfico
    # (los gráficos de Streamlit ordenan el eje categórico alfabéticamente).
    chart_data = resumen[list(FUENTES.keys())].copy()
    chart_data.index = [f"{i+1:02d} {mes[:3]}" for i, mes in enumerate(MESES_ORDEN)]

    st.bar_chart(
        chart_data,
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
