# -*- coding: utf-8 -*-
"""
71_impacto_dedup.py — a recomendacao sobrevive as duas correcoes do script 70?

Correcao 1: DEDUPLICAR POR FICHA FISICA. 18,2% da base VivaReal e o mesmo imovel
            anunciado por corretores diferentes (URLs distintas, entao a dedup
            por link_url nao pegou). Isso enviesa as medianas de preco.
Correcao 2: RECLASSIFICAR Andorinha e Castelo Branco como Meia Praia. O titulo
            e a URL dizem 'meia praia' em 91,7% e 94,3% dos casos.

Recalcula a matriz de investimento e compara com a versao do relatorio.
"""
import pandas as pd, numpy as np, os, unicodedata, re
pd.set_option("display.width", 250)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT, DATA = os.path.join(BASE, "analise", "saida"), os.path.join(BASE, "data")
vr = pd.read_csv(os.path.join(OUT, "vr_limpo.csv"), low_memory=False)
cel = pd.read_csv(os.path.join(OUT, "rank_celulas.csv"))
met = pd.read_csv(os.path.join(OUT, "metricas_listing.csv"), low_memory=False)
mi_old = pd.read_csv(os.path.join(OUT, "matriz_investimento.csv"))

PCT_AQ, MOB_M2, PCT_CANAL, PCT_MANUT = 0.05, 1500, 0.15, 0.10
CEN = {"conservador_40": .40, "base_55": .55, "otimista_70": .70}
FIS = ["sale_price", "usable_area", "bedrooms", "bathrooms", "parking_spaces"]
ocup_mercado = met.ocup_fev.mean()

