# -*- coding: utf-8 -*-
"""
20_metricas_airbnb.py — ADR, demanda e RevPAN por anuncio.

DUAS metricas de demanda, com papeis DIFERENTES e propositais:

  (1) pickup_ajustado  -> METRICA DE RANQUEAMENTO
      Fracao das noites que estavam disponiveis em 06/01 e sumiram em 20/01,
      ou seja, vendidas (ou bloqueadas) em 14 dias. E VELOCIDADE DE VENDA,
      nao ocupacao. Ajustada por composicao de datas (ver abaixo).

  (2) ocup_fev         -> METRICA DE RECEITA/ROI
      Fracao dos 28 dias de fevereiro indisponiveis na captura de 20/01.
      Mesmo horizonte de antecedencia para todos os anuncios, logo comparavel.
      SUBESTIMA a ocupacao final de fevereiro (ainda faltavam reservas a entrar).

AJUSTE DE COMPOSICAO DE DATAS (por que o pickup cru engana):
  o pickup de mercado cai de 43,9% (jan) para 3,4% (abr). Um anuncio cuja
  disponibilidade se concentra em fevereiro exibiria pickup alto sem ser mais
  demandado — seria so o mix de datas. Corrigimos por padronizacao indireta:
      esperado_i = media do pickup de mercado nas datas disponiveis do anuncio i
      indice_i   = observado_i / esperado_i        (>1 = vende acima do mercado)
      ajustado_i = pickup_global * indice_i        (volta a escala interpretavel)

Saida: analise/saida/metricas_listing.csv (1 linha por anuncio com preco)
"""
import pandas as pd, numpy as np, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "analise", "saida")

pr = pd.read_csv(os.path.join(OUT, "price_limpo.csv"), parse_dates=["date", "captura"])
det = pd.read_csv(os.path.join(OUT, "det_limpo.csv"), low_memory=False)

CAP_A = pd.Timestamp("2025-01-06")   # captura inicial
CAP_B = pd.Timestamp("2025-01-20")   # captura final (14 dias depois)
MIN_NOITES_A = 20                    # amostra minima para o pickup ser confiavel

A = pr[pr.captura == CAP_A]
B = pr[pr.captura == CAP_B]

print("=" * 78)
print("METRICAS AIRBNB")
print("=" * 78)

# ------------------------------------------------- 1. ADR (captura B, 91 dias)
adr = (B.groupby("airbnb_listing_id")
         .agg(adr=("price", "median"),
              adr_media=("price", "mean"),
              noites_ofertadas_B=("price", "size"))
         .reset_index())
print(f"\n[ADR] captura {CAP_B.date()} | {len(adr)} anuncios")
print(f"  mediana das medianas: R$ {adr.adr.median():,.0f}")
print(f"  p10/p90: R$ {adr.adr.quantile(.1):,.0f} / R$ {adr.adr.quantile(.9):,.0f}")
print("  NOTA: preco so existe para noite DISPONIVEL -> ADR e preco pedido do "
      "estoque nao vendido.")

# ---------------------------------------- 2. ocup_fev (janela fixa, captura B)
FEV = pd.date_range("2025-02-01", "2025-02-28")
lst_B = B.airbnb_listing_id.unique()
grid_f = pd.MultiIndex.from_product([lst_B, FEV],
                                    names=["airbnb_listing_id", "date"]).to_frame(index=False)
grid_f = grid_f.merge(B[["airbnb_listing_id", "date", "price"]], how="left")
ocup = (grid_f.assign(indisp=grid_f.price.isna())
              .groupby("airbnb_listing_id")
              .agg(ocup_fev=("indisp", "mean"),
                   adr_fev=("price", "median"))
              .reset_index())
print(f"\n[OCUP_FEV] janela fixa 01-28/fev vista de {CAP_B.date()} | {len(ocup)} anuncios")
print(f"  mediana: {ocup.ocup_fev.median():.1%} | media: {ocup.ocup_fev.mean():.1%}")
print(f"  quartis: {ocup.ocup_fev.quantile([.25,.5,.75]).round(3).to_dict()}")

