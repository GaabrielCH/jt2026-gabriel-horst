# Plano de análise — Itapema/SC (para revisão antes de executar)

Status: **proposto, não executado.** Baseado no perfilamento real
(`00_perfil_dados.py`, `01_diagnostico.py`, `02_estrutura_disponibilidade.py`,
`03_teste_pickup.py`).

---

## 1. Schema real

### Details_Itapema.csv — 4.441 linhas × 35 colunas (1 linha = 1 anúncio)
Chave `airbnb_listing_id` única, sem duplicatas.
Úteis: `number_of_bedrooms`, `number_of_bathrooms`, `number_of_beds`,
`number_of_guests`, `listing_type`, `amenities` (JSON), `cleaning_fee`,
`number_of_reviews`, `star_rating` + 6 sub-ratings, `picture_count`,
`owner_id`, `is_guest_favorite`, `can_instant_book`, `is_professional`.
**Inúteis:** `latitude`/`longitude` (100% = 0,0), `min_nights` (100% = 0).

### Hosts_ids_Itapema.csv — 4.440 linhas × 11 colunas
**Não é 1 linha por host:** 3.057 `owner_id` distintos, ou seja 1.383 duplicados
com valores divergentes (snapshots diferentes). `response_rate_shown` e
`response_time_shown` são **100% nulas**.

### Mesh_Ids_Data_Itapema.csv — 4.441 linhas × 8 colunas
1 linha por listing, cobre 100% do Details. Lat/long válidos.
`suburb`: 16 bairros — Meia Praia 2.860, Centro 657, Morretes 441,
Tabuleiro dos Oliveiras 129, Casa Branca 88, demais abaixo de 65.
5 anúncios com bairro `"none"`.

### Price_AV_Itapema.csv — 118.839 linhas × 4 colunas
**O arquivo mais restritivo da base.** Painel de preço-por-noite:

- Apenas **3 capturas**: 06/01, 07/01 e 20/01/2025. Cada uma projeta 91 dias à frente.
- Datas de estadia: **06/01 a 20/04/2025** (105 dias). Só verão + outono.
- Cobre **1.005 listings (22,6%)**, não os 4.441.
- Chave real = (listing, date, aquisition_date). Sem duplicatas nessa chave.
- **A ausência de linha é informação:** dentro da janela de uma captura,
  data faltante = noite indisponível (reservada ou bloqueada).

### VivaReal_Itapema.csv — 8.329 linhas × 22 colunas
`sale_price` (mediana R$ 1,75 mi), `usable_area`, `bedrooms`, `bathrooms`,
`parking_spaces`, `monthly_condo_fee`, `yearly_iptu`, `amenities`, `suburb`.
`rental_price`/`rental_period` **100% nulas** (2 registros) — sem yield de
aluguel longo. 36 `listing_id`/`link_url` duplicados.

---

## 2. Problemas de qualidade — e o que fazer

