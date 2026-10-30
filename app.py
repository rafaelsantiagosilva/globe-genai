import pandas as pd
import json
import folium
import streamlit as st
from streamlit_folium import st_folium
from validacao import carregarDados, montarAvisos

institutions, researchers = carregarDados()
avisos = montarAvisos(institutions, researchers)

def mostrarAvisos(avisos):
    for aviso in avisos:
        mostrar = f"mostrar_{aviso['id']}"
        ignorar = f"ignorar_{aviso['id']}"
        
        if not st.session_state.get(mostrar, True):
            continue
        
        st.warning(aviso["texto"])
        with st.expander("Ver mais"):
            st.dataframe(aviso["detalhes"])
        if st.button("Ignorar", key=ignorar):
            st.session_state[mostrar] = False
            st.rerun()

DATA_PATH = "./data"

@st.cache_data
def carregar_dados():
    return pd.read_excel(DATA_PATH + "/institutions-and-researchers.xlsx")

@st.cache_data
def carregar_instituiçoes():
    return pd.read_csv(DATA_PATH + "/institutions.csv")

@st.cache_data
def carregar_researchers():
    return pd.read_csv(DATA_PATH + "/researchers.csv")

df = carregar_dados()
df_institutions = carregar_instituiçoes()
df_researchers = carregar_researchers()

st.title("Globe GenAI 🌎️")
mostrarAvisos(avisos)
st.markdown("O projeto consiste na elaboração de um *software web* que permita a visualização em um mapa mundi das instituições registradas em um determinado `dataset`.")

# Dialog: janela de diálogo (modal)
# Dismissible True permite fechar a janela clicando fora dela
@st.dialog("Informations about the institution", dismissible=True)
def mostrar_instituicao(instituicao):
    st.subheader(instituicao["University / Institute"])
    st.write("**Country:**", instituicao["Country"])

    researchers = df_researchers[
        df_researchers["institution_id"]
        == instituicao["institution_id"]
    ]

    st.subheader("Researchers")

    if researchers.empty:
        st.write("No researchers found.")
    else:
        st.dataframe(
            researchers[["Research Name"]].rename(
                columns={
                    "Research Name": "Nome do pesquisador"
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

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


    for _, linha in df_institutions.iterrows():
        if pd.isna(linha["lat"]) or pd.isna(linha["lon"]):
            continue

        folium.Marker(
            location=[linha["lat"], linha["lon"]],
            tooltip=linha["University / Institute"],
            icon=folium.Icon(
                color="darkblue",
                icon="map-marker",
                prefix="fa"
            ),
        ).add_to(mapa)

    #st_data = st_folium(mapa, use_container_width=True, height=500)

    st_data = st_folium(
        mapa,
        use_container_width=True,
        height=500,
        key="mapa_instituicoes",
    )

    if st_data and st_data["last_object_clicked"]:
        ponto = st_data["last_object_clicked"]

        selecionada = df_institutions[
            (df_institutions["lat"] == ponto["lat"]) &
            (df_institutions["lon"] == ponto["lng"])
        ]

        if not selecionada.empty:
            mostrar_instituicao(selecionada.iloc[0])

    return st_data

carregar_mapa()

st.dataframe(df)

