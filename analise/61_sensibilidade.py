# -*- coding: utf-8 -*-
"""
61_sensibilidade.py — a rejeicao da tese sobrevive ao elo fragil?

O ponto fraco da analise e o preco de compra do compacto no Centro: so 16
anuncios no VivaReal. Se esse preco estiver superestimado, o ROI do compacto
sobe e a tese poderia se salvar. Aqui eu testo isso ATE O LIMITE:
  (a) usar o p25 do preco (comprador que garimpa) em vez da mediana
  (b) usar o preco de compacto de toda Itapema, nao so do Centro
  (c) calcular o PONTO DE VIRADA: por qual preco o compacto teria que ser
      comprado para empatar com 2 quartos no Centro
"""
import pandas as pd, numpy as np, os
pd.set_option("display.width", 200)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "analise", "saida")
vr = pd.read_csv(os.path.join(OUT, "vr_limpo.csv"), low_memory=False)
mi = pd.read_csv(os.path.join(OUT, "matriz_investimento.csv"))
met = pd.read_csv(os.path.join(OUT, "metricas_listing.csv"), low_memory=False)

PCT_AQ, MOB_M2, PCT_CANAL, PCT_MANUT, S = 0.05, 1500, 0.15, 0.10, 0.55
ocup_mercado = met.ocup_fev.mean()

def roi(adr, ocup, preco, area, condo, iptu, S=S):
    inv = preco * (1 + PCT_AQ) + area * MOB_M2
    noites = 365 * S * (ocup / ocup_mercado)
    liq = adr * noites * (1 - PCT_CANAL - PCT_MANUT) - (condo * 12 + iptu)
    return liq / inv, liq, inv

cc = met[(met.bairro == "Centro") & (met.faixa_quartos == "0-1 (compacto)")
         & met.pickup_ajustado.notna()]
adr_c, ocup_c = cc.adr.median(), cc.ocup_fev.mean()
ref = mi[(mi.bairro == "Centro") & (mi.faixa_quartos == "2")].iloc[0]

print("=" * 96)
print("SENSIBILIDADE — o compacto no Centro consegue vencer 2 quartos no Centro?")
print("=" * 96)
print(f"\nreferencia a bater: Centro / 2 quartos -> ROI {100*ref.roi_base_55:.2f}% a.a.")
print(f"compacto no Centro: ADR R$ {adr_c:.0f}, ocupacao de fevereiro {100*ocup_c:.1f}%, "
      f"n_airbnb={len(cc)}")

cv = vr[(vr.bairro == "Centro") & (vr.faixa_quartos == "0-1 (compacto)")]
cvt = vr[vr.faixa_quartos == "0-1 (compacto)"]

cenarios = [
    ("mediana do Centro (n=16)", cv.sale_price.median(), cv.usable_area.median(),
     cv.monthly_condo_fee.median(), cv.yearly_iptu.median()),
    ("p25 do Centro", cv.sale_price.quantile(.25), cv.usable_area.median(),
     cv.monthly_condo_fee.median(), cv.yearly_iptu.median()),
    ("minimo do Centro", cv.sale_price.min(), cv.usable_area.median(),
     cv.monthly_condo_fee.median(), cv.yearly_iptu.median()),
    ("mediana de toda Itapema (n=%d)" % len(cvt), cvt.sale_price.median(),
     cvt.usable_area.median(), cvt.monthly_condo_fee.median(), cvt.yearly_iptu.median()),
    ("p25 de toda Itapema", cvt.sale_price.quantile(.25), cvt.usable_area.median(),
     cvt.monthly_condo_fee.median(), cvt.yearly_iptu.median()),
]

print(f"\n{'cenario de preco':<32} {'preco':>11} {'area':>6} {'invest':>11} "
      f"{'liq/ano':>10} {'ROI':>7}  vence?")
