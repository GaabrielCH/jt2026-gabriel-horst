# -*- coding: utf-8 -*-
"""
50_vivareal_roi.py — cruza receita (Airbnb) com preco de compra (VivaReal) e
monta a matriz de investimento por celula (bairro x faixa de quartos).

PREMISSAS DECLARADAS (nao vem dos dados — sao escolhas minhas, sujeitas a revisao):

  S = "fator anual de realizacao" em 3 cenarios: 40% / 55% / 70%.
      Interpretacao: receita anual equivale a S x 365 noites vendidas ao ADR de
      VERAO. O fator absorve DE UMA VEZ a sazonalidade de ocupacao E a de preco,
      porque o ADR da base e de janeiro (alta temporada) e no inverno cai. Usar
      ADR de verao com ocupacao anual, sem esse desconto, superestimaria a receita.
      A demanda RELATIVA entre celulas vem dos dados; o NIVEL absoluto vem de S.

  Custos de aquisicao: ITBI + escritura = 5% do preco.
  Mobiliar para short stay: R$ 1.500/m2.
  Comissao de canal (OTA): 15% da receita bruta.
  Manutencao + utilities + reposicao: 10% da receita bruta.
  Condominio e IPTU: medianas do proprio VivaReal na celula.
  Nao inclui: imposto de renda, vacancia por reforma, custo de capital.

Saida: matriz_investimento.csv (com n_airbnb e n_vivareal por celula)
"""
import pandas as pd, numpy as np, os
pd.set_option("display.width", 240)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "analise", "saida")

cel = pd.read_csv(os.path.join(OUT, "rank_celulas.csv"))
vr = pd.read_csv(os.path.join(OUT, "vr_limpo.csv"), low_memory=False)
met = pd.read_csv(os.path.join(OUT, "metricas_listing.csv"), low_memory=False)

CENARIOS = {"conservador_40": 0.40, "base_55": 0.55, "otimista_70": 0.70}
PCT_AQUISICAO, MOBILIA_M2 = 0.05, 1500
PCT_CANAL, PCT_MANUT = 0.15, 0.10
N_MIN_AIRBNB, N_MIN_VR = 20, 20

print("=" * 100)
print("MATRIZ DE INVESTIMENTO — receita Airbnb x preco de compra VivaReal")
print("=" * 100)

# ------------------------------------------------- 1. preco de compra por celula
pv = vr.groupby(["bairro", "faixa_quartos"]).agg(
    n_vivareal=("sale_price", "size"),
    preco_mediano=("sale_price", "median"),
    preco_p25=("sale_price", lambda s: s.quantile(.25)),
    area_mediana=("usable_area", "median"),
    preco_m2=("preco_m2", "median"),
    condominio=("monthly_condo_fee", "median"),
    iptu_anual=("yearly_iptu", "median")).reset_index()

print(f"\n[VIVAREAL] {len(vr)} apartamentos a venda -> {len(pv)} celulas")
print(pv[pv.n_vivareal >= N_MIN_VR]
      .sort_values(["bairro", "faixa_quartos"])
      .assign(preco_mediano=lambda d: (d.preco_mediano/1000).round(0),
              preco_p25=lambda d: (d.preco_p25/1000).round(0),
              preco_m2=lambda d: d.preco_m2.round(0),
              condominio=lambda d: d.condominio.round(0))
      .rename(columns={"preco_mediano": "preco_med_kR$", "preco_p25": "preco_p25_kR$"})
      .to_string(index=False))

# condominio/IPTU faltantes: usa a mediana do bairro, depois a global
for col, glob in [("condominio", vr.monthly_condo_fee.median()),
                  ("iptu_anual", vr.yearly_iptu.median())]:
    porb = vr.groupby("bairro")[{"condominio": "monthly_condo_fee",
                                 "iptu_anual": "yearly_iptu"}[col]].median()
    pv[col] = pv[col].fillna(pv.bairro.map(porb)).fillna(glob)

# ------------------------------------------------------------- 2. juntar receita
m = cel.merge(pv, on=["bairro", "faixa_quartos"], how="inner")
print(f"\n[JOIN] {len(m)} celulas com receita E preco de compra")

