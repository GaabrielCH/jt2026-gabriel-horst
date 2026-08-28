# 🎥 VÍDEO (3 min): [COLE AQUI O LINK DO GOOGLE DRIVE — TROCAR ANTES DE ENVIAR]

> ⚠️ **Checklist antes de submeter:** trocar o placeholder acima pelo link real,
> e conferir numa aba anônima que o vídeo abre com compartilhamento
> "qualquer pessoa com o link".

---

# Onde a Seazone deveria investir em Itapema/SC

Hackathon Jovens Talentos AI Builder 2026 — desafio individual.
Análise de **4.441 anúncios de Airbnb** e **5.865 apartamentos à venda** para
recomendar perfil de imóvel, localização e retorno de investimento.

## 👉 A resposta está em [`relatorio.md`](relatorio.md)

> 💡 Prefere navegar visualmente? A análise também está publicada como página única:
> **<https://gaabrielch.github.io/jt2026-gabriel-horst/>**
> — tabelas, navegação por seção e os dois pontos que decidem a recomendação em
> destaque. O fonte está em [`docs/index.html`](docs/index.html) e abre direto no
> navegador, sem servidor. O Markdown continua sendo a fonte da recomendação.

| Pergunta do desafio | Onde está |
|---|---|
| Resumo executivo | [Resposta curta](relatorio.md#resposta-curta) |
| **1.** Melhor perfil de imóvel (tipologia, quartos, tipo de anúncio) | [Seção 2](relatorio.md#2-melhor-perfil-de-imóvel) |
| **2.** Melhor localização em termos de receita | [Seção 3](relatorio.md#3-melhor-localização) |
| **3.** Quais características explicam as melhores receitas | [Seção 4](relatorio.md#4-o-que-explica-as-melhores-receitas) |
| **4.** O que comprar hoje + estimativa de retorno | [Seção 5](relatorio.md#5-recomendação-de-compra-e-retorno) |
| Retorno comparado à taxa livre de risco | [Seção 5.5](relatorio.md#55-o-teste-que-o-investimento-precisa-passar-antes-de-qualquer-bairro) |
| **5.** ⭐ **Posição sobre a tese dos compactos no Centro** | **[Seção 6](relatorio.md#6-posição-sobre-a-tese-dos-compactos-no-centro)** |
| Limites e vieses assumidos | [Seção 7](relatorio.md#7-limites-desta-análise) |
| O que ficou fora do ranking (n < 20) | [Seção 8](relatorio.md#8-apêndice--o-que-ficou-fora-do-ranking-principal) |

---

## A recomendação em três frases

1. **Apartamento de 2 quartos, ~85 m².** A tipologia é a conclusão firme: o
   degrau de retorno entre 2 quartos (≈5,6%) e 3 quartos (≈4,0%) é 4× maior que
   qualquer diferença entre bairros.
2. **O bairro não é decidível com estes dados.** Morretes 5,67%, Centro 5,57%,
   Meia Praia 5,50% — empate técnico depois de corrigir 18,2% de duplicatas
   físicas na base de venda.
3. **A tese interna dos compactos no Centro não se sustenta.** O compacto é o
   m² mais caro da cidade (+60,5% sobre 2 quartos no Centro), rende menos e tem
   estoque de 10 unidades. Detalhamento na [seção 6](relatorio.md#6-posição-sobre-a-tese-dos-compactos-no-centro).

E a ressalva que atravessa tudo: com **Selic a 14,00%**, o melhor imóvel da
matriz entrega **41% do que o mesmo capital renderia no CDI**. Comprar em
Itapema só se justifica como aposta em valorização, não em renda —
[seção 5.5](relatorio.md#55-o-teste-que-o-investimento-precisa-passar-antes-de-qualquer-bairro).

---

## Estrutura do repositório

```
.
├── README.md                  <- você está aqui
├── relatorio.md               <- A RESPOSTA: análise, recomendação e posição sobre a tese
├── docs/index.html            <- versão navegável da análise (GitHub Pages)
├── CLAUDE.md                  <- instruções que configurei para a IA neste projeto
├── data/                      <- os 5 CSVs originais do desafio (não modificados)
├── analise/                   <- todo o código
│   ├── PLANO.md               <- plano escrito e revisado ANTES de rodar a análise
│   ├── 00..03_*.py            <- diagnóstico dos dados
│   ├── 10..61_*.py            <- pipeline principal
│   ├── 70..73_*.py            <- auditorias que corrigiram o relatório
│   └── saida/                 <- tabelas de resultado (CSV)
└── ai-log/                    <- conversa completa com a IA, em texto
    ├── README.md              <- como ler os logs
    ├── decisoes-e-iteracoes.md<- os pontos de virada da sessão, comentados
    ├── transcript-completo.md <- a sessão inteira, legível (inclui o raciocínio)
    ├── sessao-raw.jsonl       <- o transcript bruto, sem cortes
    └── exportar_transcript.py <- script que gerou os dois acima
```

---

## Como rodar

**Requisitos:** Python 3.10+

```bash
pip install pandas numpy scipy scikit-learn statsmodels
```

Os scripts são numerados e devem rodar **nessa ordem** — cada bloco depende do
anterior. Todos imprimem os resultados no terminal e gravam CSVs em
`analise/saida/`.

### 1. Diagnóstico (entender os dados antes de analisar)

```bash
python analise/00_perfil_dados.py               # schema real dos 5 arquivos
python analise/01_diagnostico.py                # problemas de qualidade de dado
python analise/02_estrutura_disponibilidade.py  # como Price_AV realmente funciona
python analise/03_teste_pickup.py               # viabilidade do sinal de pickup
```

### 2. Pipeline principal

```bash
python analise/10_limpeza.py            # -> det_limpo, price_limpo, vr_limpo
python analise/20_metricas_airbnb.py    # -> metricas_listing.csv (ADR, pickup, RevPAN)
python analise/30_localizacao.py        # -> rank_bairros, rank_celulas, rank_quartos
python analise/40_drivers.py            # -> drivers_coeficientes.csv
python analise/50_vivareal_roi.py       # -> matriz_investimento.csv
python analise/60_tese_centro.py        # os 5 testes da tese dos compactos
python analise/61_sensibilidade.py      # a tese sobrevive ao elo frágil?
```

### 3. Auditorias (foram elas que corrigiram números do relatório)

```bash
python analise/70_compacto_centro.py    # auditoria dos 16 anúncios, um a um
python analise/71_impacto_dedup.py      # -> matriz_investimento_corrigida.csv
python analise/72_robustez_modelos.py   # Ridge/Lasso/RepeatedKFold
python analise/73_benchmark_retorno.py  # Selic/CDI e alavancas de retorno
```

**Rodar tudo de uma vez** (bash):

```bash
for s in 00_perfil_dados 01_diagnostico 02_estrutura_disponibilidade 03_teste_pickup \
         10_limpeza 20_metricas_airbnb 30_localizacao 40_drivers 50_vivareal_roi \
         60_tese_centro 61_sensibilidade 70_compacto_centro 71_impacto_dedup \
         72_robustez_modelos 73_benchmark_retorno; do
  echo "== $s"; python "analise/$s.py" > /dev/null || echo "FALHOU: $s"
done
```

Tempo total: ~3 minutos (o gargalo é `72_robustez_modelos.py`, que roda 50
validações cruzadas por modelo).

### Sobre os CSVs de saída

As tabelas de **resultado** estão versionadas em `analise/saida/` e podem ser
abertas direto, sem rodar nada:

| Arquivo | O que tem |
|---|---|
| `matriz_investimento_corrigida.csv` | **a tabela que sustenta a recomendação** — ROI por bairro × tipologia, com `n_airbnb` e `n_vivareal` |
| `matriz_investimento.csv` | a versão anterior, antes da deduplicação (para comparar) |
| `rank_bairros.csv` / `rank_celulas.csv` / `rank_quartos.csv` | rankings de RevPAN |
| `teste_tese_celulas.csv` | os testes da tese dos compactos, com IC bootstrap |
| `drivers_coeficientes.csv` | coeficientes dos modelos de receita |
| `robustez_modelos.csv` | R² fora da amostra por modelo e por alvo |
| `log_limpeza.txt` | registro do que foi removido/alterado na limpeza |

Seis arquivos intermediários grandes (~21 MB — `det_limpo.csv`,
`price_limpo.csv`, `vr_limpo.csv`, `metricas_listing.csv`, `noites_pickup.csv`,
`noites_fev.csv`) **não** estão versionados de propósito: são 100% regeneráveis
pelo pipeline acima. Ver [`.gitignore`](.gitignore).

---

## Método, em um parágrafo

A base **não tem reservas realizadas** e cobre só 06/01 a 20/04/2025 (sem
inverno). `Price_AV` tem apenas 3 capturas, e a ausência de linha é informação:
data faltante = noite indisponível. Como a indisponibilidade cresce quanto mais
perto a data (80% em janeiro contra 22% em abril — curva de booking, não
ocupação), usar "% indisponível" como ocupação induziria erro. A saída foi
comparar as capturas de 06/01 e 20/01: noite disponível na primeira e ausente na
segunda **foi vendida nesses 14 dias**. Isso dá o `pickup`, uma medida de
velocidade de venda, padronizada pelo mix de datas de cada anúncio. `RevPAN =
ADR × pickup` ranqueia; a ocupação de fevereiro estima receita. A definição
completa e as ressalvas estão na [seção 1 do relatório](relatorio.md#1-método--e-o-que-revpan-significa-aqui).

---

## Sobre o uso de IA

Todo o trabalho foi feito com **Claude Code (Opus 5)**, e a sessão inteira está
em [`ai-log/`](ai-log/) — incluindo os blocos de raciocínio interno do modelo,
onde aparecem as hipóteses descartadas e as auto-correções.

Dois momentos que valem a leitura, porque mudaram conclusões:

- **A auditoria que inverteu o ranking.** Uma revisão pediu para eu olhar os 16
  anúncios de compactos um a um. Descobri que eram 12 imóveis (duplicatas por
  corretor), que 5 diziam "Meia Praia" no próprio título, e que a base inteira
  tinha 18,2% de repetição. Corrigido, o 1º lugar do ranking de ROI mudou.
- **Uma auto-correção estatística.** Eu havia reportado R² negativo como prova de
  que "a demanda não é explicável". Ao testar com Ridge/Lasso e validação
  repetida, ficou claro que o número era *overfitting da árvore*, não ausência de
  fenômeno. O relatório foi corrigido e registra o erro explicitamente.

Os detalhes comentados estão em
[`ai-log/decisoes-e-iteracoes.md`](ai-log/decisoes-e-iteracoes.md).

---

## Dados de origem (`data/`)

Os 5 CSVs do desafio, **não modificados**.

| Arquivo | O que tem | Como conecta |
|---|---|---|
| `Details_Itapema.csv` | Anúncios de Airbnb: título, reviews, rating, quartos, tipo | Base dos listings |
| `Hosts_ids_Itapema.csv` | Anfitrião: reviews, anos, superhost | Liga por `owner_id` |
| `Mesh_Ids_Data_Itapema.csv` | Latitude/longitude + bairro | Liga por listing |
| `Price_AV_Itapema.csv` | Preço por anúncio, data de estadia e de captura | Liga por listing |
| `VivaReal_Itapema.csv` | Anúncios de venda: preço, condomínio, área | Mercado de compra |

Enunciado original do desafio: [`index.html`](index.html) ·
[versão online](https://seazone-tech.github.io/jovens-talentos-2026-hackathon-data/)