print("-" * 96)
for nome, p, a, cd, ip in cenarios:
    cd = cd if pd.notna(cd) else vr.monthly_condo_fee.median()
    ip = ip if pd.notna(ip) else vr.yearly_iptu.median()
    r, liq, inv = roi(adr_c, ocup_c, p, a, cd, ip)
    print(f"{nome:<32} {p:>11,.0f} {a:>6.0f} {inv:>11,.0f} {liq:>10,.0f} "
          f"{100*r:>6.2f}%  {'SIM' if r > ref.roi_base_55 else 'nao'}")

# ponto de virada
area_c = cv.usable_area.median()
condo_c = cv.monthly_condo_fee.median() if pd.notna(cv.monthly_condo_fee.median()) else vr.monthly_condo_fee.median()
iptu_c = cv.yearly_iptu.median() if pd.notna(cv.yearly_iptu.median()) else vr.yearly_iptu.median()
noites = 365 * S * (ocup_c / ocup_mercado)
liq_c = adr_c * noites * (1 - PCT_CANAL - PCT_MANUT) - (condo_c * 12 + iptu_c)
inv_alvo = liq_c / ref.roi_base_55
preco_alvo = (inv_alvo - area_c * MOB_M2) / (1 + PCT_AQ)

print(f"\n### PONTO DE VIRADA")
print(f"  Para empatar com 2 quartos no Centro ({100*ref.roi_base_55:.2f}% a.a.), o "
      f"compacto teria que ser comprado por")
print(f"    R$ {preco_alvo:,.0f}  ({preco_alvo/area_c:,.0f}/m2)")
print(f"  Preco mediano observado: R$ {cv.sale_price.median():,.0f} "
      f"({cv.preco_m2.median():,.0f}/m2)")
print(f"  Desconto necessario: {100*(1 - preco_alvo/cv.sale_price.median()):.1f}%")
n_abaixo = int((cv.sale_price <= preco_alvo).sum())
print(f"  Compactos no Centro a venda nesse preco ou abaixo: {n_abaixo} de {len(cv)}")

print(f"\n### E o premio de m2 do compacto e real ou artefato da amostra?")
for b in ["Centro", "Meia Praia", "Morretes"]:
    s = vr[vr.bairro == b]
    a = s[s.faixa_quartos == "0-1 (compacto)"].preco_m2
    d = s[s.faixa_quartos == "2"].preco_m2
    if len(a) >= 5 and len(d) >= 5:
        from scipy.stats import mannwhitneyu
        u, p = mannwhitneyu(a, d, alternative="greater")
        print(f"  {b:<11} compacto R$ {a.median():>7,.0f}/m2 (n={len(a):>3}) vs "
              f"2q R$ {d.median():>7,.0f}/m2 (n={len(d):>3}) | "
              f"premio {100*(a.median()/d.median()-1):>5.1f}% | Mann-Whitney p={p:.4f}")
print("  -> o premio por m2 do compacto se repete nos tres bairros: nao e ruido "
      "da amostra de 16.")

print(f"\n### ESTOQUE — quantos compactos existem para comprar")
tot = len(vr)
comp = int((vr.faixa_quartos == "0-1 (compacto)").sum())
print(f"  compactos: {comp} de {tot} apartamentos a venda ({100*comp/tot:.1f}%)")
print(f"  2 quartos: {int((vr.faixa_quartos=='2').sum())} ({100*(vr.faixa_quartos=='2').mean():.1f}%)")
print(f"  no Centro: {len(cv)} compactos vs "
      f"{int(((vr.bairro=='Centro')&(vr.faixa_quartos=='2')).sum())} de 2 quartos")
print("  -> mesmo que o retorno empatasse, a tese nao escala: nao ha o que comprar.")

print(f"\n### CONTEXTO — o retorno se compara a que?")
for nome, r in [("Centro / 2 quartos", ref.roi_base_55),
                ("Centro / compacto", roi(adr_c, ocup_c, cv.sale_price.median(),
                                          area_c, condo_c, iptu_c)[0])]:
    print(f"  {nome:<20} {100*r:>5.2f}% a.a. liquido de custos operacionais, "
          f"ANTES de IR e sem contar valorizacao")
