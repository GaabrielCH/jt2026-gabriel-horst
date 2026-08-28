# -*- coding: utf-8 -*-
"""
70_compacto_centro.py — APROFUNDAMENTO 1: o elo fragil (preco do compacto, n=16)

Responde:
  (a) quem sao os 5 anuncios abaixo do ponto de virada — sao comparaveis ou erro de dado?
  (b) IC bootstrap do p25 com n=16 — quao instavel e essa estimativa?
  (c) ha comparaveis perdidos por divergencia de nomenclatura de bairro?
  (d) o lado da RECEITA e sensivel ao rotulo de bairro? (usa lat/long do Mesh)
  (e) "garimpo" e operacionalizavel? da para estimar reposicao de estoque?
"""
import pandas as pd, numpy as np, os, re, unicodedata
rng = np.random.default_rng(7)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT, DATA = os.path.join(BASE, "analise", "saida"), os.path.join(BASE, "data")
vr = pd.read_csv(os.path.join(OUT, "vr_limpo.csv"), low_memory=False)
vr_bruto = pd.read_csv(os.path.join(DATA, "VivaReal_Itapema.csv"), low_memory=False)
met = pd.read_csv(os.path.join(OUT, "metricas_listing.csv"), low_memory=False)
PONTO_VIRADA = 694_904

