# Onde a Seazone deveria investir em Itapema/SC

Análise de 4.441 anúncios de Airbnb e 5.865 apartamentos à venda (após correções).
Código em [`/analise`](analise/), dados intermediários em [`/analise/saida`](analise/saida/).

---

## Resposta curta

Há duas respostas, e a segunda importa mais que a primeira.

**1. Sobre o perfil do imóvel — conclusão firme.**
Apartamento de **2 quartos**. Não studio. As três melhores células do mercado
são todas de 2 quartos, e a diferença para 3 e 4+ quartos é grande e estável.

**2. Sobre qual bairro — os dados não decidem.**
Depois de corrigir 18,2% de duplicatas físicas na base de venda, o topo virou
empate técnico:

| Célula | ROI operacional | Investimento |
|---|---|---|
| Morretes / 2q | **5,67%** | R$ 937 mil |
| Centro / 2q | **5,57%** | R$ 1,40 mi |
| Meia Praia / 2q | **5,50%** | R$ 1,24 mi |

Dezessete centésimos de ponto separam o primeiro do terceiro. **Não é diferença
real** — é ruído. Quem afirmar "o Centro é o melhor bairro" com estes dados está
lendo precisão que eles não têm.

**3. E a pergunta que vem antes de todas — a mais desconfortável.**
Com a **Selic em 14,00%** e o **CDI em 13,90%** (Copom, 05/08/2026), um retorno
operacional de 5,5% a 6,5% entrega **40% do que o mesmo capital renderia no CDI**,
sem risco, sem iliquidez e sem trabalho operacional. Nenhuma alavanca operacional
plausível fecha esse gap — nem +20% de preço e +20% de ocupação simultâneos.

> **Comprar short stay em Itapema hoje só se justifica como aposta em
> valorização do imóvel — não como investimento em renda.** Seria preciso
> ~8,3% a.a. de valorização só para empatar com o CDI, e esta base é uma
> fotografia de um momento: não permite avaliar valorização.

**Sobre a tese interna dos compactos no Centro: os dados não a sustentam** — e a
rejeição ficou mais forte depois da auditoria de dados. Detalhe na seção 6.

---

## 1. Método — e o que "RevPAN" significa aqui

### A restrição que definiu tudo

`Price_AV_Itapema.csv` tem **apenas 3 capturas** (06/01, 07/01 e 20/01/2025),
cada uma projetando 91 dias à frente, cobrindo estadias de **06/01 a 20/04/2025**.
Não existe reserva realizada na base, não existe inverno, e só 22,6% dos
anúncios têm preço.

Dentro da janela de uma captura, **a ausência de linha é informação**: data
faltante = noite indisponível. Mas indisponibilidade cresce quanto mais perto a
data (80% em janeiro contra 22% em abril) — isso é **curva de booking, não
ocupação**. Quem usar "% indisponível" como ocupação vai concluir que janeiro
rende 4× abril por artefato de medição.

### A saída: medir reservas entre capturas

As capturas de 06/01 e 20/01 têm 77 noites de janela comum. Se uma noite estava
disponível em 06/01 e sumiu em 20/01, **ela foi vendida nesses 14 dias**.

> ### Definição de RevPAN (leia antes de usar o número)
>
> **`RevPAN = ADR × pickup`**, onde `pickup` é a fração das noites ofertadas em
> 06/01 que foram vendidas até 20/01.
>
> **Isto não é receita realizada da temporada.** É uma **velocidade de venda
> normalizada por preço** — quanto de receita cada noite disponível gera por
> janela de 14 dias de comercialização. Serve para **ranquear** imóveis
> comparáveis, não para dizer quanto um imóvel faturou.
>
> RevPAN de R$ 91 **não** significa R$ 91 por noite de receita, nem
> R$ 91 × 30 por mês. A receita usada no cálculo de retorno (seção 5) vem de
> outra métrica, a ocupação de fevereiro.

O pickup bruto engana, porque o pickup de mercado cai de 43,9% (jan) para 3,4%
(abr): um imóvel com estoque concentrado em fevereiro pareceria mais demandado
sem ser. Corrigimos por **padronização indireta** — o pickup observado é
dividido pelo pickup esperado dado o mix de datas daquele anúncio.

**Por que RevPAN e não ADR:** a correlação entre preço e velocidade de venda é
**−0,227** (Spearman). Quem cobra mais vende mais devagar. Ranquear por ADR
premiaria o imóvel caro e vazio.

### Duas métricas, dois papéis

| Métrica | O que é | Para que serve |
|---|---|---|
| `pickup_ajustado` | noites vendidas em 14 dias ÷ noites ofertadas | **ranquear** (578 anúncios) |
| `ocup_fev` | % dos 28 dias de fevereiro indisponíveis, visto de 20/01 | **estimar receita** (780 anúncios) |

Testei se o pickup sofria censura (imóvel muito procurado já vendeu fevereiro e
só lhe sobra estoque ruim). **Não sofre** — a correlação entre estoque
disponível e pickup é −0,055, praticamente zero.

