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
from countries_in_continents import identificar_continente

st.html(
    """
    <style>
    .block-container { max-width: 1100px; }
    </style>
    """
)

# Carregamento dos dados
institutions, researchers = carregarDados()
avisos = montarAvisos(institutions, researchers)
df_institutions, df_researchers = limparLinhasInvalidas(institutions, researchers)

DATA_PATH = "./data"
ICONS_PATH = Path(DATA_PATH) / "icons"      # ./data/icons/[ID_DA_INSTITUIÇÃO].[EXTENSÃO]
EXTENSOES_ICONE = {".png", ".svg", ".jpg", ".jpeg", ".webp", ".gif", ".ico"}
TAMANHO_ICONE = 44                          # diâmetro do círculo branco, em pixels

@st.cache_data
def carregar_dados():
    return pd.read_excel(DATA_PATH + "/institutions-and-researchers.xlsx")

df = carregar_dados()


@st.cache_data
def carregar_geojson():
    with open("continents.geojson", "r", encoding="utf-8") as f:
        return json.load(f)


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

    geojson_data = carregar_geojson()

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

#menu retratil
if "pais_menu" not in st.session_state:
    st.session_state["pais_menu"] = None
 
def abrir_pais(pais):
    st.session_state["pais_menu"] = pais
 
def voltar():
    st.session_state["pais_menu"] = None
 
@st.fragment
def menu_regioes(df_inst, df_pesq):
    df_pi = df_pesq.merge(df_inst, on="institution_id", how="inner")
 
    por_pais = df_pi.groupby("Country")["researcher_id"].nunique()
    paises_menu = sorted(df_inst["Country"].dropna().unique())
 
    if st.session_state["pais_menu"] not in paises_menu:
        st.session_state["pais_menu"] = None
 
    pais_aberto = st.session_state["pais_menu"]
 
    with st.container(horizontal_alignment="right"):
        with st.popover("Mais informações"):
 
            if pais_aberto is None:
                st.subheader("All regions")
                st.caption(
                    f"{df_pi['researcher_id'].nunique()} researchers · "
                    f"{df_inst['institution_id'].nunique()} institutions · "
                    f"{df_inst['Country'].nunique()} countries"
                )
 
                with st.container(height=420, border=False):
                    for pais in paises_menu:
                        st.button(
                            f"{pais} · {int(por_pais.get(pais, 0))}",
                            key=f"btn_{pais}",
                            on_click=abrir_pais,
                            args=(pais,),
                            width="stretch",
                        )
 
            else:
                st.button(
                    "← All regions",
                    key="btn_voltar",
                    on_click=voltar,
                )
 
                inst_pais = df_inst[df_inst["Country"] == pais_aberto]
                pesq_pais = df_pi[df_pi["Country"] == pais_aberto]
                continente = ", ".join(
                    sorted(inst_pais["Continent"].dropna().unique())
                )
 
                st.subheader(pais_aberto)
                st.caption(
                    f"{pesq_pais['researcher_id'].nunique()} researchers · "
                    f"{inst_pais['institution_id'].nunique()} institutions · "
                    f"{continente or '-'}"
                )
 
                with st.container(height=420, border=False):
                    for _, inst in inst_pais.sort_values(
                        "University / Institute"
                    ).iterrows():
                        nomes = (
                            pesq_pais[
                                pesq_pais["institution_id"]
                                == inst["institution_id"]
                            ]["Research Name"]
                            .dropna()
                            .astype(str)
                            .str.strip()
                            .sort_values()
                            .tolist()
                        )
                        st.markdown(f"**{inst['University / Institute']}**")
                        if nomes:
                            st.markdown("\n".join(f"- {nome}" for nome in nomes))
                        else:
                            st.caption("Não foram encontradas informações.")
 
 
menu_regioes(df_filtrado, df_researchers)


def exibir_mapa(df_filtrado):
    # ATENÇÃO: o mapa é reconstruído a CADA execução, de propósito.
    # O st_folium reescreve os `_id` dos elementos do objeto folium ao gerar o
    # script do mapa. Se o mesmo objeto for reaproveitado (ex.: guardado no
    # st.session_state), o script gerado no rerun seguinte vem diferente e a
    # chave do componente muda -> o mapa é recriado quebrado e "some".
    # Com um mapa novo, o script só muda quando os marcadores mudam (filtros),
    # e aí o componente é recriado do jeito certo.
    mapa = construir_mapa(df_filtrado)

    st_data = st_folium(
        mapa,
        use_container_width=True,
        height=780,
        key="mapa_instituicoes",
        returned_objects=["last_object_clicked", "last_object_clicked_count"],
    ) or {}

    ponto = st_data.get("last_object_clicked")
    contagem = st_data.get("last_object_clicked_count")

    # Sem clique registrado (mapa recém-criado, por exemplo após mudar um
    # filtro): libera o próximo clique, mesmo que seja no mesmo ícone.
    if not ponto or "lat" not in ponto or "lng" not in ponto:
        st.session_state.pop("ultimo_clique_tratado", None)
        return None

    latitude = ponto["lat"]
    longitude = ponto["lng"]

    # O contador sobe a cada clique, então clicar de novo no mesmo ícone
    # (depois de fechar o modal) também abre o modal outra vez, enquanto
    # reruns causados por outros widgets (ex.: digitar na busca) não reabrem.
    clique = (contagem, latitude, longitude)
    if st.session_state.get("ultimo_clique_tratado") == clique:
        return None

    selecionada = df_filtrado[
        ((df_filtrado["lat"] - latitude).abs() < 0.000001)
        & ((df_filtrado["lon"] - longitude).abs() < 0.000001)
    ]

    # Clique em um continente (e não em um ícone): nada a abrir
    if selecionada.empty:
        return None

    st.session_state["ultimo_clique_tratado"] = clique
    return selecionada.iloc[0]


instituicao_selecionada = exibir_mapa(df_filtrado)

if instituicao_selecionada is not None:
    mostrar_instituicao(
        instituicao_selecionada
    )