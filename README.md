# 🌎️ Globe Gen AI 🤖

O projeto consiste na elaboração de um *software web* que permita a visualização em um mapa mundi das instituições registradas em um determinado `dataset`.

## Colaboradores

- Felipe
- Julia
- Mariana
- Rafael

## Stack

- Python
- Pandas
- Streamlit + Folium

## Requisitos

| Número do Requisito | Tipo          | Descrição                                                                                                                                                                                                                                                  |
| ------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **RF-01**           | Funcional     | O mapa deve ter um indicador para cada instituição participante e ao passar o mouse por cima de um deles, deve ser exibido algumas informações como: nome da universidade, país, cidade/localização e nome dos pesquisadores vinculados àquela instituição |
| **RNF-01**          | Não Funcional | O mapa não deve utilizar as fronteiras para os países fornecidas pelo Google Maps. Em vez disso, deve exibir apenas o contorno do continente de cada participante, acompanhado da geolocalização das instituições.                                         |
| **RF-02**           | Funcional     | O mapa deve ter um menu esquerdo flutuante retrátil, que ao ser selecionado, exibe informações como: número de universidades, pesquisadores e países participantes                                                                                         |
| **RF-03**           | Funcional     | O mapa deveria permitir que sejam filtrados: participantes por regiões e continentes, além de pesquisar os nomes dos pesquisadores, países ou universidades.                                                                                               |
| **RF-04**           | Funcional     | Cada indicador pode conter uma opção de rota que leva à sua posição no Google Maps e à requisição de entrada do ponto de partida, para calculo da trajetória até a instituição participante                                                                |
| **RF-05**           | Funcional     | O sistema pode permitir que quando um pesquisador participante é selecionado, sejam exibidas informações de contato a que ele(a) esteja de acordo, como e-mail, Linkedin, Instagram e páginas web pessoais.                                                |
| **RF-06**           | Funcional     | O mapa deveria permitir que o usuário altere o zoom em áreas específicas com o scroll do mouse, ao posicionar o cursor sobre uma zona.                                                                                                                     |

## Legenda do Mapa

- **América Do Norte:** #8e6bbf
- **América Do Sul:** #7cb342
- **Europa:** #5b8def
- **Ásia:** #d9534f
- **Oceania:** #2fb59a
- **Antártica:** #cfd8dc