# ------------------------------------------------- 3. pickup A->B, padronizado
janela = pd.date_range(CAP_B, min(A.date.max(), B.date.max()))
comuns = sorted(set(A.airbnb_listing_id) & set(B.airbnb_listing_id))
print(f"\n[PICKUP] {CAP_A.date()} -> {CAP_B.date()} | janela comum "
      f"{janela[0].date()}..{janela[-1].date()} ({len(janela)} noites) | "
      f"{len(comuns)} anuncios nas duas capturas")

g = pd.MultiIndex.from_product([comuns, janela],
                               names=["airbnb_listing_id", "date"]).to_frame(index=False)
g = g.merge(A[["airbnb_listing_id", "date", "price"]].rename(columns={"price": "pA"}), how="left")
g = g.merge(B[["airbnb_listing_id", "date", "price"]].rename(columns={"price": "pB"}), how="left")
g["disp_A"] = g.pA.notna()
g["disp_B"] = g.pB.notna()

ofer = g[g.disp_A].copy()               # so noites que estavam a venda em A
ofer["vendida"] = ~ofer.disp_B

pickup_global = ofer.vendida.mean()
p_data = ofer.groupby("date").vendida.mean().rename("p_mercado")
print(f"  pickup global: {pickup_global:.1%} "
      f"({int(ofer.vendida.sum()):,} de {len(ofer):,} noites-anuncio)")

ofer = ofer.merge(p_data, on="date", how="left")
pk = (ofer.groupby("airbnb_listing_id")
          .agg(noites_disp_A=("vendida", "size"),
               noites_vendidas=("vendida", "sum"),
               pickup_bruto=("vendida", "mean"),
               pickup_esperado=("p_mercado", "mean"))
          .reset_index())
pk = pk[pk.noites_disp_A >= MIN_NOITES_A].copy()
pk["indice_pickup"] = pk.pickup_bruto / pk.pickup_esperado
pk["pickup_ajustado"] = pickup_global * pk.indice_pickup

print(f"  anuncios com >= {MIN_NOITES_A} noites ofertadas em A: {len(pk)}")
print(f"  pickup bruto    mediana {pk.pickup_bruto.median():.1%}")
print(f"  pickup ajustado mediana {pk.pickup_ajustado.median():.1%} "
      f"| p10 {pk.pickup_ajustado.quantile(.1):.1%} "
      f"| p90 {pk.pickup_ajustado.quantile(.9):.1%}")
print(f"  correlacao bruto x ajustado: {pk.pickup_bruto.corr(pk.pickup_ajustado):.3f}")
print("  -> o ajuste importa: sem ele, anuncio com estoque em fevereiro parece "
      "mais demandado do que e.")

# --------------------------------------------------------- 4. juntar e RevPAN
m = adr.merge(ocup, on="airbnb_listing_id", how="outer") \
       .merge(pk, on="airbnb_listing_id", how="outer")

# (1) ranqueamento: preco x velocidade de venda em 14 dias
m["revpan_pickup"] = m.adr * m.pickup_ajustado
# (2) receita: preco x ocupacao observada de fevereiro (mesmo horizonte p/ todos)
m["revpan_ocup"] = m.adr * m.ocup_fev
m["receita_fev_obs"] = m.revpan_ocup * 28

m = m.merge(det, on="airbnb_listing_id", how="left")

print(f"\n[RESULTADO] {len(m)} anuncios com alguma metrica")
print(f"  com ADR:            {int(m.adr.notna().sum())}")
print(f"  com ocup_fev:       {int(m.ocup_fev.notna().sum())}")
print(f"  com pickup ajust.:  {int(m.pickup_ajustado.notna().sum())}")
print(f"  com revpan_pickup:  {int(m.revpan_pickup.notna().sum())}  <- base do ranking")

ok = m[m.revpan_pickup.notna()]
print(f"\n  revpan_pickup  mediana R$ {ok.revpan_pickup.median():,.0f} "
      f"| p25 R$ {ok.revpan_pickup.quantile(.25):,.0f} "
      f"| p75 R$ {ok.revpan_pickup.quantile(.75):,.0f}")
print(f"  revpan_ocup    mediana R$ {m.revpan_ocup.median():,.0f}")
print(f"  receita_fev_obs mediana R$ {m.receita_fev_obs.median():,.0f}")

