# Contexto do projeto

Este é um desafio individual (take-home de 1 dia) da Seazone, empresa de gestão
de short stay. O objetivo é analisar dados reais do mercado imobiliário de
Itapema/SC e recomendar onde e no que a Seazone deveria investir.

Este projeto **é avaliado tanto pela qualidade da análise quanto pelo processo
de uso da IA** (raciocínio, iteração, senso crítico registrado no ai-log/).
Por isso, priorize clareza de raciocínio sobre velocidade de execução.

## Perguntas que a análise precisa responder

1. Melhor perfil de imóvel para investir (tipologia, nº de quartos, tipo de anúncio)
2. Melhor localização em termos de receita
3. Quais características explicam as melhores receitas
4. Recomendação de compra + estimativa simples de retorno, com justificativa
5. Posição sobre a tese interna: "studios/1 quarto no Centro é a aposta mais eficiente" — os dados sustentam ou não?

## Dados (em /data)

- `Details_Itapema.csv` — anúncios do Airbnb: título, reviews, rating, host_id, nº de quartos, tipo de imóvel
- `Hosts_ids_Itapema.csv` — dados do anfitrião (liga por owner_id)
- `Mesh_Ids_Data_Itapema.csv` — lat/long e bairro (liga por listing)
- `Price_AV_Itapema.csv` — preço por anúncio, por data de estadia e de captura (liga por listing)
- `VivaReal_Itapema.csv` — anúncios de venda: preço, condomínio, área

## Como trabalhar comigo neste projeto

- **Antes de rodar análise pesada, explique seu raciocínio primeiro.** Descreva o
  schema real dos dados (não assuma colunas — confira), aponte problemas de
  qualidade de dado, e proponha um plano antes de executar.
- **Não pule direto para a resposta final.** Prefiro decisões incrementais que eu
  possa revisar e discutir, mesmo que isso gere mais idas e vindas — isso é
  intencional e faz parte do processo avaliado.
- **Seja explícito sobre suposições.** Se uma métrica ou critério for ambíguo
  (ex: o que conta como "melhor localização"), diga qual critério está usando e
  por quê, em vez de decidir silenciosamente.
- **Aponte quando os dados não sustentam algo**, mesmo que contrarie a hipótese
  que eu levantei. Não force uma conclusão para agradar.

## Convenções

- Código de análise vai em `/analise`
- Conclusões e recomendação final vão em `relatorio.md` (não só no chat)
- Nunca commitar dados sensíveis ou credenciais