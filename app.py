
import pandas as pd
import json
import folium
import streamlit as st
import random
from streamlit_folium import st_folium
from validacao import carregarDados, montarAvisos, limparLinhasInvalidas
from countries_in_continents import identificar_continente

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1100px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Carregamento dos dados
institutions, researchers = carregarDados()
avisos = montarAvisos(institutions, researchers)
df_institutions, df_researchers = limparLinhasInvalidas(institutions, researchers)

DATA_PATH = "./data"

@st.cache_data
def carregar_dados():
    return pd.read_excel(DATA_PATH + "/institutions-and-researchers.xlsx")

df = carregar_dados()

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

st.title("Globe GenAI 🌎️")
mostrarAvisos(avisos)
st.markdown("O projeto consiste na elaboração de um *software web* que permita a visualização em um mapa mundi das instituições registradas em um determinado `dataset`.")

# Modal (janela de diálogo dialog)
@st.dialog("Informations about the institution", dismissible=True)
def mostrar_instituicao(instituicao):
    st.subheader(instituicao["University / Institute"])
    st.write("**Country:**", instituicao["Country"])

    pesquisadores = df_researchers[
        df_researchers["institution_id"].astype(str)
        == str(instituicao["institution_id"])
    ]

    st.subheader("Researchers")

    if pesquisadores.empty:
        st.write("No researchers found.")
    else:
        st.dataframe(
            pesquisadores[["Research Name"]].rename(
                columns={
                    "Research Name": "Nome do pesquisador"
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

# Identificando o continente de cada instituição e salvando num df
df_institutions_continents = df_institutions.copy()

df_institutions_continents["Continent"] = (
    df_institutions_continents["Country"]
    .apply(identificar_continente)
)

# Interface do filtro e pesquisa
st.subheader("Filters and Search")
col1, col2 = st.columns(2)

# Opções dos filtros
continentes = sorted(
    df_institutions_continents["Continent"].dropna().unique()
)

with col1:
    continente_selecionado = st.selectbox(
        "Continent",
        ["Todos"] + continentes,
        key="filtro_continente"
    )

# Mostra somente os países do continente selecionado
df_opcoes_pais = df_institutions_continents

if continente_selecionado != "Todos":
    df_opcoes_pais = df_opcoes_pais[
        df_opcoes_pais["Continent"] == continente_selecionado
    ]

paises = sorted(
    df_opcoes_pais["Country"].dropna().unique()
)

# Ao trocar o continente, reinicia o filtro de país
if st.session_state.get("continente_anterior") != continente_selecionado:
    st.session_state["pais_selecionado"] = "Todos"
    st.session_state["continente_anterior"] = continente_selecionado

with col2:
    pais_selecionado = st.selectbox(
        "Region / Country",
        ["Todos"] + paises,
        key="pais_selecionado"
    )

pesquisa = st.text_input(
    "Search for a researcher, continent or university",
    placeholder="Type a name, continent or university..."
)

# O que o filtro faz em cada caso
def aplicar_filtros(df_institutions, df_researchers, continente, pais, pesquisa):
    
    df_filtrado = df_institutions.copy()

    if continente != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Continent"] == continente]

    if pais != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Country"] == pais]

    termo = pesquisa.strip()

    # Verificando quais instituições cumprem o filtro
    if termo:
        nomes_instituicoes = (df_filtrado["University / Institute"].fillna("").astype(str))
        nomes_continentes = (df_filtrado["Continent"].fillna("").astype(str))

        instituicoes_encontradas = (
            nomes_instituicoes.str.contains(termo,case=False,na=False)
            |
            nomes_continentes.str.contains(termo,case=False,na=False)
        )

        ids_instituicoes = set(
            df_filtrado.loc[instituicoes_encontradas,"institution_id"].dropna()
        )

        ids_disponiveis = set(
            df_filtrado["institution_id"].dropna()
        )

        pesquisadores_disponiveis = df_researchers[
            df_researchers["institution_id"].isin(ids_disponiveis)
        ]

        pesquisadores_encontrados = (
            pesquisadores_disponiveis["Research Name"]
            .fillna("")
            .astype(str)
            .str.contains(
                termo,
                case=False,
                regex=False,
                na=False
            )
        )

        ids_pesquisadores = set(
            pesquisadores_disponiveis.loc[
                pesquisadores_encontrados,
                "institution_id"
            ].dropna()
        )

        ids_encontrados = ids_instituicoes | ids_pesquisadores

        df_filtrado = df_filtrado[
            df_filtrado["institution_id"].isin(ids_encontrados)
        ]

    return df_filtrado

df_filtrado = aplicar_filtros(
    df_institutions_continents,
    df_researchers,
    continente_selecionado,
    pais_selecionado,
    pesquisa
)

# Mostrando o resultado
st.caption(
    f"{len(df_filtrado)} institutions found"
)

if df_filtrado.empty:
    st.info(
        "No institutions found for the selected filters."
    )


# Construindo o mapa
def construir_mapa(df_institutions):

    with open("continents.geojson", "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    mapa = folium.Map(
        location=[10, 0],
        zoom_start=2,
        min_zoom=2,
        tiles=None,
        max_bounds=True,
        min_lat=-85, max_lat=85,
        min_lon=-180, max_lon=180,
        max_bounds_viscosity=1.0,
    )

    mapa.get_root().header.add_child(
        folium.Element(
            "<style>.leaflet-container { background: #0099bb; }</style>"
        )
    )

    COR_PADRAO = "#cccccc"

    # Continentes
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
            highlight_function=lambda _f: {
                "fillOpacity": 0.95,
                "weight": 2.5,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["CONTINENT"],
                aliases=["Continente:"],
                sticky=True,
            ),
        ).add_to(mapa)

    # Marcadores das instituições
    for _, linha in df_institutions.iterrows():

        if pd.isna(linha["lat"]) or pd.isna(linha["lon"]):
            continue

        folium.Marker(
            location=[linha["lat"], linha["lon"]],
            tooltip=linha["University / Institute"],
            icon=folium.Icon(
                color="darkblue",
                icon="map-marker",
                prefix="fa",
            ),
        ).add_to(mapa)

    return mapa

# Mostrando o mapa na tela
def exibir_mapa(df_filtrado):
    # Identifica os marcadores para verificar
    # se o mapa precisa ser reconstruído
    marcadores = []
    for _, linha in df_filtrado.iterrows():
        if pd.isna(linha["lat"]) or pd.isna(linha["lon"]):
            continue

        marcadores.append(
            (
                linha["institution_id"],
                str(linha["University / Institute"]),
                round(float(linha["lat"]), 8),
                round(float(linha["lon"]), 8)
            )
        )

    assinatura = tuple(sorted(marcadores))

    if (
        "assinatura_mapa" not in st.session_state
        or st.session_state["assinatura_mapa"] != assinatura
    ):
        numero_anterior = st.session_state.get("numero_mapa")
        numero_novo = random.randint(0, 999999999)
        while numero_novo == numero_anterior:
            numero_novo = random.randint(0, 999999999)

        st.session_state["numero_mapa"] = numero_novo
        st.session_state["mapa_folium"] = construir_mapa(
            df_filtrado
        )

        st.session_state["assinatura_mapa"] = assinatura
        st.session_state.pop(
            "ultimo_clique_tratado",
            None
        )

    mapa = st.session_state["mapa_folium"]
    numero_mapa = st.session_state["numero_mapa"]

    st_data = st_folium(
        mapa,
        use_container_width=True,
        height=780,
        key=f"mapa_instituicoes_{numero_mapa}",
        returned_objects=["last_object_clicked"],
    )

    # Identificando qual instituição foi clicada
    if st_data and st_data.get("last_object_clicked"):
        ponto = st_data["last_object_clicked"]
        if "lat" in ponto and "lng" in ponto:
            latitude = ponto["lat"]
            longitude = ponto["lng"]
            clique = (
                numero_mapa,
                latitude,
                longitude
            )
            if (
                st.session_state.get("ultimo_clique_tratado")
                != clique
            ):
                selecionada = df_filtrado[
                    (
                        (df_filtrado["lat"] - latitude).abs()
                        < 0.000001
                    )
                    &
                    (
                        (df_filtrado["lon"] - longitude).abs()
                        < 0.000001
                    )
                ]

                if not selecionada.empty:
                    st.session_state[
                        "ultimo_clique_tratado"
                    ] = clique
                    return selecionada.iloc[0]

    return None

instituicao_selecionada = exibir_mapa(df_filtrado)

if instituicao_selecionada is not None:
    mostrar_instituicao(
        instituicao_selecionada
    )
