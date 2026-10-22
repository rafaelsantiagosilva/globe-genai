import pandas as pd

def carregarDados():
  institutions = pd.read_csv('data/institutions.csv')
  researchers = pd.read_csv('data/researchers.csv')
  return institutions, researchers

def verificaCoordenadaVazia(institutions):
  # verifica se as colunas lat ou lon estao vazias passando por um filtro que armazena essas linhas vazias
  lat_vazia = institutions["lat"].isna()
  lon_vazia = institutions["lon"].isna()
  linha_vazia = lat_vazia | lon_vazia
  return institutions[linha_vazia]

def validacaoCoordenadas(institutions):
  # verifica se as colunas lat e lon estão fora do padrão número minimo e maximo utilizado, aramazenando em um filtro os que forem True
  lat_invalida = ~institutions["lat"].between(-90, 90) & institutions["lat"].notna()
  lon_invalida = ~institutions["lon"].between(-180, 180) & institutions["lon"].notna()
  coord_fora = lat_invalida | lon_invalida
  return institutions[coord_fora]

def pesquisadorInstituicaoInexistente(institutions, researchers):
  # faz a verificacao de quais pesquisadores estao com um id inexistente de instituicoes
  pesquisador_orfao = ~researchers["institution_id"].isin(institutions["institution_id"]) & researchers["institution_id"].notna()
  
  return researchers[pesquisador_orfao]

def pesquisadorSemInstituicao(researchers):
  # verifica linhas no qual o pesquisador esta com id de instituicao vaiza
  id_inst_vazio = researchers["institution_id"].isna()
  return researchers[id_inst_vazio]

def instituicaoSemPesquisador(institutions, researchers):
  # verifica linhas no qual a instituicao não tem nenhum pesquisador alocado
  id_pesq_vazio = ~institutions["institution_id"].isin(researchers["institution_id"]) & institutions["institution_id"].notna()

  return institutions[id_pesq_vazio]


def limparLinhasInvalidas(institutions, researchers):
  # devcolve as tabelas limpas
  sem_coord = verificaCoordenadaVazia(institutions)
  invalidas = validacaoCoordenadas(institutions)
  # Instituições limpas: fica só quem NÃO está em sem_coord E NÃO está em invalidas
  institutions_limpas = institutions[~institutions["institution_id"].isin(sem_coord["institution_id"])
  & ~institutions["institution_id"].isin(invalidas["institution_id"])
  ]

  #  fica só quem aponta para uma instituição que sobrou.
  # e quem apontava para uma instituição que acabou de sair.
  researchers_limpos = researchers[researchers["institution_id"].isin(institutions_limpas["institution_id"])
  ]

  # devolve duas tabelas novas. as originais não são alteradas.
  return institutions_limpas, researchers_limpos

def montarAvisos(institutions, researchers):
  avisos = []
  
  coord_vazia = verificaCoordenadaVazia(institutions)
  if len(coord_vazia) > 0:
    avisos.append({"id": "coordenada_vazia", "texto": f"tem {len(coord_vazia)} linhas com coordenadas vazias.", "detalhes": coord_vazia})
    
  coord_invalida = validacaoCoordenadas(institutions)
  if len(coord_invalida) > 0:
    avisos.append({"id": "coordenada_invalida", "texto": f"Foram encontradas {len(coord_invalida)} coordenadas inválidas.", "detalhes": coord_invalida})
    
  pesq_cinsti_inv = pesquisadorInstituicaoInexistente(institutions, researchers)
  if len(pesq_cinsti_inv) > 0:
    avisos.append({"id": "pesquisador_com_id_de_instituicao_inexistente", "texto": f"Foram econtrados {len(pesq_cinsti_inv)} pesquisadores com ID de Instituições Inexistentes.", "detalhes": pesq_cinsti_inv})
    
  pesq_sinst = pesquisadorSemInstituicao(researchers)
  if len(pesq_sinst) > 0:
    avisos.append({"id": "pesquisador_sem_id_de_instituicao", "texto": f"Foram econtrados {len(pesq_sinst)} pesquisadores sem ID de Instituição.", "detalhes": pesq_sinst})
    
  inst_spesq = instituicaoSemPesquisador(institutions, researchers)
  if len(inst_spesq) > 0:
    avisos.append({"id": "instituicao_sem_pesquisador_relacionado", "texto": f"Foram econtradas {len(inst_spesq)} instituições sem ID de Pesquisadores Relacionados.", "detalhes": inst_spesq})
  
  return avisos
  
if __name__ == "__main__":
  institutions, researchers = carregarDados()
  inst_limpas, pesq_limpos = limparLinhasInvalidas(institutions, researchers)
  print(len(inst_limpas), len(pesq_limpos))  
  print(len(institutions), len(researchers)) 
  avisos = montarAvisos(institutions, researchers)
  for aviso in avisos:
    print(aviso["texto"])
    print(len(aviso["detalhes"]))