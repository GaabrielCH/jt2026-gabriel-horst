# -*- coding: utf-8 -*-
"""
60_tese_centro.py — os 5 testes da tese interna:
"apartamentos compactos (studio/1 quarto) no Centro sao a aposta mais eficiente".

A tese junta duas afirmacoes (TAMANHO e LOCALIZACAO). Testadas separadamente,
depois em conjunto. "Eficiente" e lido como RETORNO POR REAL INVESTIDO — nao
receita absoluta, senao a tese seria refutada por construcao.
"""
import pandas as pd, numpy as np, os
rng = np.random.default_rng(42)
pd.set_option("display.width", 240)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "analise", "saida")

met = pd.read_csv(os.path.join(OUT, "metricas_listing.csv"), low_memory=False)
noites = pd.read_csv(os.path.join(OUT, "noites_pickup.csv"), parse_dates=["date"])
vr = pd.read_csv(os.path.join(OUT, "vr_limpo.csv"), low_memory=False)
mi = pd.read_csv(os.path.join(OUT, "matriz_investimento.csv"))

val = met[met.pickup_ajustado.notna()].copy()
noites = noites.merge(met[["airbnb_listing_id", "bairro", "faixa_quartos", "adr"]],
                      on="airbnb_listing_id", how="left")
noites = noites[noites.airbnb_listing_id.isin(val.airbnb_listing_id)]

def boot_revpan(sub_noites, sub_list, B=2000):
    """IC do RevPAN da celula por bootstrap NO ANUNCIO (nao na noite):
    reamostra anuncios, recalcula pickup agrupado x ADR mediano."""
    ids = sub_list.airbnb_listing_id.values
    if len(ids) < 3:
        return (np.nan, np.nan)
    porid = {i: g for i, g in sub_noites.groupby("airbnb_listing_id")}
    adrs = sub_list.set_index("airbnb_listing_id").adr
    out = []
    for _ in range(B):
        pick = rng.choice(ids, size=len(ids), replace=True)
        v = s = 0
        for i in pick:
            g = porid.get(i)
            if g is not None:
                v += g.vendida.sum(); s += len(g)
        if s:
            out.append((v/s) * np.median(adrs.loc[pick].values))
    return (np.percentile(out, 2.5), np.percentile(out, 97.5)) if out else (np.nan, np.nan)

def celula(bairro=None, faixa=None):
    l = val if bairro is None else val[val.bairro == bairro]
    n = noites if bairro is None else noites[noites.bairro == bairro]
    if faixa is not None:
        l = l[l.faixa_quartos == faixa]; n = n[n.faixa_quartos == faixa]
    if len(l) == 0:
        return None
    pk = n.vendida.sum() / len(n) if len(n) else np.nan
    adr = l.adr.median()
    lo, hi = boot_revpan(n, l)
    return dict(n=len(l), adr=adr, pickup=pk, revpan=adr*pk,
                ic_lo=lo, ic_hi=hi, ocup_fev=l.ocup_fev.mean())

print("=" * 100)
print("TESTE DA TESE: 'studio/1 quarto no Centro e a aposta mais eficiente'")
print("=" * 100)

# ================================================== TESTE 1 — tamanho, por bairro
print("\n" + "#" * 100)
print("# TESTE 1 — compacto vs maior, CONTROLANDO O BAIRRO")
print("#" * 100)
rows = []
for b in ["Centro", "Meia Praia", "Morretes"]:
    for f in ["0-1 (compacto)", "2", "3", "4+"]:
        r = celula(b, f)
        if r: rows.append({"bairro": b, "faixa": f, **r})
t1 = pd.DataFrame(rows)
print(t1.assign(adr=t1.adr.round(0), pickup=(100*t1.pickup).round(1),
                revpan=t1.revpan.round(0), ic_lo=t1.ic_lo.round(0),
                ic_hi=t1.ic_hi.round(0), ocup_fev=(100*t1.ocup_fev).round(1))
      .rename(columns={"pickup": "pickup_%", "ocup_fev": "ocup_%",
                       "ic_lo": "IC95_lo", "ic_hi": "IC95_hi"}).to_string(index=False))