As duas métricas concordam apenas moderadamente (Spearman 0,44). Isso é um
limite real e está na seção 7.

### Universo

4.441 anunciados → **1.005 com alguma linha de preço** (22,6%) → **780 presentes
na captura de 20/01**, usada para ADR e ocupação → **578 com pickup válido**
(mínimo de 20 noites ofertadas). Bairros entram no ranking com **n ≥ 20**; abaixo
disso vão para o apêndice da seção 8, com os números à vista.

### Correções aplicadas à base de venda

Duas auditorias posteriores mudaram números deste relatório e estão integradas
em todas as tabelas:

- **Deduplicação por ficha física.** A limpeza inicial deduplicou por `link_url`,
  mas o mesmo imóvel aparece com URLs diferentes quando dois corretores o
  anunciam. Deduplicando por (preço + área + quartos + banheiros + vagas):
  **7.181 → 5.874 imóveis, 18,2% da base era repetição.**
- **Andorinha e Castelo Branco reclassificados como Meia Praia** (seção 3).
- **9 falsos compactos removidos** — `bedrooms ≤ 1` no dado, mas o título indica
  2 ou mais dormitórios. Base final: **5.865 imóveis**.

---

## 2. Melhor perfil de imóvel

### Tipologia e número de quartos

| Faixa | n | ADR | pickup | **RevPAN** | ocup. fev |
|---|---|---|---|---|---|
| 4+ quartos | 37 | R$ 946 | 11,3% | **R$ 107** | 47,1% |
| 3 quartos | 270 | R$ 650 | 13,7% | **R$ 89** | 48,6% |
| 0-1 (compacto) | 87 | R$ 471 | 15,6% | **R$ 73** | 45,5% |
| 2 quartos | 184 | R$ 457 | 14,2% | **R$ 65** | 51,7% |

O compacto tem o **maior pickup da cidade** (15,6%) — vende mais rápido, como a
tese previa. Mas o ADR mais baixo anula a vantagem: em receita por noite
disponível ele fica em terceiro.

**Atenção à leitura:** esta tabela é de *receita*, e nela 2 quartos aparece por
último. A recomendação de 2 quartos vem do **retorno sobre o capital**
(seção 5) — o imóvel grande gera mais receita, mas custa desproporcionalmente
mais para comprar.

### Tipo de anúncio

| Tipo | n | ADR | pickup | RevPAN |
|---|---|---|---|---|
| Apartamento | 567 | R$ 546 | 14,1% | **R$ 77** |
| Casa | 11 | R$ 440 | 10,9% | R$ 48 |

Apartamento domina — e é 91% do mercado com dados de preço. Casa tem amostra
fraca (n=11) e não é recomendável concluir muito dela.

A base **não tem** a coluna de tipo de acomodação (imóvel inteiro / quarto
privado). Usei como proxy os marcadores operacionais. Controlando bairro,
tipologia, capacidade e reputação, o anúncio profissional **cobra +26,1% de ADR
(p<0,001) mas ocupa −8,4pp (p=0,061)**; o superhost faz o oposto (−1,2% de ADR,
+5,0pp de ocupação). São duas estratégias de precificação opostas convivendo no
mesmo mercado, e o efeito líquido sobre a receita é modesto.

**Perfil vencedor: apartamento de 2 quartos, ~85 m², operado profissionalmente.**

---

## 3. Melhor localização

### Correção de bairro aplicada antes do ranking

A base de venda tinha 3 bairros que o Airbnb não reconhece, deixando 1.399
imóveis (19% do mercado de venda) fora do cruzamento de ROI. O VivaReal **não
tem latitude/longitude**, então não é possível geolocalizá-los. A saída foi ler
o bairro citado no próprio título e URL do anúncio:

| Rótulo `suburb` | n | título/URL diz "meia praia" |
|---|---|---|
| Andorinha | 577 | **91,7%** |
| Castelo Branco | 370 | **94,3%** |

**Andorinha e Castelo Branco são sub-áreas de Meia Praia.** Foram reclassificados,
e o ponto cego de 19% deixou de existir — aqueles imóveis pertencem a um bairro
que já estava no ranking. Meia Praia passa de 2.653 para **3.710 imóveis à venda**.

### Ranking por receita

Critério: **RevPAN mediano do bairro, com n ≥ 20**.

| Bairro | n | ADR | pickup | **RevPAN** | ocup. fev | RevPAN via ocupação |
|---|---|---|---|---|---|---|
| **Meia Praia** | 367 | R$ 599 | 14,0% | **R$ 84** | 49,9% | R$ 299 |
| **Centro** | 145 | R$ 498 | 14,8% | **R$ 74** | 46,8% | R$ 233 |
| **Morretes** | 48 | R$ 464 | 12,0% | **R$ 56** | 52,5% | R$ 244 |

**Meia Praia é o melhor bairro em receita**, e também o maior mercado — 2.860
dos 4.441 anúncios contra 657 do Centro. O Centro não é o principal mercado de
Itapema, o que já contraria a intuição da tese interna.