| # | Problema | Impacto | Tratamento proposto |
|---|---|---|---|
| 1 | Price_AV cobre só 22,6% dos anúncios, e os cobertos têm **27 reviews médios vs 3,8** dos não cobertos (98% vs 56% com rating) | Viés de seleção forte: o painel é de imóveis **maduros e ativos** | Não corrigir — **assumir explicitamente**. É o universo certo para decisão de investimento (anúncio morto não é benchmark). Reportar como limite. |
| 2 | Janela só 06/01–20/04 | Itapema é praia: **sem inverno na base** | Proibido anualizar por média simples. Ver §3.4. |
| 3 | Indisponibilidade cresce quanto mais perto a data: 80% jan, 51% fev, 28% mar, 22% abr | "% indisponível" **não é ocupação** — é curva de booking | Usar **pickup entre capturas** como sinal primário. Ver §3.2. |
| 4 | Indisponível = reservado **ou** bloqueado pelo dono | Superestima ocupação | Não separável. Chamar de "noites vendidas ou bloqueadas" e ser honesto. |
| 5 | `star_rating`=0 e `number_of_reviews`=0 em 1.540 anúncios | 0 é placeholder de nulo, não nota zero | Converter 0 para NaN em rating; manter reviews=0 como real. |
| 6 | Hosts com 1.383 `owner_id` duplicados divergentes | Join infla linhas | Deduplicar pelo `host_snapshot_date` mais recente. |
| 7 | `latitude`/`longitude` zeradas no Details; `min_nights` constante | Colunas mortas | Descartar; geo vem do Mesh. |
| 8 | Bairros divergem entre Mesh e VivaReal | Quebra o cruzamento receita × preço de compra | Normalizar (acento/caixa/grafia). **Andorinha (782) e Castelo Branco (510) só existem no VivaReal** — resolver via lat/long ou agrupar. |
| 9 | VivaReal: `usable_area` com 0 (11 casos) e outlier de 188.000 m²; `sale_price` até R$ 44 mi; `condo_fee`=0 em 2.364 e 29,9% nulo | Distorce R$/m² e ROI | Filtrar `business_types="Venda"`, `listing_type="apartamento"`, área 20–400 m², winsorizar p1–p99, tratar condomínio=0 como nulo. |
| 10 | 36 duplicatas de `link_url` no VivaReal | Peso duplo | Deduplicar. |
| 11 | `wc -l` dá 4.530 no Details vs 4.441 linhas reais | Campos com quebra de linha embutida | Ler sempre com parser CSV, nunca contar linhas. |

**Ausente na base:** não existe coluna de *room type* (imóvel inteiro / quarto
privado). "Tipo de anúncio" será proxiado por `listing_type`
(apartamento / casa / outros / hotel) mais `is_professional`,
`can_instant_book` e `is_guest_favorite`. Assunção a declarar no relatório.

---

## 3. Métricas propostas

### 3.1 ADR (diária média ofertada)
Mediana de `price` por listing, sobre a captura de 20/01 (a mais ampla).
Mediana, não média — a cauda vai a R$ 29.000.

### 3.2 Demanda: **pickup** (sinal primário) — já testado, funciona
Comparar captura 06/01 contra 20/01 nas 77 noites de janela comum (20/01–06/04):
noite disponível em 06/01 e ausente em 20/01 = **vendida nesses 14 dias**.

Resultado do teste de viabilidade: 630 listings comparáveis, 4.352 noites-listing
reservadas = **14,2% de pickup em 14 dias** (43,9% jan / 20,2% fev / 7,7% mar /
3,4% abr). 578 listings com 20 ou mais noites disponíveis — amostra suficiente.

Vantagem: mede **demanda incremental real**, imune à curva de booking, porque
compara o mesmo par (listing, data) em dois momentos.

### 3.3 Receita — a métrica de ranqueamento
`RevPAN` (receita por noite disponível) = ADR × taxa de pickup.
É o análogo de RevPAR hoteleiro e a única forma justa de comparar imóveis com
preço alto e ocupação baixa contra preço baixo e ocupação alta.
Secundária: `receita_mensal_estimada = RevPAN × 30`.
**Métrica de decisão de investimento: RevPAN, não ADR.**

### 3.4 Retorno sobre compra
`ROI_bruto = receita_estimada / preço_de_compra`, com preço vindo do VivaReal por
(bairro × nº de quartos) — mediana de `sale_price`.
Descontar `monthly_condo_fee`, `yearly_iptu` e taxa de gestão.

**Não vou anualizar por extrapolação linear.** Reporto o retorno do período
observado (jan–abr) e faço um cenário anual com fator de sazonalidade
**declarado como premissa externa**, com análise de sensibilidade
(ex.: 40% / 55% / 70% de ocupação anual), já que a base não tem inverno.

### 3.5 Localização
Critério: **RevPAN mediano do bairro**, com mínimo de listings para entrar no
ranking (proposta: n ≥ 20 com pickup válido). Bairros abaixo disso viram
"amostra insuficiente" — não somem do relatório, mas não são recomendados.
Corte por RevPAN e não por ADR justamente para não premiar bairro caro e vazio.

