# Decisões e iterações — o processo, comentado

Guia de leitura do [`transcript-completo.md`](transcript-completo.md). Os
momentos abaixo são os que mudaram o rumo ou o resultado da análise.

A sessão teve **5 prompts principais** e durou ~5h15 (13:41 → 18:56 de
28/08/2026). O padrão foi deliberado: **nenhuma análise pesada rodou antes de um
plano escrito e aprovado.**

---

## Turno 1 — Diagnóstico antes de análise

**O que eu pedi:** ler os 5 arquivos, reportar o schema *real* (sem assumir
colunas), apontar problemas de qualidade e propor um plano. Explicitamente:
**não rodar a análise ainda.**

**O que saiu disso:** a descoberta que definiu toda a metodologia.

O `Price_AV_Itapema.csv` tem só **3 capturas** (06/01, 07/01, 20/01/2025) e
cobre 22,6% dos anúncios. A IA percebeu que **a ausência de linha é informação**
(data faltante = noite indisponível) — mas também percebeu a armadilha: a
indisponibilidade cai de 80% em janeiro para 22% em abril, o que é **curva de
booking, não ocupação**. Quem usasse "% indisponível" como ocupação concluiria
que janeiro rende 4× abril, por artefato de medição.

A saída proposta: comparar as capturas de 06/01 e 20/01. Noite disponível na
primeira e ausente na segunda **foi vendida nesses 14 dias**. Antes de escrever
o plano, ela rodou um teste de viabilidade (`03_teste_pickup.py`) para confirmar
que o sinal existia — 630 anúncios comparáveis, 14,2% de pickup.

> **Por que isso importa:** a métrica central do trabalho (`RevPAN`) nasceu de
> ler a estrutura do dado com atenção, não de aplicar uma fórmula padrão.

**Onde ver:** turno 1, blocos de raciocínio antes de `02_estrutura_disponibilidade.py`.
Resultado em [`analise/PLANO.md`](../analise/PLANO.md).

---

## Turno 2 — Aprovação do plano com 4 ajustes meus

Aprovei as 4 decisões metodológicas e pedi 5 ajustes. Dois viraram salvaguardas
importantes:

- **Definir `RevPAN` explicitamente como velocidade de venda normalizada**, não
  receita realizada — para o número não ser lido como faturamento. A IA passou a
  nomear a coluna `revpan_pickup` e abriu a seção 1 do relatório com um box de
  definição.
- **Registrar nos limites que o ROI cruza populações diferentes**: receita de
  imóveis maduros e ativos contra preço de imóveis à venda hoje.

**Uma correção de rumo dentro do turno:** ao calcular as métricas, apareceu que
**29,8% dos anúncios têm pickup zero**. A IA identificou que a mediana por
anúncio ficaria instável e trocou a agregação — passou a somar noites
(`noites vendidas ÷ noites ofertadas`) em vez de mediar medianas.

**Uma armadilha que ela testou e descartou:** o risco de censura no pickup — um
imóvel muito procurado já vendeu fevereiro, sobra estoque ruim, e ele apareceria
com pickup baixo. Testou: correlação entre estoque e pickup = **−0,055**. Não
havia censura. O teste ficou no código (`20_metricas_airbnb.py`).

---

## Turno 3 — Três aprofundamentos que eu exigi antes de gravar o vídeo

Este foi o turno mais produtivo, e o único em que **conclusões mudaram**.

### 3.1 A auditoria que inverteu o ranking

Pedi para ela trazer os 16 anúncios de compactos do Centro **um a um**, porque
eu não queria um número sustentado por erro de digitação escondido.

O que a auditoria encontrou:

| Problema | Achado |
|---|---|
| Duplicata física | Os 16 anúncios são **12 imóveis**. Um deles aparece 3 vezes, com corretores diferentes e URLs diferentes |
| Bairro errado | **5 dos 16 dizem "MEIA PRAIA" no próprio título** — e eram justamente os baratos |
| Tipologia errada | 1 anúncio de 140 m² com `bedrooms=1` e título "03 dormitórios" |

E o mais grave: **a base inteira do VivaReal tinha 18,2% de duplicatas físicas**.
A limpeza original deduplicava por `link_url`, e o mesmo imóvel anunciado por
dois corretores tem URLs diferentes.

**Consequência:** o preço mediano de Centro/2q subiu 8,1%, o ROI caiu de 5,97%
para 5,57%, e **o 1º lugar do ranking mudou** (Centro → Morretes). A recomendação
passou de "2 quartos no Centro" para "2 quartos, bairro indiferente — é empate
técnico".

> A auditoria **fortaleceu** a rejeição da tese dos compactos: o prêmio de m² no
> Centro subiu de +42% para **+60,5%**, porque os imóveis baratos que o
> mascaravam não eram do Centro.