def sa(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()

print("=" * 100)
print("IMPACTO DAS CORRECOES NA RECOMENDACAO")
print("=" * 100)

# ------------------------------------------------------------------ correcoes
v0 = vr.copy()
v1 = vr.drop_duplicates(FIS).copy()
print(f"\n[correcao 1] dedup fisica: {len(v0)} -> {len(v1)} imoveis "
      f"(-{100*(1-len(v1)/len(v0)):.1f}%)")

v2 = v1.copy()
v2["bairro"] = v2.bairro.replace({"Andorinha": "Meia Praia", "Castelo Branco": "Meia Praia"})
mudou = int((v1.bairro.isin(["Andorinha", "Castelo Branco"])).sum())
print(f"[correcao 2] Andorinha + Castelo Branco -> Meia Praia: {mudou} imoveis")
print(f"  Meia Praia no VivaReal: {int((v1.bairro=='Meia Praia').sum())} -> "
      f"{int((v2.bairro=='Meia Praia').sum())} imoveis")

# tambem removo o compacto classificado errado (140 m2, titulo diz 3 dormitorios)
RX = r"(\d+)\s*(?:dormit|quarto|dorm\b|su[ií]te)"
def q_txt(t):
    m = re.findall(RX, sa(t))
    return max(int(x) for x in m) if m else None
v2["q_tit"] = v2.listing_title.map(q_txt)
ruim = v2[(v2.bedrooms <= 1) & (v2.q_tit > 1)]
v2 = v2.drop(index=ruim.index)
print(f"[correcao 3] removidos {len(ruim)} 'compactos' cujo titulo indica 2+ dormitorios")

def matriz(v, nome):
    pv = v.groupby(["bairro", "faixa_quartos"]).agg(
        n_vivareal=("sale_price", "size"), preco_mediano=("sale_price", "median"),
        area_mediana=("usable_area", "median"), preco_m2=("preco_m2", "median"),
        condominio=("monthly_condo_fee", "median"),
        iptu_anual=("yearly_iptu", "median")).reset_index()
    for c, g in [("condominio", v.monthly_condo_fee.median()),
                 ("iptu_anual", v.yearly_iptu.median())]:
        pb = v.groupby("bairro")[{"condominio": "monthly_condo_fee",
                                  "iptu_anual": "yearly_iptu"}[c]].median()
        pv[c] = pv[c].fillna(pv.bairro.map(pb)).fillna(g)
    m = cel.merge(pv, on=["bairro", "faixa_quartos"], how="inner")
    m["indice_demanda"] = m.ocup_fev / ocup_mercado
    m["investimento"] = m.preco_mediano*(1+PCT_AQ) + m.area_mediana*MOB_M2
    m["custo_fixo_ano"] = m.condominio*12 + m.iptu_anual
    for k, S in CEN.items():
        liq = m.adr*365*S*m.indice_demanda*(1-PCT_CANAL-PCT_MANUT) - m.custo_fixo_ano
        m[f"roi_{k}"] = liq / m.investimento
        m[f"liq_{k}"] = liq
    m["amostra_ok"] = (m.n_airbnb >= 20) & (m.n_vivareal >= 20)
    m["versao"] = nome
    return m

mA = matriz(v0, "relatorio (original)")
mC = matriz(v2, "corrigida")

print("\n" + "=" * 100)
print("RANKING CORRIGIDO (dedup fisica + Andorinha/Castelo Branco em Meia Praia)")
print("=" * 100)
s = mC[mC.amostra_ok].sort_values("roi_base_55", ascending=False)
print(s[["bairro", "faixa_quartos", "n_airbnb", "n_vivareal", "adr", "preco_mediano",
         "area_mediana", "investimento", "liq_base_55", "roi_base_55"]].assign(
    adr=s.adr.round(0), preco_mediano=(s.preco_mediano/1000).round(0),
    investimento=(s.investimento/1000).round(0),
    liq_base_55=(s.liq_base_55/1000).round(1),
    roi_base_55=(100*s.roi_base_55).round(2)).rename(
    columns={"preco_mediano": "preco_kR$", "investimento": "invest_kR$",
             "liq_base_55": "liq_kR$", "roi_base_55": "ROI_%"}).to_string(index=False))

print("\n### ANTES vs DEPOIS — celulas da recomendacao")
cmp_ = mA[["bairro", "faixa_quartos", "n_vivareal", "preco_mediano", "roi_base_55"]].merge(
    mC[["bairro", "faixa_quartos", "n_vivareal", "preco_mediano", "roi_base_55"]],
    on=["bairro", "faixa_quartos"], suffixes=("_antes", "_depois"))
cmp_ = cmp_[cmp_.n_vivareal_depois >= 20].sort_values("roi_base_55_depois", ascending=False)
print(cmp_.assign(
    preco_antes=(cmp_.preco_mediano_antes/1000).round(0),
    preco_depois=(cmp_.preco_mediano_depois/1000).round(0),
    ROI_antes=(100*cmp_.roi_base_55_antes).round(2),
    ROI_depois=(100*cmp_.roi_base_55_depois).round(2),
    delta=(100*(cmp_.roi_base_55_depois - cmp_.roi_base_55_antes)).round(2))[
    ["bairro", "faixa_quartos", "n_vivareal_antes", "n_vivareal_depois",
     "preco_antes", "preco_depois", "ROI_antes", "ROI_depois", "delta"]].to_string(index=False))

print("\n### A ORDEM MUDOU?")
oa = mA[mA.amostra_ok].sort_values("roi_base_55", ascending=False)
oa = (oa.bairro + " / " + oa.faixa_quartos).tolist()
oc = (s.bairro + " / " + s.faixa_quartos).tolist()
print(pd.DataFrame({"antes": oa + [""]*(max(len(oa),len(oc))-len(oa)),
                    "depois": oc + [""]*(max(len(oa),len(oc))-len(oc))},
                   index=[f"{i+1}o" for i in range(max(len(oa), len(oc)))]).to_string())
print(f"\n  1o lugar antes:  {oa[0]}")
print(f"  1o lugar depois: {oc[0]}")
print(f"  -> {'MANTEVE' if oa[0]==oc[0] else 'MUDOU'}")

print("\n### E o compacto no Centro?")
for nome, m in [("antes", mA), ("depois", mC)]:
    r = m[(m.bairro == "Centro") & (m.faixa_quartos == "0-1 (compacto)")]
    if len(r):
        r = r.iloc[0]
        print(f"  {nome:<7} n_vivareal={int(r.n_vivareal):>3} | "
              f"preco R$ {r.preco_mediano:>9,.0f} | R$/m2 {r.preco_m2:>7,.0f} | "
              f"ROI {100*r.roi_base_55:>5.2f}%")

ref = mC[(mC.bairro == "Centro") & (mC.faixa_quartos == "2")].iloc[0]
cc = mC[(mC.bairro == "Centro") & (mC.faixa_quartos == "0-1 (compacto)")]
if len(cc):
    cc = cc.iloc[0]
    print(f"\n  compacto vence 2 quartos no Centro? "
          f"{'SIM' if cc.roi_base_55 > ref.roi_base_55 else 'NAO'} "
          f"({100*cc.roi_base_55:.2f}% vs {100*ref.roi_base_55:.2f}%)")

print("\n### PREMIO DE m2 DO COMPACTO, APOS AS CORRECOES")
for b in ["Centro", "Meia Praia", "Morretes"]:
    a = v2[(v2.bairro == b) & (v2.faixa_quartos == "0-1 (compacto)")].preco_m2
    d = v2[(v2.bairro == b) & (v2.faixa_quartos == "2")].preco_m2
    if len(a) >= 3 and len(d) >= 3:
        print(f"  {b:<11} compacto R$ {a.median():>7,.0f}/m2 (n={len(a):>3}) vs "
              f"2q R$ {d.median():>7,.0f}/m2 (n={len(d):>3}) | "
              f"premio {100*(a.median()/d.median()-1):>+6.1f}%")

mC.to_csv(os.path.join(OUT, "matriz_investimento_corrigida.csv"), index=False)
print("\nGRAVADO: analise/saida/matriz_investimento_corrigida.csv")