O ranking **não é robusto entre Centro e Morretes**: por RevPAN de pickup o
Centro é 2º, por RevPAN de ocupação o Morretes é 2º. Meia Praia lidera nas duas.

### Controlando a tipologia

| Faixa | Centro | Meia Praia | Morretes |
|---|---|---|---|
| **2 quartos** | **R$ 91** (n=47) | R$ 66 (n=90) | R$ 46 (n=36) |
| 3 quartos | R$ 88 (n=27) | R$ 91 (n=230) | R$ 111 (n=9) ⚠ |
| 0-1 compacto | R$ 66 (n=69) | R$ 84 (n=17) ⚠ | R$ 157 (n=1) ⚠ |

Em **receita**, o Centro ganha claramente em 2 quartos. Mas receita não é
retorno: o Centro também é o bairro mais caro para comprar, e quando o preço
entra na conta (seção 5) a vantagem desaparece.

### O rótulo de bairro é confiável do lado da receita

Verifiquei com as coordenadas do Mesh: 75% dos anúncios rotulados "Centro"
estão a menos de **0,46 km** do centroide do Centro. Recalculando o RevPAN do
compacto por **raio geográfico** em vez de rótulo: **R$ 62 contra R$ 63**.
Idênticos. As conclusões de receita não dependem da nomenclatura.

---

## 4. O que explica as melhores receitas

Decompus em modelos separados, porque RevPAN = preço × demanda e os dois lados
respondem a coisas diferentes.

### O preço é bem explicável

Coeficientes padronizados sobre log(ADR), significativos a 5%:

| Variável | Efeito no ADR | p |
|---|---|---|
| Operação profissional | **+0,111** | 0,002 |
| Nº de hóspedes | +0,100 | <0,001 |
| Nº de quartos | +0,093 | 0,003 |
| Nº de banheiros | +0,091 | <0,001 |
| Nº de reviews (log) | **−0,068** | <0,001 |
| **Vista para o mar** | +0,059 | <0,001 |
| Star rating | +0,042 | 0,003 |
| Bairro Morretes | −0,042 | 0,004 |
| Nº de fotos | +0,038 | 0,040 |
| Beira-mar | +0,032 | 0,031 |

Capacidade e vista mar mandam no preço. O coeficiente **negativo de reviews** é
o achado contraintuitivo: anúncio com muito review cobra *menos*. Provável
leitura — quem acumula review é quem vende volume com preço competitivo.

### A demanda é muito menos explicável — mas o sinal não é zero

Validação com **RepeatedKFold (5 folds × 10 repetições = 50 estimativas)**, seis
famílias de modelo, mais controle positivo (ADR) e controle negativo (alvo
embaralhado):

| Alvo | melhor modelo | R² fora da amostra | % folds > 0 |
|---|---|---|---|
| **ADR — controle positivo** | RandomForest | **0,431** | 100% |
| Ocupação de fevereiro | Ridge | **0,078** | 100% |
| RevPAN (via ocupação) | Ridge | 0,060 | 80% |
| RevPAN (via pickup) | Ridge | 0,008 | 70% |
| pickup ajustado | Ridge | −0,002 | 60% |
| *alvo embaralhado (piso)* | Ridge | *−0,009 a −0,015* | *0%* |

**Correção de uma versão anterior deste relatório.** A primeira análise reportou
R² negativo (−0,25) para o pickup e concluiu "pior que chutar a média". Isso
estava errado: era **overfitting do Gradient Boosting**, não ausência de
fenômeno. Com modelos regularizados o valor sobe para ≈0.

O que sobrevive à correção:

1. **O pipeline funciona** — o controle positivo extrai R² de 0,431 do ADR, em
   100% dos folds, com queda holdout de ~0.
2. **A ocupação tem sinal real, pequeno e consistente:** R² de 0,078, positivo
   em **100% dos folds**, contra piso de −0,009 com alvo embaralhado. Pequeno,
   mas não é ruído.
3. **O pickup continua não explicável:** 0,008 é indistinguível do baseline da
   média (−0,012) e do piso do alvo embaralhado.

**A razão é de ~5:1** — as características do imóvel explicam 43% da variação do
preço e 8% da variação da ocupação. A leitura de negócio se mantém: **o imóvel
explica quanto ele cobra; o que explica quanto ele vende está majoritariamente
fora desta base** — gestão de preço, gestão de calendário, distribuição em
canais, qualidade real das fotos, bloqueios do proprietário. Para uma empresa
que vive de operação, isso é a favor. Mas a afirmação correta é "explica pouco",
não "não explica nada".

Na leitura direta por medianas, elevador (+R$ 25 de RevPAN), churrasqueira
(+23), piscina (+20) e superhost (+17) aparecem consistentes, mas **nenhum
sobrevive ao controle multivariado**. Não recomendo decidir compra por amenidade.

---

## 5. Recomendação de compra e retorno

