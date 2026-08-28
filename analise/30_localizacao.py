# -*- coding: utf-8 -*-
"""
30_localizacao.py — ranking de bairros e de celulas (bairro x faixa de quartos).

Agregacao POR NOITE, nao por anuncio:
    pickup_celula = soma(noites vendidas) / soma(noites ofertadas)
Motivo: 29,8% dos anuncios tem pickup zero. Mediana de medianas colapsaria.
Agregar noites junta o ruido em vez de propaga-lo.

ADR da celula = mediana dos ADR dos anuncios (resistente a outlier de preco).
RevPAN da celula = ADR_celula * pickup_celula.

Criterio aprovado: bairro entra no ranking principal com n >= 20 anuncios com
pickup valido. Abaixo disso vai para o apendice, COM os numeros.

Saidas: rank_bairros.csv, rank_celulas.csv
"""
import pandas as pd, numpy as np, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "analise", "saida")
N_MIN = 20

met = pd.read_csv(os.path.join(OUT, "metricas_listing.csv"), low_memory=False)
noites = pd.read_csv(os.path.join(OUT, "noites_pickup.csv"), parse_dates=["date"])
fev = pd.read_csv(os.path.join(OUT, "noites_fev.csv"), parse_dates=["date"])

attrs = met[["airbnb_listing_id", "bairro", "faixa_quartos", "number_of_bedrooms",
             "listing_type", "adr", "pickup_ajustado", "ocup_fev"]]
noites = noites.merge(attrs, on="airbnb_listing_id", how="left")
fev = fev.merge(attrs, on="airbnb_listing_id", how="left")

# so anuncios que entraram no calculo de pickup (>= 20 noites ofertadas)
val = met[met.pickup_ajustado.notna()].copy()
noites = noites[noites.airbnb_listing_id.isin(val.airbnb_listing_id)]

print("=" * 88)
print("RANKING DE LOCALIZACAO")
print("=" * 88)
print(f"universo: {len(val)} anuncios com pickup valido, "
      f"de {met.adr.notna().sum()} com preco, de 4.441 anunciados")


def agrega(df_noites, df_fev, chaves):
    """pickup agrupado por noites + ADR mediano + ocupacao de fevereiro."""
    pk = df_noites.groupby(chaves).agg(
        noites_ofertadas=("vendida", "size"),
        noites_vendidas=("vendida", "sum"),
        n_airbnb=("airbnb_listing_id", "nunique"))
    pk["pickup"] = pk.noites_vendidas / pk.noites_ofertadas

    ad = df_noites.drop_duplicates("airbnb_listing_id").groupby(chaves).agg(
        adr=("adr", "median"))

    oc = df_fev[df_fev.airbnb_listing_id.isin(df_noites.airbnb_listing_id)] \
        .groupby(chaves).agg(ocup_fev=("indisp", "mean"))

    g = pk.join(ad).join(oc)
    g["revpan_pickup"] = g.adr * g.pickup
    g["revpan_ocup"] = g.adr * g.ocup_fev
    g["receita_fev_obs"] = g.revpan_ocup * 28
    return g.reset_index()


# ------------------------------------------------------------- 1. por bairro
b = agrega(noites, fev, ["bairro"]).sort_values("revpan_pickup", ascending=False)
b["amostra_ok"] = b.n_airbnb >= N_MIN

cols = ["bairro", "n_airbnb", "adr", "pickup", "revpan_pickup",
        "ocup_fev", "revpan_ocup", "receita_fev_obs"]
fmt = lambda d: (d[cols].assign(
    adr=d.adr.round(0), pickup=(100*d.pickup).round(1),
    revpan_pickup=d.revpan_pickup.round(0), ocup_fev=(100*d.ocup_fev).round(1),
    revpan_ocup=d.revpan_ocup.round(0), receita_fev_obs=d.receita_fev_obs.round(0))
    .rename(columns={"pickup": "pickup_%", "ocup_fev": "ocup_fev_%"}))

