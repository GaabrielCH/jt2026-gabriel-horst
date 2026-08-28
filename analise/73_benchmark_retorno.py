# -*- coding: utf-8 -*-
"""
73_benchmark_retorno.py — APROFUNDAMENTO 3: contextualizar o retorno de ~6% a.a.

Benchmark (consultado em 28/08/2026):
  Selic meta = 14,00% a.a. (Copom, 05/08/2026)
  CDI        = 13,90% a.a.
Uso o CDI como taxa livre de risco liquida de referencia para o investidor PJ.

Responde:
  (a) qual o gap entre o retorno operacional e a taxa livre de risco
  (b) que ocupacao / que ADR fechariam esse gap, mantidos os demais custos
  (c) quanto do gap o "premio de operacao profissional" ja fecha, medido
      nos proprios dados (profissional vs amador, superhost vs nao)
"""
import pandas as pd, numpy as np, os, warnings
import statsmodels.api as sm
warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "analise", "saida")
mi = pd.read_csv(os.path.join(OUT, "matriz_investimento_corrigida.csv"))
met = pd.read_csv(os.path.join(OUT, "metricas_listing.csv"), low_memory=False)

SELIC, CDI = 0.1400, 0.1390
PCT_AQ, MOB_M2, PCT_CANAL, PCT_MANUT, S = 0.05, 1500, 0.15, 0.10, 0.55
ocup_mercado = met.ocup_fev.mean()

print("=" * 100)
print("APROFUNDAMENTO 3 — o retorno de ~6% contra a taxa livre de risco")
print("=" * 100)
print(f"\n  Selic meta (Copom 05/08/2026): {100*SELIC:.2f}% a.a.")
print(f"  CDI                          : {100*CDI:.2f}% a.a.")

# =========================================================== (a) o gap
print("\n" + "#" * 100)
print("# (a) O TAMANHO DO GAP")
print("#" * 100)
sel = mi[mi.amostra_ok].sort_values("roi_base_55", ascending=False)
t = sel[["bairro", "faixa_quartos", "roi_base_55", "investimento", "liq_base_55"]].copy()
t["gap_pp"] = 100*(CDI - t.roi_base_55)
t["quanto_do_cdi"] = 100*t.roi_base_55/CDI
t["renda_cdi"] = t.investimento * CDI
print("\n" + t.assign(
    ROI=(100*t.roi_base_55).round(2), invest_kR=(t.investimento/1000).round(0),
    liq_kR=(t.liq_base_55/1000).round(1), renda_cdi_kR=(t.renda_cdi/1000).round(1),
    gap_pp=t.gap_pp.round(2), pct_cdi=t.quanto_do_cdi.round(0))[
    ["bairro", "faixa_quartos", "ROI", "invest_kR", "liq_kR", "renda_cdi_kR",
     "gap_pp", "pct_cdi"]].to_string(index=False))
print("\n  liq_kR   = resultado operacional anual do imovel")
print("  renda_cdi_kR = o que o MESMO capital renderia no CDI, sem risco e sem operacao")

best = sel.iloc[0]
ref = mi[(mi.bairro == "Centro") & (mi.faixa_quartos == "2")].iloc[0]
print(f"\n  Centro/2q: R$ {ref.liq_base_55:,.0f} de operacao contra "
      f"R$ {ref.investimento*CDI:,.0f} no CDI.")
print(f"  O imovel entrega {100*ref.roi_base_55/CDI:.0f}% do que o CDI entrega — "
      f"assumindo risco, iliquidez e trabalho operacional.")

# ============================================ (b) o que fecharia o gap
print("\n" + "#" * 100)
print("# (b) O QUE PRECISARIA ACONTECER PARA BATER O CDI")
print("#" * 100)

def cenario(r, S_novo=None, adr_mult=1.0, preco_mult=1.0):
    S_ = S_novo if S_novo is not None else S
    inv = r.preco_mediano*preco_mult*(1+PCT_AQ) + r.area_mediana*MOB_M2
    liq = (r.adr*adr_mult)*365*S_*r.indice_demanda*(1-PCT_CANAL-PCT_MANUT) - r.custo_fixo_ano
    return liq/inv

