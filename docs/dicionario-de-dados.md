# Dicionário de dados

## Entrada

O grão é uma pessoa por ID na fotografia cadastral. Os nomes das colunas têm espaços externos removidos. Dados sintéticos são lidos em UTF-8. O leitor também aceita Windows-1252 para entradas locais.

| Coluna obrigatória | Tipo recebido | Tratamento |
|---|---|---|
| Cód Funcionário | Texto ou número identificador | ID único e preenchido. Strings preservam zeros à esquerda no leitor CSV |
| Cargo | Texto | Normalização de acentos, caixa e espaços para consultar o dicionário |
| Tipo Contrato | Texto | Empregado, Aprendiz, Estagiário ou Diretor |
| Escolaridade | Texto | Mapeamento explícito da descrição para o nível frequentado |
| Situação | Texto | Associação a vínculo existente, desligado ou situação desconhecida |
| Data Admissão | ISO ou DD/MM/YYYY | Conversão para data em coluna separada |
| Data Afastamento | ISO ou DD/MM/YYYY, com ausência permitida | Fim do vínculo somente para pessoas desligadas |
| Data Nascimento | ISO ou DD/MM/YYYY | Base do cálculo de idade completa |
| Valor Salário | Número ou moeda brasileira em texto | Conversão para número em coluna separada |

O CSV sintético também contém `Funcionário`, com rótulos como `Pessoa sintética 0001`. Outras colunas de origem são preservadas, sem participar das regras.

## Campos calculados

| Campo | Conteúdo |
|---|---|
| `id_pessoa` | ID normalizado em texto |
| `cargo_normalizado` | Cargo para consulta do dicionário |
| `cargo_agrupado` | Categoria descritiva que reúne cargos com menos de cinco ocorrências |
| `setor` | Setor definido por cargo ou Não mapeado |
| `contrato` | Contrato padronizado ou Não informado |
| `situacao_vinculo` | Com vínculo, Sem vínculo ou Não informada |
| `escolaridade_simplificada` | Fundamental, Médio, Superior, Pós-graduação ou Não informada |
| `data_admissao`, `data_afastamento`, `data_nascimento` | Datas tratadas |
| `idade`, `tempo_casa_anos` | Anos completos, com ausência preservada quando o cálculo não é possível |
| `faixa_etaria`, `faixa_salarial` | Categorias descritivas da idade e do salário |
| `salario_numerico` | Salário convertido, sem imputação ou teto |
| `qualidade_*` | Flags para valores desconhecidos, formatos inválidos, datas e mapeamentos |
| `revisar_dados` | Indica a existência de pelo menos uma pendência |
| `pontos_*` | Pontuações separadas para os cinco programas |
| `programa_sugerido` | Programa com maior pontuação, Nenhum ou Não simulado |
| `pontuacao_programa` | Maior pontuação encontrada |
| `programas_empatados`, `houve_empate` | Programas com a mesma pontuação máxima e sinalização do empate |
| `justificativa` | Critérios que pontuaram ou motivo para aguardar revisão |
| `status_simulacao` | Simulação concluída, Sem correspondência, Revisar dados ou Fora do público de demonstração |
| `pontuacao_perfil_exploratorio` | Combinação manual de características, com intervalo teórico de 0 a 10 |

O relatório de qualidade retorna as quantidades de linhas recebidas e tratadas, duplicatas exatas removidas, pessoas com pendências e ocorrências por regra. As ocorrências podem se sobrepor em uma mesma pessoa.

## Fonte previamente tratada

Entradas com as colunas `Programa`, `score_retencao`, `idade` ou `programa_sugerido` são recusadas para evitar reaplicar o fluxo sobre resultados anteriores. O arquivo do protótipo já continha campos derivados e valores modificados. A reconstrução dos dados originais exige uma extração de origem.
