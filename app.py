import base64
import io
import json
from pathlib import Path

import pandas as pd
import folium
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium
from validacao import carregarDados, montarAvisos, limparLinhasInvalidas

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

institutions, researchers = carregarDados()
avisos = montarAvisos(institutions, researchers)
df_institutions, df_researchers = limparLinhasInvalidas(institutions, researchers)

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
ICONS_PATH = Path(DATA_PATH) / "icons"      # ./data/icons/[ID_DA_INSTITUIÇÃO].[EXTENSÃO]
EXTENSOES_ICONE = {".png", ".svg", ".jpg", ".jpeg", ".webp", ".gif", ".ico"}
TAMANHO_ICONE = 44                          # diâmetro do círculo branco, em pixels

@st.cache_data
def carregar_dados():
    return pd.read_excel(DATA_PATH + "/institutions-and-researchers.xlsx")

df = carregar_dados()

# --- ÍCONES DAS INSTITUIÇÕES ---------------------------------------------------

def chave_instituicao(valor):
    """Normaliza o ID (0, 0.0, '0') para a mesma chave de texto usada no nome do arquivo."""
    try:
        return str(int(float(valor)))
    except (TypeError, ValueError):
        return str(valor).strip()


def mapear_icones():
    """Varre ./data/icons e devolve {id_da_instituicao: caminho_do_arquivo}."""
    if not ICONS_PATH.is_dir():
        return {}

    icones = {}
    for arquivo in sorted(ICONS_PATH.iterdir()):
        if arquivo.is_file() and arquivo.suffix.lower() in EXTENSOES_ICONE:
            icones.setdefault(arquivo.stem, arquivo)
    return icones


# O cache usa o caminho + data de modificação, então trocar um ícone atualiza o mapa
@st.cache_data(show_spinner=False)
def carregar_icone_base64(caminho, modificado_em):
    """Lê a imagem e devolve um data URI (ou None se o arquivo estiver corrompido).

    Imagens raster são reduzidas para no máximo 96 px para o mapa não ficar pesado
    com centenas de logos grandes embutidas no HTML.
    """
    try:
        caminho = Path(caminho)

        if caminho.suffix.lower() == ".svg":
            dados = base64.b64encode(caminho.read_bytes()).decode("ascii")
            return f"data:image/svg+xml;base64,{dados}"

        with Image.open(caminho) as imagem:
            imagem = imagem.convert("RGBA")
            imagem.thumbnail((96, 96), Image.LANCZOS)
            buffer = io.BytesIO()
            imagem.save(buffer, format="PNG")

        dados = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{dados}"
    except Exception:
        return None


def icone_circular_html(caminho):
    """HTML do ícone dentro de um círculo branco (None se não houver imagem utilizável)."""
    if caminho is None:
        return None

    uri = carregar_icone_base64(str(caminho), caminho.stat().st_mtime)
    if uri is None:
        return None

    interno = int(TAMANHO_ICONE * 0.68)
    return f"""
        <div class="icone-instituicao" style="
            width:{TAMANHO_ICONE}px; height:{TAMANHO_ICONE}px;
            box-sizing:border-box;
            border-radius:50%;
            background:#ffffff;
            border:2px solid #1f3a5f;
            box-shadow:0 1px 4px rgba(0,0,0,0.45);
            display:flex; align-items:center; justify-content:center;
            overflow:hidden;">
            <img src="{uri}"
                 style="width:{interno}px; height:{interno}px; object-fit:contain;" />
        </div>
    """

# --- FIM ÍCONES ----------------------------------------------------------------

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
                    "Researcher Name": "Nome do pesquisador"
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

def construir_mapa(df_institutions):

    with open("continents.geojson", "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    mapa = folium.Map(
        location=[10, 0],
        zoom_start=2,                # zoom inicial que tenta abranger a maior parte dos continentes sem borda
        min_zoom=2,                  # zoom minimo possivel
        tiles=None,
        max_bounds=True,
        min_lat=-85, max_lat=85,
        min_lon=-180, max_lon=180,
        max_bounds_viscosity=1.0,
    )

    mapa.get_root().header.add_child(
        folium.Element(
            """
            <style>
            .leaflet-container { background: #0099bb; }

            /* Ícones das instituições: crescem um pouco ao passar o mouse */
            .marcador-instituicao { cursor: pointer; }
            .marcador-instituicao .icone-instituicao {
                transition: transform 0.15s ease, box-shadow 0.15s ease;
            }
            .marcador-instituicao:hover {
                z-index: 100000 !important;      /* fica por cima dos ícones vizinhos */
            }
            .marcador-instituicao:hover .icone-instituicao {
                transform: scale(1.35);
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.6);
            }
            </style>
            """
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
    icones = mapear_icones()

    for _, linha in df_institutions.iterrows():

        if pd.isna(linha["lat"]) or pd.isna(linha["lon"]):
            continue

        caminho_icone = icones.get(chave_instituicao(linha["institution_id"]))
        icone_html = icone_circular_html(caminho_icone)

        if icone_html:
            # Logo da instituição dentro de um círculo branco
            icone = folium.DivIcon(
                html=icone_html,
                icon_size=(TAMANHO_ICONE, TAMANHO_ICONE),
                icon_anchor=(TAMANHO_ICONE // 2, TAMANHO_ICONE // 2),   # centraliza no ponto
                class_name="marcador-instituicao",                      # usado pelo CSS de hover
            )
        else:
            # Sem ícone (arquivo ausente ou ilegível): marcador padrão
            icone = folium.Icon(
                color="darkblue",
                icon="map-marker",
                prefix="fa",
            )

        folium.Marker(
            location=[linha["lat"], linha["lon"]],
            tooltip=linha["University / Institute"],
            icon=icone,
        ).add_to(mapa)
    
    return mapa


def exibir_mapa():

    mapa = construir_mapa(df_institutions)

    st_data = st_folium(
        mapa,
        use_container_width=True,
        height=780,
        key="mapa_instituicoes",
        returned_objects=["last_object_clicked"],
    )

    # Verifica se um marcador foi clicado
    if st_data and st_data["last_object_clicked"]:

        ponto = st_data["last_object_clicked"]
        clique = (ponto["lat"], ponto["lng"])

        if st.session_state.get("ultimo_clique_tratado") != clique:

            st.session_state["ultimo_clique_tratado"] = clique

            selecionada = df_institutions[
                (df_institutions["lat"] == ponto["lat"]) &
                (df_institutions["lon"] == ponto["lng"])
            ]

            if not selecionada.empty:
                mostrar_instituicao(selecionada.iloc[0])

exibir_mapa()

st.dataframe(df)