for nome, r in [("Centro / 2q", ref), (f"{best.bairro} / {best.faixa_quartos} (melhor)", best)]:
    print(f"\n  --- {nome} — ROI atual {100*r.roi_base_55:.2f}% ---")
    alvo_liq = CDI * (r.preco_mediano*(1+PCT_AQ) + r.area_mediana*MOB_M2)
    receita_nec = (alvo_liq + r.custo_fixo_ano) / (1-PCT_CANAL-PCT_MANUT)
    noites_atuais = 365*S*r.indice_demanda

    S_nec = receita_nec / (r.adr*365*r.indice_demanda)
    print(f"    [1] So por OCUPACAO (ADR fixo em R$ {r.adr:.0f}):")
    print(f"        fator de realizacao teria que ir de {100*S:.0f}% para "
          f"{100*S_nec:.1f}%  ({'IMPOSSIVEL: >100%' if S_nec>1 else 'possivel'})")
    print(f"        noites vendidas/ano: {noites_atuais:.0f} -> "
          f"{365*S_nec*r.indice_demanda:.0f}")

    adr_nec = receita_nec / noites_atuais
    print(f"    [2] So por PRECO (ocupacao fixa):")
    print(f"        ADR teria que ir de R$ {r.adr:.0f} para R$ {adr_nec:.0f} "
          f"({100*(adr_nec/r.adr-1):+.0f}%)")
    p90 = met[met.faixa_quartos == r.faixa_quartos].adr.quantile(.90)
    print(f"        p90 do ADR nessa tipologia na cidade: R$ {p90:.0f} "
          f"-> {'ainda insuficiente' if p90 < adr_nec else 'alcancavel no topo do mercado'}")

    print(f"    [3] So por PRECO DE COMPRA (receita fixa):")
    liq = r.liq_base_55
    inv_alvo = liq/CDI
    preco_alvo = (inv_alvo - r.area_mediana*MOB_M2)/(1+PCT_AQ)
    print(f"        precisaria comprar por R$ {preco_alvo:,.0f} em vez de "
          f"R$ {r.preco_mediano:,.0f} ({100*(preco_alvo/r.preco_mediano-1):+.0f}%)")

    print(f"    [4] COMBINACAO realista (+20% ADR e +20% ocupacao simultaneos):")
    r4 = cenario(r, S_novo=min(S*1.2, 0.95), adr_mult=1.2)
    print(f"        ROI {100*r4:.2f}%  -> {'bate o CDI' if r4>=CDI else 'ainda abaixo do CDI'}")

# ================================= (c) quanto o premio profissional fecha
print("\n" + "#" * 100)
print("# (c) QUANTO O PREMIO DE OPERACAO PROFISSIONAL JA FECHA DESSE GAP?")
print("#" * 100)

d = met[met.ocup_fev.notna()].copy()
d["log_adr"] = np.log(d.adr)
d["prof"] = d.is_professional.fillna(False).astype(float)
d["super"] = d.is_superhost.fillna(False).astype(float)
d["fav"] = d.is_guest_favorite.fillna(False).astype(float)
d["multi"] = (d.anuncios_do_host >= 5).astype(float)

print("\n  [c1] Comparacao bruta (sem controle):")
for c, lab in [("prof", "is_professional"), ("super", "is_superhost"),
               ("fav", "is_guest_favorite"), ("multi", "host com 5+ anuncios")]:
    g = d.groupby(d[c] == 1).agg(n=("adr", "size"), adr=("adr", "median"),
                                 ocup=("ocup_fev", "mean"))
    if len(g) == 2:
        print(f"    {lab:<22} n={int(g.loc[True,'n']):>3} | ADR "
              f"{g.loc[True,'adr']:>5.0f} vs {g.loc[False,'adr']:>5.0f} "
              f"({100*(g.loc[True,'adr']/g.loc[False,'adr']-1):+5.1f}%) | ocup "
              f"{100*g.loc[True,'ocup']:>4.1f}% vs {100*g.loc[False,'ocup']:>4.1f}% "
              f"({100*(g.loc[True,'ocup']-g.loc[False,'ocup']):+4.1f}pp)")