### 3.6 O que explica a receita
Modelo interpretável (regressão + árvore) de RevPAN sobre: quartos, banheiros,
hóspedes, bairro, amenities parseadas (piscina, vista mar, ar-condicionado,
churrasqueira, garagem), nº de fotos, rating, reviews, superhost,
`is_professional`, `is_guest_favorite`. Objetivo é **peso relativo e sinal**,
não previsão. Reportar R² honesto e confundidores.

---

## 4. Cruzamento dos 5 arquivos

```
Details (4.441, base)
  ├─ Mesh        por airbnb_listing_id  -> suburb, lat, long          [1:1, 100%]
  ├─ Hosts       por owner_id (dedup.)  -> superhost, anos, rating    [N:1]
  └─ Price_AV    por airbnb_listing_id  -> ADR, pickup, RevPAN        [1:N, só 22,6%]
        |
        v  agrega para o nível listing
  painel_airbnb  -> agrega por (bairro x faixa de quartos)
        |
        |  join por bairro normalizado + nº de quartos
        v
  VivaReal (filtrado) -> preço mediano de compra, R$/m², condomínio
        |
        v
  ROI por (bairro x tipologia)
```

Duas tabelas finais: `listings_enriquecido.csv` (grão = anúncio) e
`matriz_investimento.csv` (grão = bairro × quartos, com RevPAN, preço, ROI, n).

---

## 5. Como testar a tese "studio/1 quarto no Centro"

A tese tem **duas afirmações separadas** que serão testadas separadamente —
tamanho e localização — mais o teste conjunto. "Eficiente" será lido como
**retorno por real investido**, não receita absoluta (1 quarto quase certamente
perde em receita absoluta, e isso sozinho não refutaria a tese).

**Teste 1 — Compacto vs maior, controlando bairro.**
RevPAN de 0–1 quarto vs 2 vs 3+ **dentro de cada bairro**. Comparar Centro com
Centro. Sem controle, o efeito bairro contamina o efeito tamanho.

**Teste 2 — Centro vs demais, controlando tamanho.**
RevPAN do Centro vs Meia Praia vs Morretes, comparando faixas iguais de quartos.
Atenção: **Meia Praia tem 2.860 anúncios contra 657 do Centro** — o Centro não é
o mercado principal de Itapema em volume, o que já é um contraponto à tese.

**Teste 3 — o teste que decide: eficiência de capital.**
`RevPAN mensal ÷ preço de compra mediano` por (bairro × quartos). Só aqui a
palavra "eficiente" é de fato respondida. Um compacto pode render menos em
absoluto e ainda ganhar, se custar proporcionalmente muito menos.

**Teste 4 — significância e amostra.**
Bootstrap e intervalo de confiança nas diferenças. Verificar o n de studios no
Centro *com dados de preço*: pela distribuição (1 quarto = 14,4% dos listings
com preço; Centro = 14,8% do total), a célula "Centro × 0-1 quarto com pickup
válido" pode ter **n muito baixo**. Se for o caso, a resposta honesta é
*"os dados não permitem sustentar nem refutar com confiança"* — e isso será
dito, não maquiado.

**Teste 5 — robustez.** Repetir com ADR puro e com ocupação bruta. Se a
conclusão mudar conforme a métrica, isso vai no relatório.

Resultado possível e aceito: a tese pode se confirmar em eficiência de capital e
falhar em receita — a recomendação separará os dois casos.

---

## 6. Ordem de execução proposta

1. `10_limpeza.py` — aplica §2, gera dados tratados
2. `20_metricas_airbnb.py` — ADR, pickup, RevPAN por listing
3. `30_localizacao.py` — ranking de bairros
4. `40_drivers.py` — o que explica a receita
5. `50_vivareal_roi.py` — preço de compra, matriz de ROI
6. `60_tese_centro.py` — os 5 testes da §5
7. `relatorio.md` — conclusões e recomendação final

---

## 7. Decisões que quero confirmar antes de executar

- **RevPAN** como métrica principal de ranqueamento (em vez de ADR ou receita absoluta)?
- **Pickup de 14 dias** como proxy de demanda, aceitando cair de 999 para 630 listings?
- Sazonalidade anual em **cenários declarados** (40/55/70%) em vez de número único?
- "Melhor localização" = RevPAN mediano com n ≥ 20?