# concordancia entre as duas metricas = teste de robustez (Teste 5 do plano)
sub = m.dropna(subset=["revpan_pickup", "revpan_ocup"])
print(f"\n[ROBUSTEZ] correlacao entre as duas metricas de demanda (n={len(sub)}):")
print(f"  pearson  revpan_pickup x revpan_ocup : {sub.revpan_pickup.corr(sub.revpan_ocup):.3f}")
print(f"  spearman revpan_pickup x revpan_ocup : "
      f"{sub.revpan_pickup.corr(sub.revpan_ocup, method='spearman'):.3f}")
print(f"  spearman pickup_ajustado x ocup_fev  : "
      f"{sub.pickup_ajustado.corr(sub.ocup_fev, method='spearman'):.3f}")
print(f"  spearman adr x pickup_ajustado       : "
      f"{sub.adr.corr(sub.pickup_ajustado, method='spearman'):.3f}   "
      f"(negativo = quem cobra mais vende mais devagar)")

# ------------------------------------------------------------------ 5. VIESES
# O pickup tem um risco de censura: anuncio muito demandado ja vendeu fevereiro,
# entao o estoque que lhe resta e de datas distantes (que quase nao vendem) e ele
# aparece com pickup BAIXO. Se isso for forte, o pickup nao serve para ranquear.
print("\n[VIES DE CENSURA] pickup por quartil de estoque disponivel em 06/01")
sub = sub.copy()
sub["q_estoque"] = pd.qcut(sub.noites_disp_A, 4, labels=["Q1 menos estoque",
                                                         "Q2", "Q3", "Q4 mais estoque"])
diag = sub.groupby("q_estoque", observed=True).agg(
    n=("airbnb_listing_id", "size"),
    noites_disp_A=("noites_disp_A", "median"),
    ocup_fev=("ocup_fev", "median"),
    pickup_ajustado=("pickup_ajustado", "median"),
    adr=("adr", "median"))
print(diag.round(3).to_string())
print(f"  spearman noites_disp_A x pickup_ajustado: "
      f"{sub.noites_disp_A.corr(sub.pickup_ajustado, method='spearman'):+.3f}")
print(f"  spearman noites_disp_A x ocup_fev       : "
      f"{sub.noites_disp_A.corr(sub.ocup_fev, method='spearman'):+.3f}  "
      f"(negativo forte e esperado: mais estoque livre = menos ocupado)")
print(f"  anuncios com pickup ZERO: {int((sub.pickup_ajustado==0).sum())} "
      f"({(sub.pickup_ajustado==0).mean():.1%})")
print("  destes, ocup_fev mediana: "
      f"{sub.loc[sub.pickup_ajustado==0,'ocup_fev'].median():.1%} vs "
      f"{sub.loc[sub.pickup_ajustado>0,'ocup_fev'].median():.1%} nos demais")

m.to_csv(os.path.join(OUT, "metricas_listing.csv"), index=False)
print(f"\nGRAVADO: analise/saida/metricas_listing.csv ({len(m)} x {m.shape[1]})")

# guarda o pickup de mercado por data (usado no relatorio)
p_data.reset_index().to_csv(os.path.join(OUT, "pickup_por_data.csv"), index=False)

# Tabela no grao NOITE-ANUNCIO. Necessaria porque 29,8% dos anuncios tem pickup
# zero: a mediana por anuncio fica instavel. Nas agregacoes por celula
# (bairro x quartos) usamos pickup AGRUPADO = noites vendidas / noites ofertadas,
# que junta o ruido em vez de mediar medianas.
ofer[["airbnb_listing_id", "date", "pA", "vendida"]].to_csv(
    os.path.join(OUT, "noites_pickup.csv"), index=False)
print(f"GRAVADO: analise/saida/noites_pickup.csv ({len(ofer):,} noites-anuncio)")

# Grade de fevereiro no grao noite-anuncio (para agregar ocupacao por celula)
grid_f[["airbnb_listing_id", "date", "price"]].assign(indisp=grid_f.price.isna()).to_csv(
    os.path.join(OUT, "noites_fev.csv"), index=False)
print(f"GRAVADO: analise/saida/noites_fev.csv ({len(grid_f):,} noites-anuncio)")