print(f"\n### RANKING PRINCIPAL — bairros com n >= {N_MIN}")
print(fmt(b[b.amostra_ok]).to_string(index=False))

print(f"\n### APENDICE — bairros com n < {N_MIN} (nao recomendados, mas visiveis)")
ap = b[~b.amostra_ok]
print(fmt(ap).to_string(index=False) if len(ap) else "  (nenhum)")
print(f"  -> {ap.n_airbnb.sum()} anuncios em {len(ap)} bairros fora do ranking")

# ordenacao alternativa = teste de robustez
print("\n### ROBUSTEZ — a ordem muda conforme a metrica?")
r = b[b.amostra_ok].copy()
cmp = pd.DataFrame({
    "por_revpan_pickup": r.sort_values("revpan_pickup", ascending=False).bairro.values,
    "por_revpan_ocup":   r.sort_values("revpan_ocup", ascending=False).bairro.values,
    "por_adr":           r.sort_values("adr", ascending=False).bairro.values,
}, index=[f"{i+1}o" for i in range(len(r))])
print(cmp.to_string())

# --------------------------------------------- 2. por bairro x faixa de quartos
c = agrega(noites, fev, ["bairro", "faixa_quartos"])
c["amostra_ok"] = c.n_airbnb >= N_MIN
c = c.sort_values("revpan_pickup", ascending=False)

print(f"\n\n### CELULAS bairro x quartos com n >= {N_MIN}")
cc = ["bairro", "faixa_quartos", "n_airbnb", "adr", "pickup",
      "revpan_pickup", "ocup_fev", "revpan_ocup"]
sel = c[c.amostra_ok]
print(sel[cc].assign(adr=sel.adr.round(0), pickup=(100*sel.pickup).round(1),
                     revpan_pickup=sel.revpan_pickup.round(0),
                     ocup_fev=(100*sel.ocup_fev).round(1),
                     revpan_ocup=sel.revpan_ocup.round(0)).to_string(index=False))
print(f"\n  celulas com n < {N_MIN}: {int((~c.amostra_ok).sum())} "
      f"({int(c.loc[~c.amostra_ok,'n_airbnb'].sum())} anuncios) — vao para o apendice")

# ------------------------------------------------------ 3. so faixa de quartos
q = agrega(noites, fev, ["faixa_quartos"]).sort_values("revpan_pickup", ascending=False)
print("\n\n### POR FAIXA DE QUARTOS (cidade toda, sem controlar bairro)")
qc = ["faixa_quartos", "n_airbnb", "adr", "pickup", "revpan_pickup", "ocup_fev", "revpan_ocup"]
print(q[qc].assign(adr=q.adr.round(0), pickup=(100*q.pickup).round(1),
                   revpan_pickup=q.revpan_pickup.round(0),
                   ocup_fev=(100*q.ocup_fev).round(1),
                   revpan_ocup=q.revpan_ocup.round(0)).to_string(index=False))

# ------------------------------------------------------------ 4. tipo de imovel
t = agrega(noites, fev, ["listing_type"]).sort_values("revpan_pickup", ascending=False)
print("\n### POR TIPO DE IMOVEL")
tc = ["listing_type", "n_airbnb", "adr", "pickup", "revpan_pickup", "ocup_fev"]
print(t[tc].assign(adr=t.adr.round(0), pickup=(100*t.pickup).round(1),
                   revpan_pickup=t.revpan_pickup.round(0),
                   ocup_fev=(100*t.ocup_fev).round(1)).to_string(index=False))

b.to_csv(os.path.join(OUT, "rank_bairros.csv"), index=False)
c.to_csv(os.path.join(OUT, "rank_celulas.csv"), index=False)
q.to_csv(os.path.join(OUT, "rank_quartos.csv"), index=False)
print("\nGRAVADO: rank_bairros.csv, rank_celulas.csv, rank_quartos.csv")