sem_vr = set(zip(cel.bairro, cel.faixa_quartos)) - set(zip(pv.bairro, pv.faixa_quartos))
print(f"  celulas com Airbnb mas sem VivaReal: {len(sem_vr)}")
so_vr = sorted(set(vr.bairro.dropna()) - set(cel.bairro.dropna()))
print(f"  bairros so no VivaReal (sem receita): {so_vr} = "
      f"{int(vr.bairro.isin(so_vr).sum())} anuncios de venda")

# demanda relativa: quanto a celula ocupa acima/abaixo do mercado
ocup_mercado = met.ocup_fev.mean()
m["indice_demanda"] = m.ocup_fev / ocup_mercado
print(f"\n[DEMANDA] ocupacao media de fevereiro no mercado: {ocup_mercado:.1%}")
print("  indice_demanda = ocupacao da celula / ocupacao do mercado "
      "(o nivel absoluto vem do cenario, a diferenca entre celulas vem dos dados)")

# ------------------------------------------------------------------ 3. cenarios
m["investimento"] = m.preco_mediano * (1 + PCT_AQUISICAO) + m.area_mediana * MOBILIA_M2
m["custo_fixo_ano"] = m.condominio * 12 + m.iptu_anual

for nome, S in CENARIOS.items():
    noites = 365 * S * m.indice_demanda
    bruta = m.adr * noites
    liq = bruta * (1 - PCT_CANAL - PCT_MANUT) - m.custo_fixo_ano
    m[f"receita_bruta_{nome}"] = bruta
    m[f"receita_liq_{nome}"] = liq
    m[f"roi_{nome}"] = liq / m.investimento
    m[f"payback_{nome}"] = m.investimento / liq

m["amostra_ok"] = (m.n_airbnb >= N_MIN_AIRBNB) & (m.n_vivareal >= N_MIN_VR)

# ---------------------------------------------------------------- 4. resultados
print("\n" + "=" * 100)
print(f"RANKING POR RETORNO — celulas com n_airbnb >= {N_MIN_AIRBNB} "
      f"e n_vivareal >= {N_MIN_VR}")
print("=" * 100)
show = ["bairro", "faixa_quartos", "n_airbnb", "n_vivareal", "adr", "ocup_fev",
        "revpan_pickup", "preco_mediano", "area_mediana", "investimento",
        "receita_liq_base_55", "roi_base_55", "payback_base_55"]
sel = m[m.amostra_ok].sort_values("roi_base_55", ascending=False)
print(sel[show].assign(
    adr=sel.adr.round(0), ocup_fev=(100*sel.ocup_fev).round(1),
    revpan_pickup=sel.revpan_pickup.round(0),
    preco_mediano=(sel.preco_mediano/1000).round(0),
    investimento=(sel.investimento/1000).round(0),
    receita_liq_base_55=(sel.receita_liq_base_55/1000).round(1),
    roi_base_55=(100*sel.roi_base_55).round(2),
    payback_base_55=sel.payback_base_55.round(1)
).rename(columns={"ocup_fev": "ocup_%", "preco_mediano": "preco_kR$",
                  "investimento": "invest_kR$", "receita_liq_base_55": "liq_ano_kR$",
                  "roi_base_55": "ROI_%", "payback_base_55": "payback_anos"}
).to_string(index=False))

print("\n### SENSIBILIDADE AO CENARIO (ROI liquido % ao ano)")
sens = sel[["bairro", "faixa_quartos", "n_airbnb"]].copy()
for nome in CENARIOS:
    sens[nome] = (100 * sel[f"roi_{nome}"]).round(2)
print(sens.to_string(index=False))
print("  -> se a ordem entre celulas nao muda com o cenario, a escolha nao depende "
      "da premissa de sazonalidade.")

print(f"\n### APENDICE — celulas com amostra insuficiente "
      f"(n_airbnb < {N_MIN_AIRBNB} ou n_vivareal < {N_MIN_VR})")
ap = m[~m.amostra_ok].sort_values("roi_base_55", ascending=False)
print(ap[["bairro", "faixa_quartos", "n_airbnb", "n_vivareal", "adr",
          "preco_mediano", "roi_base_55"]].assign(
    adr=ap.adr.round(0), preco_mediano=(ap.preco_mediano/1000).round(0),
    roi_base_55=(100*ap.roi_base_55).round(2)).to_string(index=False))

m.to_csv(os.path.join(OUT, "matriz_investimento.csv"), index=False)
print(f"\nGRAVADO: analise/saida/matriz_investimento.csv "
      f"({len(m)} celulas x {m.shape[1]} colunas, com n_airbnb e n_vivareal)")