### Premissas (são escolhas minhas, não vêm dos dados)

- **Fator anual de realização S**: cenários de **40% / 55% / 70%**. Significa
  "receita anual equivalente a S × 365 noites vendidas ao ADR de VERÃO". O fator
  absorve de uma vez a sazonalidade de ocupação **e** a de preço — o ADR da base
  é de janeiro, e no inverno cai. A **diferença entre células vem dos dados**; o
  **nível absoluto vem da premissa**.
- Aquisição (ITBI + escritura) 5% · Mobiliar R$ 1.500/m² · Comissão de canal 15%
  · Manutenção e utilities 10% · Condomínio e IPTU do próprio VivaReal.
- Não inclui IR, custo de capital, nem valorização do imóvel.

### Matriz de investimento (n ≥ 20 nos dois lados, base deduplicada)

| Bairro / tipologia | n Airbnb | n VivaReal | ADR | Preço | Invest. | Líquido/ano | **ROI** | Payback |
|---|---|---|---|---|---|---|---|---|
| **Morretes / 2q** | 36 | 731 | R$ 430 | R$ 795 mil | R$ 937 mil | R$ 53,1 mil | **5,67%** | 17,6 anos |
| **Centro / 2q** | 47 | 66 | R$ 604 | R$ 1,21 mi | R$ 1,40 mi | R$ 78,2 mil | **5,57%** | 18,0 anos |
| **Meia Praia / 2q** | 90 | 314 | R$ 450 | R$ 1,05 mi | R$ 1,24 mi | R$ 68,0 mil | **5,50%** | 18,2 anos |
| Centro / 3q | 27 | 366 | R$ 699 | R$ 2,10 mi | R$ 2,40 mi | R$ 97,5 mil | 4,06% | 24,6 |
| Meia Praia / 3q | 230 | 2.018 | R$ 656 | R$ 1,80 mi | R$ 2,08 mi | R$ 82,7 mil | 3,97% | 25,2 |
| Meia Praia / 4+ | 30 | 1.335 | R$ 899 | R$ 3,36 mi | R$ 3,81 mi | R$ 105,5 mil | 2,77% | 36,1 |

**As três primeiras linhas são um empate técnico.** 0,17 ponto percentual separa
Morretes de Meia Praia — muito abaixo da incerteza das estimativas. O que a
tabela decide com segurança é o **degrau entre 2 quartos (≈5,6%) e 3 quartos
(≈4,0%)**: 1,61 ponto percentual, contra 0,17 pp de diferença entre bairros —
**quase 10× maior**.

Na versão anterior deste relatório, Centro/2q aparecia em 1º com 5,97%. A
deduplicação física elevou o preço mediano do Centro/2q em 8,1%
(R$ 1,12 mi → R$ 1,21 mi) e derrubou o ROI para 5,57%. **A liderança do Centro
era artefato de duplicatas baratas na amostra.**

### Sensibilidade — a ordem não muda

| Célula | 40% | **55%** | 70% |
|---|---|---|---|
| Morretes / 2q | 3,98% | **5,67%** | 7,36% |
| Centro / 2q | 3,92% | **5,57%** | 7,22% |
| Meia Praia / 2q | 3,86% | **5,50%** | 7,15% |
| Centro / 3q | 2,85% | 4,06% | 5,26% |
| Meia Praia / 3q | 2,78% | 3,97% | 5,17% |
| Meia Praia / 4+ | 1,92% | 2,77% | 3,62% |

O empate entre os três de 2 quartos persiste em todos os cenários, e o degrau
para 3 quartos também. **A premissa de sazonalidade não muda nenhuma conclusão.**

### A decisão

> **Comprar apartamentos de 2 quartos, ~85 m².** A tipologia é a decisão
> defensável. **O bairro é indiferente entre Centro, Meia Praia e Morretes** —
> escolha por disponibilidade de estoque e preço negociado, não por RevPAN.

Como desempatar na prática, já que os dados não desempatam:

- **Morretes** exige o menor capital por unidade (R$ 937 mil) — mais unidades
  pelo mesmo orçamento. Contrapartida: pior RevPAN da cidade (R$ 56) e menor
  amostra de Airbnb (n=48).
- **Meia Praia** tem de longe o maior estoque (3.710 imóveis à venda) e a maior
  ocupação (56,7%) — melhor para escalar volume.
- **Centro** tem o maior RevPAN em 2 quartos (R$ 91) mas o **menor estoque:
  apenas 66 unidades** de 2 quartos à venda após a dedup.

---

## 5.5. O teste que o investimento precisa passar antes de qualquer bairro

Todos os números acima são de retorno **operacional**. Falta compará-los ao
custo de oportunidade do capital.

**Selic meta: 14,00% a.a.** (Copom, 05/08/2026) · **CDI: 13,90% a.a.**

