import pandas as pd
import json
import folium
import streamlit as st
from streamlit_folium import st_folium

DATA_PATH = "./data"

df = pd.read_excel(DATA_PATH + "/institutions-and-researchers.xlsx")

st.title("Globe GenAI 🌎️")
st.markdown("O projeto consiste na elaboração de um *software web* que permita a visualização em um mapa mundi das instituições registradas em um determinado `dataset`.")

def carregar_mapa():
    with open("continents.geojson", "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    mapa = folium.Map(
        location=[-22.815313, -47.06914],
        zoom_start=3,
        tiles=None,
        min_zoom=2,
    )

    mapa.get_root().header.add_child( # type: ignore
        folium.Element("<style>.leaflet-container { background: #0099bb; }</style>")
    )

    COR_PADRAO = "#cccccc"

    for feature in geojson_data["features"]:
        props = feature.get("properties", {})
        nome = props.get("CONTINENT", "?")
        cor = props.get("fill") or COR_PADRAO

        folium.GeoJson(
            feature,
            name=nome,
            style_function=lambda _f, cor=cor: {  
                "fillColor": cor,
                "fillOpacity": 0.75,
                "color": "#333333",
                "weight": 1.5,
            },
            highlight_function=lambda _f: {"fillOpacity": 0.95, "weight": 2.5},
            tooltip=folium.GeoJsonTooltip(
                fields=["CONTINENT"],
                aliases=["Continente:"],
                sticky=True,
            ),
        ).add_to(mapa)

    st_data = st_folium(mapa, use_container_width=True, height=500)
    return st_data

carregar_mapa()

st.dataframe(df)