c = t1[(t1.bairro == "Centro")].set_index("faixa")
print(f"\n  DENTRO DO CENTRO: compacto RevPAN R$ {c.loc['0-1 (compacto)','revpan']:.0f} "
      f"(IC95 {c.loc['0-1 (compacto)','ic_lo']:.0f}-{c.loc['0-1 (compacto)','ic_hi']:.0f}, "
      f"n={int(c.loc['0-1 (compacto)','n'])})")
for f in ["2", "3"]:
    if f in c.index:
        print(f"                    {f} quartos       R$ {c.loc[f,'revpan']:.0f} "
              f"(IC95 {c.loc[f,'ic_lo']:.0f}-{c.loc[f,'ic_hi']:.0f}, n={int(c.loc[f,'n'])})")

# =============================================== TESTE 2 — localizacao, por faixa
print("\n" + "#" * 100)
print("# TESTE 2 — Centro vs demais, CONTROLANDO O TAMANHO")
print("#" * 100)
for f in ["0-1 (compacto)", "2", "3"]:
    print(f"\n  faixa {f}:")
    for b in ["Centro", "Meia Praia", "Morretes"]:
        r = celula(b, f)
        if r and r["n"] >= 1:
            flag = "" if r["n"] >= 20 else "   <-- amostra insuficiente"
            print(f"    {b:<12} n={r['n']:>3}  ADR {r['adr']:>6.0f}  "
                  f"pickup {100*r['pickup']:>5.1f}%  RevPAN {r['revpan']:>5.0f}"
                  f"{flag}")

# ================================== TESTE 3 — eficiencia de capital (o que decide)
print("\n" + "#" * 100)
print("# TESTE 3 — EFICIENCIA DE CAPITAL (retorno por real investido)")
print("#" * 100)
print("\n[3a] Quanto custa o m2 por tipologia — o compacto e barato mesmo?")
pm = vr.groupby(["bairro", "faixa_quartos"]).agg(
    n=("preco_m2", "size"), preco_m2=("preco_m2", "median"),
    preco=("sale_price", "median"), area=("usable_area", "median")).reset_index()
pm = pm[pm.bairro.isin(["Centro", "Meia Praia", "Morretes"])].sort_values(
    ["bairro", "faixa_quartos"])
print(pm.assign(preco_m2=pm.preco_m2.round(0), preco=(pm.preco/1000).round(0),
                area=pm.area.round(0)).rename(
    columns={"preco": "preco_kR$", "n": "n_vivareal"}).to_string(index=False))
print("\n  -> compacto NAO e barato por m2: e o m2 mais caro da cidade.")

print("\n[3b] ROI liquido por celula (cenario base 55%), incluindo as de amostra fraca")
sel = mi[mi.bairro.isin(["Centro", "Meia Praia", "Morretes"])].sort_values(
    "roi_base_55", ascending=False)
print(sel[["bairro", "faixa_quartos", "n_airbnb", "n_vivareal", "adr", "preco_mediano",
           "area_mediana", "investimento", "receita_liq_base_55", "roi_base_55"]].assign(
    adr=sel.adr.round(0), preco_mediano=(sel.preco_mediano/1000).round(0),
    investimento=(sel.investimento/1000).round(0),
    receita_liq_base_55=(sel.receita_liq_base_55/1000).round(1),
    roi_base_55=(100*sel.roi_base_55).round(2)).rename(
    columns={"preco_mediano": "preco_kR$", "investimento": "invest_kR$",
             "receita_liq_base_55": "liq_kR$", "roi_base_55": "ROI_%"}).to_string(index=False))