print("\n  [c2] Com controle de bairro, tipologia, capacidade e reputacao:")
ctrl = pd.get_dummies(d.bairro.where(d.bairro.isin(["Meia Praia","Centro","Morretes"]),"Outro"),
                      prefix="b", drop_first=True).astype(float)
ctrl = pd.concat([ctrl, pd.get_dummies(d.faixa_quartos, prefix="q", drop_first=True).astype(float),
                  d[["number_of_guests","number_of_bathrooms"]].astype(float),
                  np.log1p(d.number_of_reviews).rename("log_rev")], axis=1)
ctrl = ctrl.astype(float)
ctrl = ctrl.fillna(ctrl.median()).replace([np.inf, -np.inf], np.nan).fillna(0.0)
for alvo, lab in [("log_adr", "log(ADR)"), ("ocup_fev", "ocupacao fev")]:
    X = sm.add_constant(pd.concat([d[["prof","super","fav","multi"]], ctrl], axis=1))
    y = d[alvo]
    ok = y.notna() & np.isfinite(y)
    mod = sm.OLS(y[ok], X[ok].astype(float)).fit(cov_type="HC3")
    print(f"\n    alvo = {lab}  (R2={mod.rsquared:.3f})")
    for v in ["prof", "super", "fav", "multi"]:
        cf, p = mod.params[v], mod.pvalues[v]
        eft = f"{100*(np.exp(cf)-1):+.1f}%" if alvo == "log_adr" else f"{100*cf:+.1f}pp"
        print(f"      {v:<7} {eft:>8}  p={p:.4f}  "
              f"{'significativo' if p<0.05 else 'NAO significativo'}")

print("\n  [c3] Se a Seazone entregasse o premio profissional medido, o ROI vai a quanto?")
Xa = sm.add_constant(pd.concat([d[["prof","super","fav","multi"]], ctrl], axis=1)).astype(float)
ma = sm.OLS(d.log_adr, Xa).fit(cov_type="HC3")
mo = sm.OLS(d.ocup_fev, Xa).fit(cov_type="HC3")
adr_up = np.exp(ma.params["prof"] + ma.params["super"]) - 1
ocu_up = mo.params["prof"] + mo.params["super"]
print(f"    premio combinado (profissional + superhost), controlado:")
print(f"      ADR {100*adr_up:+.1f}%   ocupacao {100*ocu_up:+.1f}pp")
for nome, r in [("Centro / 2q", ref)]:
    idx_novo = (r.ocup_fev + ocu_up) / ocup_mercado
    inv = r.preco_mediano*(1+PCT_AQ) + r.area_mediana*MOB_M2
    liq = r.adr*(1+adr_up)*365*S*idx_novo*(1-PCT_CANAL-PCT_MANUT) - r.custo_fixo_ano
    print(f"    {nome}: ROI {100*r.roi_base_55:.2f}% -> {100*liq/inv:.2f}%  "
          f"(CDI = {100*CDI:.2f}%)")
    print(f"      fecha {100*((liq/inv)-r.roi_base_55)/(CDI-r.roi_base_55):.0f}% do gap")

print("\n  [c4] E a valorizacao do imovel? Quanto teria que valorizar por ano")
print("       para o total (operacao + valorizacao) empatar com o CDI:")
for nome, r in [("Centro / 2q", ref), (f"{best.bairro}/{best.faixa_quartos}", best)]:
    print(f"    {nome:<18} {100*(CDI - r.roi_base_55):.2f}% a.a. de valorizacao")
print("       (a base e uma fotografia de um momento — nao ha como medir "
      "valorizacao com estes dados)")