| Célula | ROI | Operação/ano | Mesmo capital no CDI | % do CDI | Gap |
|---|---|---|---|---|---|
| Morretes / 2q | 5,67% | R$ 53,1 mil | R$ 130,2 mil | **41%** | −8,23 pp |
| Centro / 2q | 5,57% | R$ 78,2 mil | R$ 195,0 mil | **40%** | −8,33 pp |
| Meia Praia / 2q | 5,50% | R$ 68,0 mil | R$ 171,8 mil | **40%** | −8,40 pp |
| Meia Praia / 3q | 3,97% | R$ 82,7 mil | R$ 289,3 mil | 29% | −9,93 pp |
| Meia Praia / 4+ | 2,77% | R$ 105,5 mil | R$ 529,2 mil | **20%** | −11,13 pp |

O melhor imóvel da matriz entrega **41% do que o CDI entrega** — assumindo risco
de mercado, iliquidez de anos e trabalho operacional contínuo.

### Nenhuma alavanca fecha o gap

Para Centro/2q chegar aos 13,90% do CDI, mantendo os demais custos:

| Alavanca | Necessário | Viável? |
|---|---|---|
| Só ocupação | fator de realização 55% → **130,6%** | **impossível** (>100%) |
| Só ADR | R$ 604 → **R$ 1.433** (+137%) | p90 da tipologia na cidade é R$ 700 |
| Só preço de compra | R$ 1,21 mi → **R$ 413 mil** (−66%) | irrealista |
| **+20% ADR e +20% ocupação juntos** | ROI **8,24%** | ainda 5,7 pp abaixo |

### O prêmio de operação profissional fecha só 11% do gap

Medido nos próprios dados, com controle de bairro, tipologia, capacidade e
reputação: `is_professional` dá **+26,1% de ADR (p<0,001)** e **−8,4pp de
ocupação (p=0,061)**; `is_superhost` dá −1,2% de ADR e +5,0pp de ocupação.

Aplicando o prêmio combinado a Centro/2q: **5,57% → 6,52%**. Contra CDI de
13,90%, isso cobre **11% da distância**.

### A conclusão que decorre disso

> Para o retorno total empatar com o CDI, o imóvel precisaria **valorizar
> ~8,3% ao ano**. Esta base é uma fotografia de 11/01/2025 — **não permite
> avaliar valorização de forma alguma.**
>
> **A recomendação de comprar em Itapema não se sustenta como investimento em
> renda. Só se sustenta como aposta em valorização imobiliária** — uma aposta
> que estes dados não conseguem informar, nem a favor nem contra.

Isso não invalida a análise de perfil: se a Seazone decidir investir por razões
estratégicas (ganho de escala operacional, densidade em praças onde já opera,
tese própria de valorização), **2 quartos continua sendo a tipologia certa**.
Mas o yield sozinho não fecha a conta, e apresentá-lo como se fechasse seria
desonesto.

---

## 6. Posição sobre a tese dos compactos no Centro

> "Apartamentos compactos (studio/1 quarto) na região do Centro seriam a aposta
> mais eficiente para a Seazone."

**Os dados não sustentam a tese** — e a auditoria de qualidade de dados
**fortaleceu** a rejeição, não a enfraqueceu.

Separei as duas afirmações e li "eficiente" como **retorno por real investido** —
não receita absoluta, senão a tese seria refutada por construção.

### O que a tese acerta

O compacto **realmente vende mais rápido**: pickup de 15,6% contra 14,2% da
cidade, o maior de todas as faixas.

### Onde ela quebra

**1. A premissa central é falsa: o compacto não é barato.** É o metro quadrado
mais caro da cidade, e depois da deduplicação o prêmio ficou **maior**:

| Bairro | compacto | 2 quartos | prêmio (antes da dedup) | **prêmio (corrigido)** |
|---|---|---|---|---|
| Centro | R$ 21.964/m² (n=10) | R$ 13.681/m² (n=66) | +42,0% | **+60,5%** |
| Meia Praia | R$ 19.250/m² (n=43) | R$ 12.235/m² (n=314) | +65,7% | **+57,3%** |
| Morretes | R$ 13.083/m² (n=23) | R$ 11.843/m² (n=731) | +11,9% | **+10,5%** |

O prêmio subiu no Centro justamente porque os imóveis baratos que o mascaravam
não eram do Centro — ver a auditoria abaixo.

**2. Perde em receita e em retorno.** Dentro do Centro: compacto RevPAN R$ 66,
contra R$ 91 de 2 quartos e R$ 88 de 3 quartos. ROI de **4,82% contra 5,57%**.

**3. Não muda com a métrica.** Posição de "Centro / compacto" entre 12 células:
**10º por RevPAN de pickup, 12º por RevPAN de ocupação, 11º por ADR puro,
7º por ROI.**

**4. Não escala.** Na base corrigida existem **91 compactos à venda em toda
Itapema (1,6% do mercado)**, contra **1.382 de 2 quartos (23,6%)**. No Centro,
**10 unidades**.
Para uma empresa que gere 3.000 imóveis, uma tese que depende de um estoque de
dez unidades não é uma estratégia.

