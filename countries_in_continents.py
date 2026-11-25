
import unicodedata
import re

PAISES_POR_CONTINENTE = {

    "Africa": [
        "Algeria",
        "Angola",
        "Benin",
        "Botswana",
        "Burkina Faso",
        "Burundi",
        "Cabo Verde",
        "Cameroon",
        "Central African Republic",
        "Chad",
        "Comoros",
        "Côte d'Ivoire",
        "Democratic Republic of the Congo",
        "Djibouti",
        "Egypt",
        "Equatorial Guinea",
        "Eritrea",
        "Eswatini",
        "Ethiopia",
        "Gabon",
        "Gambia",
        "Ghana",
        "Guinea",
        "Guinea-Bissau",
        "Kenya",
        "Lesotho",
        "Liberia",
        "Libya",
        "Madagascar",
        "Malawi",
        "Mali",
        "Mauritania",
        "Mauritius",
        "Morocco",
        "Mozambique",
        "Namibia",
        "Niger",
        "Nigeria",
        "Republic of the Congo",
        "Rwanda",
        "São Tomé and Príncipe",
        "Senegal",
        "Seychelles",
        "Sierra Leone",
        "Somalia",
        "South Africa",
        "South Sudan",
        "Sudan",
        "Tanzania",
        "Togo",
        "Tunisia",
        "Uganda",
        "Zambia",
        "Zimbabwe"
    ],

    "Asia": [
        "Afghanistan",
        "Armenia",
        "Azerbaijan",
        "Bahrain",
        "Bangladesh",
        "Bhutan",
        "Brunei",
        "Cambodia",
        "China",
        "Cyprus",
        "Georgia",
        "India",
        "Indonesia",
        "Iran",
        "Iraq",
        "Israel",
        "Japan",
        "Jordan",
        "Kazakhstan",
        "Kuwait",
        "Kyrgyzstan",
        "Laos",
        "Lebanon",
        "Malaysia",
        "Maldives",
        "Mongolia",
        "Myanmar",
        "Nepal",
        "North Korea",
        "Oman",
        "Pakistan",
        "Palestine",
        "Philippines",
        "Qatar",
        "Saudi Arabia",
        "Singapore",
        "South Korea",
        "Sri Lanka",
        "Syria",
        "Tajikistan",
        "Thailand",
        "Timor-Leste",
        "Turkey",
        "Turkmenistan",
        "United Arab Emirates",
        "Uzbekistan",
        "Vietnam",
        "Yemen"
    ],

    "Europe": [
        "Albania",
        "Andorra",
        "Austria",
        "Belarus",
        "Belgium",
        "Bosnia and Herzegovina",
        "Bulgaria",
        "Croatia",
        "Czechia",
        "Denmark",
        "Estonia",
        "Finland",
        "France",
        "Germany",
        "Greece",
        "Holy See (Vatican City)",
        "Hungary",
        "Iceland",
        "Ireland",
        "Italy",
        "Latvia",
        "Liechtenstein",
        "Lithuania",
        "Luxembourg",
        "Malta",
        "Moldova",
        "Monaco",
        "Montenegro",
        "Netherlands",
        "North Macedonia",
        "Norway",
        "Poland",
        "Portugal",
        "Romania",
        "Russia",
        "San Marino",
        "Serbia",
        "Slovakia",
        "Slovenia",
        "Spain",
        "Sweden",
        "Switzerland",
        "Ukraine",
        "United Kingdom"
    ],

    "North America": [
        "Antigua and Barbuda",
        "Bahamas",
        "Barbados",
        "Belize",
        "Canada",
        "Costa Rica",
        "Cuba",
        "Dominica",
        "Dominican Republic",
        "El Salvador",
        "Grenada",
        "Guatemala",
        "Haiti",
        "Honduras",
        "Jamaica",
        "Mexico",
        "Nicaragua",
        "Panama",
        "Saint Kitts and Nevis",
        "Saint Lucia",
        "Saint Vincent and the Grenadines",
        "Trinidad and Tobago",
        "United States"
    ],

    "South America": [
        "Argentina",
        "Bolivia",
        "Brazil",
        "Chile",
        "Colombia",
        "Ecuador",
        "Guyana",
        "Paraguay",
        "Peru",
        "Suriname",
        "Uruguay",
        "Venezuela"
    ],

    "Oceania": [
        "Australia",
        "Fiji",
        "Kiribati",
        "Marshall Islands",
        "Micronesia (Federated States of)",
        "Nauru",
        "New Zealand",
        "Palau",
        "Papua New Guinea",
        "Samoa",
        "Solomon Islands",
        "Tonga",
        "Tuvalu",
        "Vanuatu"
    ],

    "Antarctica": []

}


