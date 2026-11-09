# Metodologia da demonstração

## Base e data de referência

O projeto público utiliza perfis sintéticos gerados com a semente 42. Foram inseridos casos de salário ausente, valor inválido, data ausente, data impossível, cronologia invertida, cargo desconhecido, cargo com classificação conflitante e duplicata exata. Isso permite observar e testar as decisões do tratamento.

A referência é 09/11/2026 e pode ser alterada no notebook. Idade e tempo de casa usam aniversários completos. Para quem nasceu em 29 de fevereiro, em anos sem esse dia a comparação de mês e dia completa o aniversário em 1º de março. O público deriva da situação na fotografia recebida.

## Tratamento

- A entrada permanece intacta. As colunas novas usam nomes em minúsculas com separadores `_`.
- Duplicatas inteiramente iguais são removidas. IDs ausentes ou repetidos em linhas diferentes interrompem a carga, pois o grão esperado é uma pessoa por ID.
- Datas ISO e `DD/MM/YYYY` são aceitas. Datas impossíveis viram valores ausentes na coluna tratada e recebem uma flag de qualidade. O texto original é preservado.
- A admissão ou o nascimento ausentes impedem a simulação. Uma pessoa desligada com afastamento sem data permanece com tempo de casa desconhecido.
- Para pessoas com vínculo, uma data de férias ou licença não encerra o tempo de casa. Para desligados, a data de afastamento é usada como fim do vínculo.
- Datas posteriores ao recorte, nascimento após admissão e afastamento anterior à admissão geram revisão.
- Números e textos como `10000.0`, `R$ 1.234,56` e `1.500` são convertidos sem modificar o valor original. A convenção para pontos isolados com grupos de três dígitos é de milhar brasileiro. Outros formatos precisam ser conferidos.
- Salários não positivos ou inválidos geram pendência. Os limites ilustrativos de 600 e 50.000 sinalizam conferência. Não alteram o valor e não representam pisos ou tetos legais.
- Escolaridade é associada por descrição ao nível frequentado. Superior completo e incompleto permanecem no grupo Superior, com sua descrição original disponível. O uso do nível frequentado como critério do programa é uma suposição a validar.
- O mapa de cargos do protótipo foi preservado. Após normalizar acentos e caixa, cargos associados a mais de um setor ficam sem mapeamento. A classificação final exige conferência do domínio.
- Agrupar cargos raros serve à descrição da base. O setor é calculado antes desse agrupamento.

## Público da simulação

Trabalhando, Ativo, Férias e as licenças listadas no dicionário são interpretados como vínculo existente. Demitido e Desligado ficam fora da simulação de programas. Situações desconhecidas exigem revisão. O vínculo cadastral, por si só, não estabelece elegibilidade efetiva para qualquer programa.

Registros com pendências não recebem pontuação ou sugestão. Registros com dados completos e vínculo conhecido passam pelas regras abaixo. Um registro pode ter pendências e estar desligado ao mesmo tempo. O status exibido prioriza a separação do público, mantendo as flags de qualidade disponíveis.

## Pontuações dos programas

| Programa | Condição de entrada | Pontos adicionais |
|---|---|---|
| Conecta Carreira | Aprendiz ou Estagiário recebe 3 | Idade até 25 recebe 2, salário até 3.000 recebe 2 e escolaridade fundamental ou média recebe 1 |
| Direcionamento Head | Empregado ou Diretor em Administrativo, Comercial, Financeiro, TI, Marketing ou RH recebe 2 | Tempo acima de 5 anos recebe 2, idade acima de 40 recebe 2 ou entre 30 e 40 recebe 1, salário acima de 6.000 recebe 2 e escolaridade superior ou pós recebe 1 |
| DataDrive | Escolaridade superior ou pós e pelo menos 1 ano de casa | Administrativo recebe 3, Marketing ou Logística recebe 2, TI ou Financeiro recebe 1,5 e os demais setores mapeados recebem 1. Idade até 30 acrescenta 2. Empregado, Aprendiz ou Estagiário acrescenta 1 |
| Crescer Juntos | Empregado em Produção, Logística ou Engenharia / Manutenção recebe 2 | Idade entre 26 e 35 recebe 2, salário acima de 1.500 e até 6.000 recebe 2, escolaridade média ou superior recebe 1 e até 5 anos de casa recebe 1 |
| Liderança Sustentável | Empregado ou Diretor com mais de 35 anos recebe 2 | Salário acima de 6.000 recebe 2, escolaridade superior ou pós recebe 1 e mais de 10 anos de casa recebe 2 |

A sugestão usa a maior pontuação. Se nenhuma regra pontuar, o resultado é `Nenhum`. O programa escolhido fica acompanhado de seus motivos e de todas as pontuações dos programas.

Em um empate, os programas empatados são registrados. O rótulo demonstrativo respeita a prioridade Conecta Carreira, DataDrive, Crescer Juntos, Direcionamento Head e Liderança Sustentável, herdada do protótipo. Essa prioridade precisa de validação antes de uso operacional.

## Pontuação exploratória do perfil

A coluna `pontuacao_perfil_exploratorio` substitui o nome `score_retencao`. Ela soma 2 para tempo de casa a partir de 2 anos, 2 para idade entre 30 e 50, 1 para salário inferior a 3.000, 1 para setores Administrativo, RH ou TI, 1 para escolaridade superior ou pós e 1 para contrato Empregado ou Diretor. A partir de 5 pontos, soma mais 2. O intervalo teórico é de 0 a 10.

Essa pontuação é apresentada para discutir a regra original. A escolaridade agora usa o nível explicitamente mapeado, em vez de comparar códigos de origem por ordem numérica. A pontuação de perfil não seleciona o programa e não foi validada para estimar retenção ou risco individual.

## Próxima avaliação com RH

A finalidade dos programas, o público, o significado da escolaridade incompleta e os critérios por cargo precisam ser acordados com os responsáveis. A avaliação também precisa considerar como idade e salário influenciam o acesso às oportunidades, o efeito dos empates e a cobertura dos cargos mapeados. Uma futura avaliação de retenção exige um alvo observado, janelas temporais definidas e validação independente dos resultados.