### A auditoria dos 16 anúncios — por que a amostra não era o que parecia

O elo frágil da análise era o preço de compra do compacto no Centro (n=16).
Auditei os 16 um a um:

| Problema | Achado |
|---|---|
| **Duplicata física** | Os 16 anúncios são **12 imóveis distintos**. R$ 890 mil/69 m² aparece **3 vezes**; R$ 660 mil/61 m² e R$ 980 mil/42 m², 2 vezes cada. URLs diferentes, mesmo imóvel, corretores distintos. |
| **Bairro errado** | **5 dos 16 dizem "MEIA PRAIA" no próprio título** — e são justamente os baratos (os dois de R$ 660 mil, a R$ 10.820/m²). |
| **Tipologia errada** | 1 anúncio: R$ 1,65 mi, 140 m², `bedrooms=1`, título "Apartamento **03 dormitórios** Pé na Areia". |
| **Amostra real** | Após limpar: **10 a 11 imóveis**, R$/m² sobe de 18.720 para **21.964**. |

**Dos 5 anúncios abaixo do ponto de virada, apenas 2 sobrevivem à auditoria**
como compactos do Centro legítimos (R$ 600 mil/28 m² e R$ 650 mil/40 m²) — e
ambos sem condomínio informado.

### "Garimpo" não é uma estratégia operacionalizável com estes dados

A versão anterior deste relatório sugeriu que a tese poderia se salvar como
estratégia de garimpo, comprando ~22% abaixo do preço pedido. **Retiro essa
formulação.** Duas razões:

**1. A estimativa é uma aposta de moeda.** Bootstrap do p25 com n=16:

- p25 pontual: R$ 685.500
- **IC95: R$ 650.000 a R$ 890.000** — largura de R$ 240 mil, 35% do valor pontual
- **P(p25 ≤ ponto de virada de R$ 694.904) = 59,4%**

Uma estratégia que depende de uma estimativa com 59% de chance de estar do lado
certo não é uma estratégia.

**2. Não há como medir a frequência de oportunidade.** O `VivaReal_Itapema.csv`
tem **uma única data de captura (11/01/2025)**. É uma fotografia, não uma série.
Não é possível estimar reposição de estoque, tempo de permanência do anúncio,
nem taxa de chegada de barganhas. Qualquer número sobre "quantos compactos
descontados aparecem por mês" seria inventado, e não vou inventá-lo.

O que dá para dizer honestamente: no corte transversal, 26% dos compactos de
Itapema (24 de 91) estavam abaixo do ponto de virada. Se isso se repõe, com que velocidade,
e se a Seazone conseguiria capturá-los — a base não responde.

### Veredito

**Rejeitada.** Mantenha 2 quartos, não studio. E note que a tese errava também
na direção do bairro: em compactos, o Centro (RevPAN R$ 66) perde para Meia
Praia (R$ 84). Se a aposta fosse mesmo em compactos, o Centro não seria o lugar.

---

## 7. Limites desta análise

Em ordem de gravidade.

1. **Não há receita realizada na base.** Toda demanda é inferida de
   disponibilidade entre capturas. "Indisponível" pode ser reserva **ou bloqueio
   do proprietário** — não são separáveis. A ocupação está superestimada em
   magnitude desconhecida.

2. **Sem inverno.** A janela é 06/01 a 20/04/2025. Itapema é cidade de praia com
   sazonalidade forte. Nenhum número anual aqui é observado — todos vêm dos
   cenários declarados.

3. **O ROI cruza duas populações que podem não ser equivalentes.** A receita vem
   de anúncios **maduros e ativos**: os 999 anúncios com dados de preço têm **27
   reviews em média, contra 3,8** dos 3.442 sem preço, e 98% têm rating contra
   56%. O preço de compra vem de imóveis **à venda hoje** — possivelmente mais
   novos, mais velhos, sem mobília ou em pior conservação. **Não há chave que
   ligue um anúncio de Airbnb ao seu equivalente no VivaReal**, então o
   cruzamento é feito por (bairro × nº de quartos), assumindo comparabilidade
   dentro da célula. É a premissa mais forte de toda a análise, e não é
   verificável com estes dados.

4. **A base de venda tinha 18,2% de duplicatas físicas.** O mesmo imóvel
   anunciado por corretores diferentes, com URLs distintas. Corrigido
   deduplicando por conteúdo (preço + área + quartos + banheiros + vagas) em vez
   de só por `link_url`. **Esse erro sozinho inverteu o 1º lugar do ranking de
   ROI.** Não há garantia de que a dedup por ficha física capture todos os casos
   — imóveis idênticos com preços ligeiramente diferentes passam.

5. **O bairro no VivaReal vem de texto livre, não de geolocalização.** A base
   não tem lat/long. A reclassificação de Andorinha e Castelo Branco e a
   auditoria de rótulo foram feitas lendo título e URL. A concordância geral
   entre rótulo e texto é de **79,5%** — ou seja, **cerca de 1 em 5 anúncios tem
   divergência de bairro** que não foi individualmente auditada. Só os 16 casos
   do compacto no Centro receberam auditoria manual.