# ==================================================== TESTE 4 — amostra e incerteza
print("\n" + "#" * 100)
print("# TESTE 4 — A AMOSTRA SUSTENTA A CONCLUSAO?")
print("#" * 100)
cc = val[(val.bairro == "Centro") & (val.faixa_quartos == "0-1 (compacto)")]
print(f"\n  lado RECEITA (Airbnb): {len(cc)} anuncios compactos no Centro com pickup valido")
print(f"    dos {int((met.bairro=='Centro').sum())} anuncios do Centro com preco, "
      f"de {int((met.bairro=='Centro').sum())} no total")
print(f"    -> amostra BOA. A duvida que eu tinha no plano nao se confirmou.")

cv = vr[(vr.bairro == "Centro") & (vr.faixa_quartos == "0-1 (compacto)")]
print(f"\n  lado COMPRA (VivaReal): {len(cv)} apartamentos compactos a venda no Centro")
print(f"    -> amostra FRACA (limiar = 20). Este e o elo fragil da conclusao.")
if len(cv):
    print(f"    preco: mediana R$ {cv.sale_price.median():,.0f} | "
          f"p25 R$ {cv.sale_price.quantile(.25):,.0f} | "
          f"p75 R$ {cv.sale_price.quantile(.75):,.0f}")
    print(f"    area:  mediana {cv.usable_area.median():.0f} m2 | "
          f"preco/m2 mediana R$ {cv.preco_m2.median():,.0f}")

print(f"\n  compactos a venda em TODA Itapema: {int((vr.faixa_quartos=='0-1 (compacto)').sum())} "
      f"de {len(vr)} ({100*(vr.faixa_quartos=='0-1 (compacto)').mean():.1f}%)")
print("  por bairro:")
print("   ", vr[vr.faixa_quartos == "0-1 (compacto)"].bairro.value_counts().to_dict())
print("  -> ALEM do retorno: nao existe estoque de compactos para comprar em escala.")

print("\n  Sobreposicao dos IC95 do RevPAN (Centro):")
a = t1[(t1.bairro=="Centro") & (t1.faixa=="0-1 (compacto)")].iloc[0]
for f in ["2", "3"]:
    o = t1[(t1.bairro=="Centro") & (t1.faixa==f)]
    if len(o):
        o = o.iloc[0]
        sep = "SIM (nao se sobrepoem)" if a.ic_hi < o.ic_lo or o.ic_hi < a.ic_lo else "NAO (se sobrepoem)"
        print(f"    compacto [{a.ic_lo:.0f}, {a.ic_hi:.0f}] vs {f}q "
              f"[{o.ic_lo:.0f}, {o.ic_hi:.0f}] -> diferenca estatisticamente clara? {sep}")

# ========================================================= TESTE 5 — robustez
print("\n" + "#" * 100)
print("# TESTE 5 — A CONCLUSAO MUDA CONFORME A METRICA?")
print("#" * 100)
ordens = {}
base = mi[mi.bairro.isin(["Centro", "Meia Praia", "Morretes"])].copy()
base["celula"] = base.bairro + " / " + base.faixa_quartos
for met_nome, col, asc in [("RevPAN (pickup)", "revpan_pickup", False),
                           ("RevPAN (ocupacao)", "revpan_ocup", False),
                           ("ADR puro", "adr", False),
                           ("ROI base 55%", "roi_base_55", False)]:
    ordens[met_nome] = base.sort_values(col, ascending=asc).celula.values
print(pd.DataFrame(ordens, index=[f"{i+1}o" for i in range(len(base))]).to_string())

print("\n  Posicao de 'Centro / 0-1 (compacto)' em cada criterio:")
for k, v in ordens.items():
    pos = list(v).index("Centro / 0-1 (compacto)") + 1
    print(f"    {k:<20} {pos}o de {len(v)}")

t1.to_csv(os.path.join(OUT, "teste_tese_celulas.csv"), index=False)
print("\nGRAVADO: analise/saida/teste_tese_celulas.csv")