def sa(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()

print("=" * 104)
print("APROFUNDAMENTO 1 — o preco do compacto no Centro (n=16)")
print("=" * 104)

cv = vr[(vr.bairro == "Centro") & (vr.faixa_quartos == "0-1 (compacto)")].copy()

# ============================================================== (a) os 5 anuncios
print("\n" + "#" * 104)
print("# (a) OS ANUNCIOS ABAIXO DO PONTO DE VIRADA — sao comparaveis ou lixo de dado?")
print("#" * 104)
print(f"\nTodos os {len(cv)} compactos do Centro, ordenados por preco "
      f"(linha de corte = R$ {PONTO_VIRADA:,.0f}):\n")
cv = cv.sort_values("sale_price")
v = cv[["sale_price", "usable_area", "preco_m2", "bedrooms", "bathrooms",
        "parking_spaces", "monthly_condo_fee", "yearly_iptu", "advertiser_name",
        "listing_title"]].copy()
v["abaixo"] = np.where(cv.sale_price <= PONTO_VIRADA, "<<< SIM", "")
print(v.assign(sale_price=v.sale_price.map(lambda x: f"{x:,.0f}"),
               preco_m2=v.preco_m2.round(0),
               listing_title=v.listing_title.str.slice(0, 52)).to_string(index=False))

alvo = cv[cv.sale_price <= PONTO_VIRADA]
print(f"\n--- auditoria dos {len(alvo)} anuncios abaixo do corte ---")
for _, r in alvo.iterrows():
    flags = []
    if r.usable_area < 25: flags.append("AREA SUSPEITA (<25m2)")
    if r.bedrooms == 0: flags.append("bedrooms=0 (studio ou dado ausente?)")
    if pd.isna(r.monthly_condo_fee): flags.append("sem condominio informado")
    if r.preco_m2 < vr.preco_m2.quantile(.05): flags.append("R$/m2 no piso do mercado")
    if r.bathrooms == 0: flags.append("bathrooms=0")
    print(f"\n  R$ {r.sale_price:,.0f} | {r.usable_area:.0f} m2 | "
          f"{r.preco_m2:,.0f}/m2 | {int(r.bedrooms)}q {int(r.bathrooms)}b "
          f"{int(r.parking_spaces)}vg | condo {r.monthly_condo_fee}")
    print(f"    titulo: {str(r.listing_title)[:88]}")
    print(f"    corretor: {r.advertiser_name}")
    print(f"    ALERTAS: {'; '.join(flags) if flags else 'nenhum — parece comparavel legitimo'}")

print(f"\n  duplicatas de anunciante entre os {len(alvo)}: "
      f"{len(alvo) - alvo.advertiser_name.nunique()} "
      f"(se alto, e o mesmo estoque anunciado varias vezes)")
print(f"  areas: {sorted(alvo.usable_area.tolist())}")
print(f"  quartos: {alvo.bedrooms.value_counts().to_dict()}")

# =================================== (a2) AUDITORIA: a amostra de 16 e real?
print("\n" + "#" * 104)
print("# (a2) A AMOSTRA DE 16 E REAL? — duplicata fisica e erro de classificacao")
print("#" * 104)

FIS = ["sale_price", "usable_area", "bedrooms", "bathrooms", "parking_spaces"]
dup = cv[cv.duplicated(FIS, keep=False)].sort_values(FIS)
print(f"\n  [1] MESMO IMOVEL ANUNCIADO POR CORRETORES DIFERENTES")
print(f"  A limpeza deduplicou por link_url. Mas o mesmo imovel aparece com URLs")
print(f"  diferentes quando dois corretores o anunciam. Conferindo por ficha fisica:")
if len(dup):
    print(dup[["sale_price", "usable_area", "bathrooms", "parking_spaces",
               "monthly_condo_fee", "advertiser_name", "listing_title"]]
          .assign(sale_price=dup.sale_price.map(lambda x: f"{x:,.0f}"),
                  listing_title=dup.listing_title.str.slice(0, 40)).to_string(index=False))
n_unico = len(cv.drop_duplicates(FIS))
print(f"\n  -> {len(cv)} anuncios = {n_unico} imoveis distintos. "
      f"{len(cv)-n_unico} sao repeticao.")

print(f"\n  [2] O ROTULO 'Centro' BATE COM O TITULO?")
cv["txt2"] = cv.listing_title.map(sa)
fora = cv[cv.txt2.str.contains("meia praia", na=False)]
print(f"  {len(fora)} dos {len(cv)} anuncios rotulados Centro dizem 'MEIA PRAIA' no titulo:")
if len(fora):
    print(fora[["sale_price", "usable_area", "listing_title"]]
          .assign(sale_price=fora.sale_price.map(lambda x: f"{x:,.0f}")).to_string(index=False))

print(f"\n  [3] O CAMPO bedrooms BATE COM O TITULO?")
RX = r"(\d+)\s*(?:dormit|quarto|dorm\b|su[ií]te)"
def q_txt(t):
    m = re.findall(RX, sa(t))
    return max(int(x) for x in m) if m else None
cv["q_titulo"] = cv.listing_title.map(q_txt)
mis = cv[(cv.q_titulo.notna()) & (cv.q_titulo > 1)]
print(f"  {len(mis)} anuncios tem bedrooms<=1 no dado mas o titulo indica mais:")
if len(mis):
    print(mis[["sale_price", "usable_area", "bedrooms", "q_titulo", "listing_title"]]
          .assign(sale_price=mis.sale_price.map(lambda x: f"{x:,.0f}"),
                  listing_title=mis.listing_title.str.slice(0, 50)).to_string(index=False))
    print("  -> classificacao errada: nao e compacto. Contamina a estimativa por cima.")

limpo = cv.drop_duplicates(FIS)
limpo = limpo[~limpo.index.isin(mis.index)]
print(f"\n  [4] AMOSTRA APOS LIMPAR: {len(limpo)} imoveis "
      f"(de {len(cv)} linhas brutas)")
print(f"    mediana R$ {limpo.sale_price.median():,.0f} "
      f"(era R$ {cv.sale_price.median():,.0f})")
print(f"    p25     R$ {limpo.sale_price.quantile(.25):,.0f} "
      f"(era R$ {cv.sale_price.quantile(.25):,.0f})")
print(f"    R$/m2   {limpo.preco_m2.median():,.0f} (era {cv.preco_m2.median():,.0f})")

print(f"\n  [5] O PROBLEMA E SO DOS COMPACTOS OU DA BASE INTEIRA?")
g = vr.groupby(["bairro", "faixa_quartos"]).apply(
    lambda d: pd.Series({"linhas": len(d), "unicos": len(d.drop_duplicates(FIS))}))
g["pct_dup"] = (100*(1 - g.unicos/g.linhas)).round(1)
tot_l, tot_u = len(vr), len(vr.drop_duplicates(FIS))
print(f"    base inteira: {tot_l} linhas -> {tot_u} imoveis distintos "
      f"({100*(1-tot_u/tot_l):.1f}% de repeticao)")
print("    celulas usadas na recomendacao:")
for b, f in [("Centro","2"),("Centro","3"),("Meia Praia","2"),("Meia Praia","3"),
             ("Morretes","2"),("Centro","0-1 (compacto)")]:
    if (b,f) in g.index:
        r = g.loc[(b,f)]
        print(f"      {b:<11} {f:<16} {int(r.linhas):>5} linhas -> "
              f"{int(r.unicos):>5} unicos ({r.pct_dup:>4.1f}% repetido)")

print(f"\n  [6] O PRECO MEDIANO DAS CELULAS MUDA SE DEDUPLICAR?")
vru = vr.drop_duplicates(FIS)
for b, f in [("Centro","2"),("Meia Praia","2"),("Morretes","2"),("Centro","3"),
             ("Meia Praia","3"),("Meia Praia","4+")]:
    a = vr[(vr.bairro==b)&(vr.faixa_quartos==f)].sale_price.median()
    d = vru[(vru.bairro==b)&(vru.faixa_quartos==f)].sale_price.median()
    print(f"      {b:<11} {f:<4} R$ {a:>10,.0f} -> R$ {d:>10,.0f} "
          f"({100*(d/a-1):+.1f}%)")

# ==================================================== (b) bootstrap do p25, n=16
print("\n" + "#" * 104)
print("# (b) QUAO INSTAVEL E O p25 COM n=16?")
print("#" * 104)
x = cv.sale_price.values
B = 20000
p25 = np.array([np.percentile(rng.choice(x, len(x), replace=True), 25) for _ in range(B)])
p50 = np.array([np.percentile(rng.choice(x, len(x), replace=True), 50) for _ in range(B)])
print(f"\n  p25 pontual:  R$ {np.percentile(x,25):,.0f}")
print(f"  IC95 do p25:  R$ {np.percentile(p25,2.5):,.0f}  a  R$ {np.percentile(p25,97.5):,.0f}")
print(f"  largura do IC: R$ {np.percentile(p25,97.5)-np.percentile(p25,2.5):,.0f} "
      f"({100*(np.percentile(p25,97.5)-np.percentile(p25,2.5))/np.percentile(x,25):.0f}% "
      f"do valor pontual)")
print(f"\n  mediana pontual: R$ {np.median(x):,.0f}")
print(f"  IC95 da mediana: R$ {np.percentile(p50,2.5):,.0f} a R$ {np.percentile(p50,97.5):,.0f}")
print(f"\n  P(p25 <= ponto de virada de R$ {PONTO_VIRADA:,.0f}) = "
      f"{100*(p25 <= PONTO_VIRADA).mean():.1f}%")
print(f"  P(mediana <= ponto de virada)                 = "
      f"{100*(p50 <= PONTO_VIRADA).mean():.1f}%")

# ============================================ (c) comparaveis perdidos por rotulo
print("\n" + "#" * 104)
print("# (c) HA COMPARAVEIS PERDIDOS POR DIVERGENCIA DE NOMENCLATURA?")
print("#" * 104)
print("\n  LIMITE DURO: o VivaReal NAO tem latitude/longitude. As coordenadas do Mesh")
print("  sao dos anuncios de AIRBNB. Nao existe chave para geolocalizar um imovel a")
print("  venda. O que da para fazer e ler o bairro citado no proprio titulo/URL.")

vb = vr_bruto.copy()
vb["txt"] = vb.listing_title.map(sa) + " | " + vb.link_url.map(sa)
BR = ["centro", "meia praia", "morretes", "andorinha", "castelo branco",
      "canto da praia", "alto sao bento", "tabuleiro", "varzea", "ilhota", "casa branca"]
vb["bairro_txt"] = vb.txt.map(lambda t: (lambda h: h[0] if len(h) == 1 else None)
                              ([b for b in BR if b in t]))
vb["lbl"] = vb.suburb.map(lambda s: sa(s) if pd.notna(s) else None)
cmp_ = vb.dropna(subset=["bairro_txt", "lbl"])
print(f"\n  concordancia rotulo x texto: "
      f"{100*(cmp_.bairro_txt==cmp_.lbl).mean():.1f}% de {len(cmp_)} anuncios")

print("\n  >>> ACHADO: os 'bairros fantasma' sao sub-areas de Meia Praia:")
for b in ["andorinha", "castelo branco"]:
    s = cmp_[cmp_.lbl == b]
    print(f"    {b:<16} n={len(s):>4} | texto diz 'meia praia' em "
          f"{100*(s.bairro_txt=='meia praia').mean():>5.1f}% dos casos")
print("    -> os 19% do mercado de venda que estavam fora do ROI nao estao 'perdidos':")
print("       pertencem a Meia Praia, que ja esta no ranking.")

comp = vb[(vb.listing_type == "apartamento") & (vb.bedrooms <= 1) &
          (vb.business_types.isin(["Venda", "Ambos"])) &
          (vb.usable_area.between(20, 400))]
print(f"\n  compactos com 'centro' citado no texto, por rotulo de suburb:")
cen = comp[comp.txt.str.contains("centro", na=False)]
print("   ", cen.suburb.value_counts().to_dict())
extras = cen[cen.suburb.map(lambda s: sa(s) if pd.notna(s) else "") != "centro"]
print(f"\n  -> {len(extras)} compactos citam Centro mas estao rotulados em outro bairro.")
if len(extras):
    print(extras[["suburb", "sale_price", "usable_area", "listing_title"]]
          .assign(listing_title=lambda d: d.listing_title.str.slice(0, 55)).to_string(index=False))
    amp = pd.concat([cv.sale_price, extras.sale_price])
    print(f"\n  amostra ampliada: n={len(amp)} (era {len(cv)})")
    print(f"    mediana R$ {amp.median():,.0f} (era R$ {cv.sale_price.median():,.0f})")
    print(f"    p25     R$ {amp.quantile(.25):,.0f} (era R$ {cv.sale_price.quantile(.25):,.0f})")

# ============================== (d) o lado da RECEITA e sensivel ao rotulo?
print("\n" + "#" * 104)
print("# (d) E O LADO DA RECEITA? (aqui SIM ha lat/long — via Mesh)")
print("#" * 104)
def hav(la1, lo1, la2, lo2):
    R = 6371.0
    p1, p2 = np.radians(la1), np.radians(la2)
    dp, dl = np.radians(la2-la1), np.radians(lo2-lo1)
    a = np.sin(dp/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2*R*np.arcsin(np.sqrt(a))

geo = met.dropna(subset=["latitude", "longitude"]).copy()
lat0 = geo.loc[geo.bairro == "Centro", "latitude"].median()
lon0 = geo.loc[geo.bairro == "Centro", "longitude"].median()
geo["km_centro"] = hav(geo.latitude, geo.longitude, lat0, lon0)
ctr = geo[geo.bairro == "Centro"]
print(f"\n  centroide do Centro (mediana dos anuncios rotulados Centro): "
      f"{lat0:.5f}, {lon0:.5f}")
print("\n  distancia ao centroide do Centro, por rotulo de bairro (km):")
print(geo.groupby("bairro").km_centro.describe()[["count", "25%", "50%", "75%"]]
      .round(2).sort_values("50%").to_string())

raio = ctr.km_centro.quantile(.75)
print(f"\n  raio que cobre 75% do Centro rotulado: {raio:.2f} km")
prox = geo[(geo.km_centro <= raio) & (geo.pickup_ajustado.notna())]
print(f"  anuncios com pickup dentro desse raio: {len(prox)} "
      f"(rotulados Centro: {int((prox.bairro=='Centro').sum())}, "
      f"outros: {int((prox.bairro!='Centro').sum())})")
print("  composicao por rotulo:", prox.bairro.value_counts().to_dict())

pc = prox[prox.faixa_quartos == "0-1 (compacto)"]
lc = geo[(geo.bairro == "Centro") & (geo.faixa_quartos == "0-1 (compacto)")
         & geo.pickup_ajustado.notna()]
print(f"\n  RevPAN do compacto — definicao por ROTULO vs por GEOGRAFIA:")
for nome, s in [("rotulo 'Centro'", lc), (f"raio de {raio:.2f} km", pc)]:
    if len(s):
        pk = s.pickup_ajustado.median()
        print(f"    {nome:<22} n={len(s):>3} | ADR R$ {s.adr.median():>5.0f} | "
              f"RevPAN R$ {(s.adr.median()*pk):>5.0f} | ocup {100*s.ocup_fev.mean():>4.1f}%")
print("  -> se os dois baterem, a conclusao do lado da receita nao depende do rotulo.")

# ======================================================== (e) garimpo e viavel?
print("\n" + "#" * 104)
print("# (e) 'GARIMPO' E OPERACIONALIZAVEL?")
print("#" * 104)
print(f"\n  LIMITE DURO: VivaReal tem {vr_bruto.aquisition_date.nunique()} data de captura "
      f"({vr_bruto.aquisition_date.unique()[0][:10]}).")
print("  E uma FOTOGRAFIA, nao uma serie. NAO da para estimar frequencia de reposicao")
print("  de estoque, tempo de permanencia do anuncio, nem taxa de chegada de barganha.")
print("  Qualquer numero de 'quantos aparecem por mes' seria inventado. Nao vou inventar.")
print("\n  O que da para medir — dispersao no corte transversal:")
print(f"    compactos no Centro abaixo do ponto de virada: {len(alvo)} de {len(cv)} "
      f"({100*len(alvo)/len(cv):.0f}%)")
tot = vr[vr.faixa_quartos == "0-1 (compacto)"]
print(f"    compactos em Itapema abaixo do ponto de virada: "
      f"{int((tot.sale_price<=PONTO_VIRADA).sum())} de {len(tot)} "
      f"({100*(tot.sale_price<=PONTO_VIRADA).mean():.0f}%)")
print(f"    dispersao de preco dos compactos do Centro: "
      f"CV = {cv.sale_price.std()/cv.sale_price.mean():.2f}")
print(f"    2 quartos no Centro, para comparar:            "
      f"CV = {vr[(vr.bairro=='Centro')&(vr.faixa_quartos=='2')].sale_price.pipe(lambda s: s.std()/s.mean()):.2f}")
print(f"\n    corretores distintos com compacto no Centro: {cv.advertiser_name.nunique()} "
      f"para {len(cv)} anuncios")