6. **Apenas 22,6% dos anúncios têm preço**, e a seleção não é aleatória — o
   painel é de imóveis estabelecidos. Assumi isso deliberadamente: anúncio morto
   não é benchmark de investimento. Mas o retorno estimado é o de um operador que
   **já alcançou** maturidade, não o do primeiro ano.

7. **As duas métricas de demanda concordam só moderadamente** (Spearman 0,44
   entre pickup e ocupação). Onde a conclusão dependia da métrica, eu disse.

8. **O modelo de custos é premissa, não dado.** Mobília, comissão e manutenção
   foram arbitrados. 55% dos anúncios do VivaReal não informam condomínio (usei
   mediana do bairro).

9. **Amostras pequenas nas células decisivas.** Centro/2q tem n_VivaReal=66 após
   a dedup; Centro/3q tem n_Airbnb=27; Centro/compacto tem n_VivaReal=10. Os
   intervalos de confiança do RevPAN dentro do Centro **se sobrepõem** —
   compacto [54, 80] contra 2q [65, 117]. A diferença de *receita* entre compacto
   e 2 quartos **não é estatisticamente decisiva**. O que decide a rejeição da
   tese é o preço por m², o estoque e o retorno — não a receita.

10. **Não há dados de valorização imobiliária**, que a seção 5.5 mostra ser a
    variável decisiva de todo o caso de investimento. Esta é a maior lacuna da
    base em relação à decisão que ela pretende informar.

---

## 8. Apêndice — o que ficou fora do ranking principal

Nada foi descartado silenciosamente. Estas células têm n < 20 em pelo menos um
dos lados e por isso não entram na recomendação, mas os números estão aqui.

### Bairros com n < 20 (Airbnb)

| Bairro | n | ADR | pickup | RevPAN | ocup. fev |
|---|---|---|---|---|---|
| Sertão do Trombudo | 1 | R$ 1.000 | 12,1% | R$ 121 | 57,1% |
| Tabuleiro dos Oliveiras | 10 | R$ 509 | 16,3% | R$ 83 | 42,9% |
| Canto da Praia | 3 | R$ 518 | 13,5% | R$ 70 | 45,2% |
| Casa Branca | 3 | R$ 240 | 12,4% | R$ 30 | 31,0% |
| Ilhota | 1 | R$ 946 | 0,0% | R$ 0 | 0,0% |

18 anúncios em 5 bairros. Tabuleiro dos Oliveiras tem o maior pickup da base
(16,3%) e merece coleta dedicada — com n=10 não dá para recomendar.

### Células bairro × quartos com amostra insuficiente (base corrigida)

| Bairro / tipologia | n Airbnb | n VivaReal | ADR | Preço | ROI base |
|---|---|---|---|---|---|
| Morretes / compacto | **1** | 23 | R$ 480 | R$ 750 mil | 13,36% |
| Morretes / 3q | **9** | 133 | R$ 650 | R$ 849 mil | 12,76% |
| Meia Praia / compacto | **17** | 43 | R$ 490 | R$ 850 mil | 7,13% |
| Tabuleiro dos Oliveiras / 2q | **7** | 86 | R$ 400 | R$ 782 mil | 5,85% |
| **Centro / compacto** | 69 | **10** | R$ 440 | R$ 895 mil | **4,82%** |
| Sertão do Trombudo / 4+ | **1** | **1** | R$ 1.000 | R$ 3,68 mi | 3,83% |
| Canto da Praia / 3q | **1** | 54 | R$ 308 | R$ 1,68 mi | 3,80% |
| Centro / 4+ | **2** | 312 | R$ 725 | R$ 3,60 mi | 3,77% |
| Tabuleiro dos Oliveiras / 4+ | **1** | **1** | R$ 1.700 | R$ 4,09 mi | 3,73% |
| Casa Branca / 2q | **2** | **16** | R$ 228 | R$ 655 mil | 3,36% |
| Tabuleiro dos Oliveiras / 3q | **2** | **13** | R$ 585 | R$ 810 mil | 2,94% |
| Canto da Praia / 2q | **2** | **13** | R$ 550 | R$ 1,23 mi | 2,63% |
| Morretes / 4+ | **2** | 47 | R$ 795 | R$ 6,00 mi | 2,31% |
| Ilhota / 4+ | **1** | 18 | R$ 946 | R$ 2,85 mi | −0,42% |
| Casa Branca / 3q | **1** | **6** | R$ 500 | R$ 762 mil | −0,47% |

**Atenção:** as duas maiores taxas da base — Morretes/compacto com 13,36% e
Morretes/3q com 12,76% — vêm de **1 e 9 anúncios de Airbnb**. Não são
recomendações. Mas note: são as **únicas duas células da base inteira que
chegariam perto do CDI**. Se Morretes/3q se confirmar com amostra maior, é a
única coisa neste relatório que mudaria a resposta da seção 5.5. R$ 849 mil por
70 m² com ADR de R$ 650 é uma anomalia de preço que merece explicação — ou é
erro de dado, ou é a melhor oportunidade da cidade.