**Onde ver:** turno 3, `70_compacto_centro.py` e `71_impacto_dedup.py`.

### 3.2 Onde a IA disse "não dá para responder"

Duas perguntas minhas não tinham resposta nos dados, e ela disse isso em vez de
inventar:

- **"Use lat/long do Mesh para achar compactos perto do Centro classificados em
  outro bairro."** → O VivaReal **não tem lat/long**. As coordenadas do Mesh são
  dos anúncios de Airbnb, e não há chave entre as bases. Ela usou o substituto
  possível (ler o bairro citado no título e na URL) e explicou a limitação.
- **"Dá para estimar a frequência de reposição de estoque de barganhas?"** → O
  VivaReal tem **uma única data de captura**. É fotografia, não série. A resposta
  foi: *"qualquer número seria inventado. Não vou inventar."*

Isso levou à **retirada de uma recomendação anterior**: eu havia aceitado a ideia
de que a tese dos compactos poderia se salvar como "estratégia de garimpo". Com o
IC95 do p25 em R$ 650k–890k e P(p25 ≤ ponto de virada) = **59,4%**, virou o que
é: uma aposta de moeda, não uma estratégia. Foi removida do relatório.

### 3.3 A auto-correção estatística

Eu desconfiei do R² negativo que ela havia reportado e pedi para testar com
modelos regularizados e validação repetida antes de aceitar "a demanda não é
explicável".

**Eu estava certo, e ela reconheceu sem rodeios.** O R² de −0,246 era
**overfitting do Gradient Boosting**, não ausência de fenômeno. Com Ridge, o
valor subiu para ≈0.

Mas a conclusão sobreviveu, com evidência mais forte — porque ela montou os
controles certos:

| Alvo | Melhor modelo | R² fora da amostra | % folds > 0 |
|---|---|---|---|
| **ADR (controle positivo)** | RandomForest | **0,431** | 100% |
| Ocupação de fevereiro | Ridge | 0,078 | 100% |
| pickup ajustado | Ridge | −0,002 | 60% |
| *alvo embaralhado (piso)* | Ridge | *−0,012* | *0%* |

O controle positivo prova que o pipeline detecta sinal quando existe. A leitura
correta virou "explica pouco" (razão ~5:1 entre preço e demanda), não "não
explica nada" — e o relatório registra o erro explicitamente na seção 4.

### 3.4 O achado que ninguém pediu

Investigando a divergência de nomenclatura, ela descobriu que **Andorinha e
Castelo Branco são sub-áreas de Meia Praia** — o título/URL confirma em 91,7% e
94,3% dos casos. Isso resolveu um ponto cego de **19% do mercado de venda** que
estava listado como limitação do relatório.

### 3.5 A ressalva que mudou o enquadramento

Pedi para contextualizar o retorno de ~6% com números, não como afirmação solta.
Ela buscou a taxa vigente (**Selic 14,00%**, Copom de 05/08/2026) e calculou o
que seria preciso para fechar o gap:

- só ocupação → precisaria de **130,6%** (impossível)
- só ADR → **+137%**, contra p90 da cidade de R$ 700
- só preço de compra → **−66%**
- +20% de ADR **e** +20% de ocupação juntos → 8,24%, ainda abaixo
- o prêmio de operação profissional medido nos dados fecha **11% do gap**

Conclusão: o caso de investimento só fecha com ~8,3% a.a. de valorização — que a
base não permite avaliar. Isso virou a seção 5.5 e reposicionou o relatório
inteiro.

---

## Turno 4 — Reescrita integrada

Pedi para incorporar tudo nas seções certas, não como adendo, e fui explícito:
**não amenizar os números para parecer uma recomendação mais confortável.**

O relatório final assume as duas coisas desconfortáveis: o bairro não é
decidível, e o investimento não fecha por yield.

---

## Turno 5 — Auditoria de entrega

Verificação do repositório contra o checklist do desafio: estrutura, README,
consistência de números entre versões, `.gitignore`, e geração desta pasta.

---

## O que eu tiraria como aprendizado

1. **O plano antes do código valeu mais que o código.** A decisão de não usar
   "% indisponível" como ocupação foi tomada no turno 1 e evitou uma análise
   inteira errada.
2. **Pedir para auditar linha a linha achou o que agregado nenhum acharia.** As
   duplicatas por corretor não apareciam em nenhuma estatística resumo — só
   olhando os 16 registros.
3. **Desconfiar de um número bom é tão importante quanto desconfiar de um ruim.**
   O R² negativo parecia sustentar minha narrativa favorita ("a operação é que
   importa"). Era artefato.
4. **A IA disse "não sei" três vezes**, e essas foram as respostas mais úteis da
   sessão.