# ==================================================
# NORMALIZAÇÃO DOS NOMES DOS PAÍSES
# ==================================================

def normalizar_nome(nome):

    texto = unicodedata.normalize(
        "NFKD",
        str(nome)
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = texto.casefold()

    texto = re.sub(
        r"[^a-z0-9]+",
        " ",
        texto
    )

    return texto.strip()


# ==================================================
# NOMES ALTERNATIVOS DOS PAÍSES
# ==================================================

ALIASES_PAISES = {

    "Ivory Coast": "Côte d'Ivoire",
    "Cape Verde": "Cabo Verde",
    "Swaziland": "Eswatini",
    "The Gambia": "Gambia",

    "DR Congo": "Democratic Republic of the Congo",
    "DRC": "Democratic Republic of the Congo",
    "Congo Kinshasa": "Democratic Republic of the Congo",
    "Congo, Democratic Republic of the": "Democratic Republic of the Congo",
    "Democratic Republic of Congo": "Democratic Republic of the Congo",

    "Congo Brazzaville": "Republic of the Congo",
    "Republic of Congo": "Republic of the Congo",
    "Congo": "Republic of the Congo",

    "Czech Republic": "Czechia",

    "Vatican City": "Holy See (Vatican City)",
    "Holy See": "Holy See (Vatican City)",

    "Turkiye": "Turkey",

    "Micronesia": "Micronesia (Federated States of)",

    "Burma": "Myanmar",

    "East Timor": "Timor-Leste",

    "Macedonia": "North Macedonia",

    "Russian Federation": "Russia",

    "United States of America": "United States",
    "USA": "United States",
    "US": "United States",

    "UK": "United Kingdom",

    "Republic of Korea": "South Korea",
    "Korea, Republic of": "South Korea",

    "Democratic People's Republic of Korea": "North Korea",
    "Korea, Democratic People's Republic of": "North Korea",

    "Viet Nam": "Vietnam",

    "Brunei Darussalam": "Brunei",

    "Iran, Islamic Republic of": "Iran",

    "Syrian Arab Republic": "Syria",

    "Tanzania, United Republic of": "Tanzania",

    "Bolivia, Plurinational State of": "Bolivia",

    "Venezuela, Bolivarian Republic of": "Venezuela",

    "Moldova, Republic of": "Moldova",

    "Lao People's Democratic Republic": "Laos",

    "Palestine, State of": "Palestine",

    # Nomes em português

    "Brasil": "Brazil",
    "Estados Unidos": "United States",
    "Reino Unido": "United Kingdom",
    "Alemanha": "Germany",
    "Espanha": "Spain",
    "França": "France",
    "Itália": "Italy",
    "Japão": "Japan",
    "Coreia do Sul": "South Korea",
    "Coreia do Norte": "North Korea",
    "Turquia": "Turkey",
    "Países Baixos": "Netherlands",
    "Holanda": "Netherlands",
    "África do Sul": "South Africa",
    "Egito": "Egypt",
    "Índia": "India",
    "China": "China",
    "Suíça": "Switzerland",
    "Suécia": "Sweden",
    "Noruega": "Norway",
    "Nova Zelândia": "New Zealand",
    "Vietnã": "Vietnam",
    "Rússia": "Russia",
    "México": "Mexico",
    "Argentina": "Argentina",
    "Colômbia": "Colombia",
    "Chile": "Chile",
    "Peru": "Peru",
    "Portugal": "Portugal"
}


# ==================================================
# DICIONÁRIO INVERSO: PAÍS -> CONTINENTE
# ==================================================

PAIS_PARA_CONTINENTE = {

    normalizar_nome(pais): continente

    for continente, paises in PAISES_POR_CONTINENTE.items()

    for pais in paises
}


# ==================================================
# IDENTIFICAÇÃO DO CONTINENTE
# ==================================================

def identificar_continente(pais):

    if pais is None:
        return None

    nome = normalizar_nome(pais)

    # Verifica se existe um nome alternativo
    if nome in {
        normalizar_nome(alias)
        for alias in ALIASES_PAISES
    }:

        for alias, nome_correto in ALIASES_PAISES.items():

            if nome == normalizar_nome(alias):

                nome = normalizar_nome(nome_correto)
                break

    return PAIS_PARA_CONTINENTE.get(nome)