---

## 9. Conclusão

**O que os dados sustentam com firmeza:**

1. **2 quartos é a tipologia certa.** O degrau de ROI entre 2 quartos (≈5,6%) e
   3 quartos (≈4,0%) é de 1,61 pp — **quase 10× maior** que os 0,17 pp que
   separam os bairros, e persiste nos três cenários de sazonalidade.
2. **A tese dos compactos no Centro está errada.** O compacto é o m² mais caro
   da cidade (+60,5% sobre 2 quartos no Centro), rende menos, e tem estoque de
   10 unidades. A auditoria de dados fortaleceu essa rejeição.
3. **O imóvel explica o preço; a operação explica a venda.** Razão de ~5:1 entre
   o R² do ADR (0,431) e o da ocupação (0,078).

**O que os dados não sustentam:**

4. **Qual bairro.** Morretes 5,67%, Centro 5,57%, Meia Praia 5,50% é empate
   técnico. A liderança do Centro na versão anterior era artefato de duplicatas.
5. **Que comprar em Itapema seja um bom investimento de renda.** Com Selic a
   14,00%, o melhor imóvel entrega 41% do CDI, e nenhuma alavanca operacional
   plausível fecha o gap. Só valorização de ~8,3% a.a. fecharia — e a base não
   permite avaliá-la.

**O enquadramento honesto para a decisão:**

> A pergunta "studio ou 2 quartos" tem resposta clara: 2 quartos. Mas ela é
> secundária. A pergunta que decide é **se comprar imóvel em Itapema faz sentido
> a 14% de Selic** — e o que estes dados dizem é que só faz sentido como aposta
> em valorização, não em yield.
>
> Se a Seazone investir, que seja com essa tese declarada e com uma análise de
> valorização que esta base não contém. Se a decisão for por renda, o mesmo
> capital em CDI entrega 2,4× mais, sem operação e sem risco.

---

## 10. Reproduzir

```bash
pip install pandas numpy scipy scikit-learn statsmodels

# diagnóstico e plano
python analise/00_perfil_dados.py               # schema real dos 5 arquivos
python analise/01_diagnostico.py                # problemas de qualidade
python analise/02_estrutura_disponibilidade.py  # como Price_AV funciona
python analise/03_teste_pickup.py               # viabilidade do sinal de pickup

# pipeline principal
python analise/10_limpeza.py                    # -> saida/*_limpo.csv
python analise/20_metricas_airbnb.py            # -> saida/metricas_listing.csv
python analise/30_localizacao.py                # -> saida/rank_*.csv
python analise/40_drivers.py                    # -> saida/drivers_coeficientes.csv
python analise/50_vivareal_roi.py               # -> saida/matriz_investimento.csv
python analise/60_tese_centro.py                # os 5 testes da tese
python analise/61_sensibilidade.py              # a tese sobrevive ao elo frágil?

# auditorias que corrigiram o relatório
python analise/70_compacto_centro.py            # auditoria dos 16 anúncios
python analise/71_impacto_dedup.py              # -> saida/matriz_investimento_corrigida.csv
python analise/72_robustez_modelos.py           # Ridge/Lasso/RepeatedKFold
python analise/73_benchmark_retorno.py          # Selic/CDI e alavancas
```

O plano de análise, escrito e revisado **antes** de executar, está em
[`analise/PLANO.md`](analise/PLANO.md).

**Fontes do benchmark:** [Selic/Copom](https://investidor10.com.br/indices/selic/)
· [CDI](https://www.numerando.com.br/cdi-hoje) ·
[contexto Copom](https://apublica.org/2026/08/quase-tudo-o-que-voce-precisa-saber-sobre-o-copom-e-a-taxa-selic/)

---

## 11. Com mais uma semana

1. **Dados de valorização imobiliária.** A seção 5.5 mostra que é a variável que
   decide todo o caso de investimento, e é a que falta por completo. Séries
   históricas de preço por m² em Itapema mudariam a resposta final — não a
   análise de perfil.
2. **Mais capturas de preço.** Três snapshots em 14 dias é a maior limitação
   metodológica. Com capturas semanais por 3 meses, o pickup vira série e a
   ocupação para de ser inferência.
3. **Auditar os ~20% de divergência de rótulo de bairro no VivaReal.** Só 16
   casos foram checados manualmente. O erro que inverteu o 1º lugar do ranking
   veio exatamente daí.
4. **Investigar Morretes/3 quartos.** R$ 849 mil por 70 m² com ADR de R$ 650 é a
   única célula que chegaria perto do CDI. Com n=9 no Airbnb, não dá para
   recomendar — mas é a primeira coisa a checar.
5. **Separar bloqueio de reserva** cruzando com o calendário do anfitrião —
   removeria o maior viés da ocupação.
