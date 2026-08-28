# -*- coding: utf-8 -*-
"""
10_limpeza.py — aplica os tratamentos da secao 2 do PLANO.md e grava dados limpos.

Saidas em analise/saida/:
  det_limpo.csv    - 1 linha por anuncio Airbnb (+ bairro, +host, +amenities booleanas)
  price_limpo.csv  - painel de precos com datas parseadas
  vr_limpo.csv     - VivaReal filtrado para apartamentos a venda
  log_limpeza.txt  - registro do que foi removido/alterado
"""
import pandas as pd, numpy as np, os, json, re, unicodedata, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "analise", "saida")
os.makedirs(OUT, exist_ok=True)

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(str(msg))

r = lambda f: pd.read_csv(os.path.join(DATA, f), low_memory=False)

# ---------------------------------------------------------------- utilitarios
def norm_txt(s):
    """minuscula, sem acento, sem espaco duplo — para casar nomes de bairro."""
    if pd.isna(s):
        return np.nan
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()

# Mapa canonico de bairros. Chave = forma normalizada; valor = nome de exibicao.
MAPA_BAIRRO = {
    "meia praia": "Meia Praia",
    "meia praia - frente mar": "Meia Praia",
    "ocean tower": "Meia Praia",          # predio, nao bairro; fica em Meia Praia
    "centro": "Centro",
    "morretes": "Morretes",
    "tabuleiro dos oliveiras": "Tabuleiro dos Oliveiras",
    "tabuleiro": "Tabuleiro dos Oliveiras",
    "taboleiro": "Tabuleiro dos Oliveiras",
    "casa branca": "Casa Branca",
    "alto sao bento": "Alto Sao Bento",
    "ilhota": "Ilhota",
    "varzea": "Varzea",
    "canto da praia": "Canto da Praia",
    "sertao do trombudo": "Sertao do Trombudo",
    "sertaozinho": "Sertaozinho",
    "leopoldo zarling": "Leopoldo Zarling",
    "areal": "Areal",
    "jardim praiamar": "Jardim Praiamar",
    "jardim praia mar": "Jardim Praiamar",
    "lameiro": "Lameiro",
    "andorinha": "Andorinha",             # so existe no VivaReal
    "castelo branco": "Castelo Branco",   # so existe no VivaReal
    "estreito": "Estreito",
    "itapema": np.nan,                    # cidade no campo de bairro = sem info
    "none": np.nan,
}

def canon_bairro(s):
    n = norm_txt(s)
    if pd.isna(n):
        return np.nan
    return MAPA_BAIRRO.get(n, s if isinstance(s, str) else np.nan)

# Amenities que a hipotese de investimento sugere importar (short stay em praia)
AMEN_ALVO = {
    "piscina":        [r"\bpiscina\b"],
    "vista_mar":      [r"vista para o mar", r"vista para a praia", r"frente ?mar"],
    "ar_condicionado":[r"ar[- ]condicionado"],
    "churrasqueira":  [r"churrasqueira"],
    "estacionamento": [r"estacionamento", r"garagem"],
    "wifi":           [r"\bwifi\b", r"wi-?fi"],
    "elevador":       [r"elevador"],
    "academia":       [r"academia"],
    "maq_lavar":      [r"m[aá]quina de lavar"],
    "pet_friendly":   [r"permitidos animais", r"aceita animais", r"pets? permitidos"],
    "beira_mar":      [r"beira[- ]mar", r"p[eé] na areia", r"acesso a praia"],
}

def flags_amenities(serie):
    """serie de strings JSON -> DataFrame booleano."""
    txt = serie.fillna("").astype(str).map(norm_txt).fillna("")
    out = {}
    for nome, pats in AMEN_ALVO.items():
        pats_n = [norm_txt(p) if not p.startswith("\\b") else p for p in pats]
        rx = "|".join(pats)
        out["am_" + nome] = txt.str.contains(rx, regex=True, na=False)
    return pd.DataFrame(out, index=serie.index)


log("=" * 80)
log("LIMPEZA — inicio")
log("=" * 80)

# ================================================================= 1. DETAILS
det = r("Details_Itapema.csv")
n0 = len(det)
log(f"\n[DETAILS] entrada: {n0} linhas")

# (7) colunas mortas
mortas = []
for c in ["latitude", "longitude", "min_nights"]:
    if c in det.columns and det[c].nunique(dropna=False) <= 1:
        mortas.append(c)
det = det.drop(columns=mortas)
log(f"  colunas removidas por serem constantes: {mortas}")

# (5) 0 = placeholder de nulo nos ratings
cols_rating = ["star_rating", "accuracy_rating", "checkin_rating", "cleanliness_rating",
               "communication_rating", "location_rating", "value_rating",
               "guest_satisfaction_overall"]
for c in cols_rating:
    z = int((det[c] == 0).sum())
    det[c] = det[c].replace(0, np.nan)
    log(f"  {c}: {z} zeros -> NaN")
log(f"  (number_of_reviews==0 mantido como valor real: "
    f"{int((det.number_of_reviews == 0).sum())} anuncios sem review)")

# booleanos vindos como texto
for c in ["can_instant_book", "is_professional", "is_new_listing"]:
    det[c] = det[c].map({"True": True, "False": False, True: True, False: False})

# amenities -> flags
det = pd.concat([det, flags_amenities(det["amenities"])], axis=1)
log("  flags de amenities criadas: " + ", ".join("am_" + k for k in AMEN_ALVO))
log("  prevalencia: " + str({k: round(float(det["am_" + k].mean()), 3) for k in AMEN_ALVO}))

# faixa de quartos (usada em toda a analise)
def faixa_q(q):
    if q <= 1:  return "0-1 (compacto)"
    if q == 2:  return "2"
    if q == 3:  return "3"
    return "4+"
det["faixa_quartos"] = det["number_of_bedrooms"].map(faixa_q)
log("  faixa_quartos: " + str(det.faixa_quartos.value_counts().to_dict()))

# ==================================================================== 2. MESH
mesh = r("Mesh_Ids_Data_Itapema.csv")
mesh["bairro"] = mesh["suburb"].map(canon_bairro)
log(f"\n[MESH] {len(mesh)} linhas | bairros nulos apos canonizar: "
    f"{int(mesh.bairro.isna().sum())}")
nao_map = sorted(set(mesh.suburb.map(norm_txt).dropna()) - set(MAPA_BAIRRO))
log(f"  suburbs sem regra de mapeamento: {nao_map if nao_map else 'nenhum'}")

det = det.merge(mesh[["airbnb_listing_id", "bairro", "latitude", "longitude"]],
                on="airbnb_listing_id", how="left", validate="1:1")
log(f"  join Details<-Mesh: {int(det.bairro.notna().sum())}/{len(det)} com bairro")

# =================================================================== 3. HOSTS
hos = r("Hosts_ids_Itapema.csv")
log(f"\n[HOSTS] entrada: {len(hos)} linhas, {hos.owner_id.nunique()} owner_id distintos")
hos = hos.drop(columns=[c for c in ["response_rate_shown", "response_time_shown"]
                        if hos[c].isna().all()])
log("  colunas 100% nulas removidas: response_rate_shown, response_time_shown")
# (6) deduplicar pelo snapshot mais recente
hos["host_snapshot_date"] = pd.to_datetime(hos["host_snapshot_date"])
hos = (hos.sort_values("host_snapshot_date")
          .drop_duplicates("owner_id", keep="last"))
log(f"  apos dedup pelo snapshot mais recente: {len(hos)} linhas")

det = det.merge(
    hos[["owner_id", "is_superhost", "is_verified", "number_of_reviews_host",
         "star_rating_host", "years_host", "months_host"]],
    on="owner_id", how="left", validate="m:1")
log(f"  join Details<-Hosts: {int(det.is_superhost.notna().sum())}/{len(det)} com host")

# anuncios por host = proxy de operador profissional
n_por_host = det.groupby("owner_id").size().rename("anuncios_do_host")
det = det.merge(n_por_host, on="owner_id", how="left")
log(f"  anuncios por host: mediana={det.anuncios_do_host.median():.0f}, "
    f"max={det.anuncios_do_host.max()}")

assert len(det) == n0, f"join inflou linhas: {len(det)} != {n0}"
log(f"  [OK] Details permanece com {len(det)} linhas apos os joins")

# =================================================================== 4. PRICE
pr = r("Price_AV_Itapema.csv")
log(f"\n[PRICE_AV] entrada: {len(pr)} linhas")
pr["date"] = pd.to_datetime(pr["date"])
pr["captura"] = pd.to_datetime(pr["aquisition_date"]).dt.normalize()
dups = int(pr.duplicated(["airbnb_listing_id", "date", "captura"]).sum())
log(f"  duplicatas em (listing,date,captura): {dups}")
if dups:
    pr = pr.drop_duplicates(["airbnb_listing_id", "date", "captura"])
# outlier absurdo de preco (1 caso > 20k)
alto = int((pr.price > 20000).sum())
pr = pr[pr.price <= 20000]
log(f"  removidas {alto} linhas com price > R$20.000 (outlier)")
log(f"  capturas: {[str(x.date()) for x in sorted(pr.captura.unique())]}")
log(f"  saida: {len(pr)} linhas, {pr.airbnb_listing_id.nunique()} listings")

# ================================================================ 5. VIVAREAL
vr = r("VivaReal_Itapema.csv")
log(f"\n[VIVAREAL] entrada: {len(vr)} linhas")

d = int(vr.duplicated("link_url").sum())
vr = vr.drop_duplicates("link_url")
log(f"  (10) removidas {d} duplicatas de link_url -> {len(vr)}")

vr = vr[vr.business_types.isin(["Venda", "Ambos"])]
log(f"  apenas venda: {len(vr)}")

antes = len(vr)
vr = vr[vr.listing_type == "apartamento"]
log(f"  (9) apenas apartamentos: {len(vr)} (removidos {antes-len(vr)}: "
    f"casa/terreno/comercial/outros)")

antes = len(vr)
vr = vr[(vr.usable_area >= 20) & (vr.usable_area <= 400)]
log(f"  area util entre 20 e 400 m2: {len(vr)} (removidos {antes-len(vr)})")

# winsorizar preco em p1-p99
p1, p99 = vr.sale_price.quantile([0.01, 0.99])
fora = int(((vr.sale_price < p1) | (vr.sale_price > p99)).sum())
vr = vr[(vr.sale_price >= p1) & (vr.sale_price <= p99)]
log(f"  preco entre p1={p1:,.0f} e p99={p99:,.0f}: removidos {fora} -> {len(vr)}")

# condominio e IPTU: 0 tratado como ausente (apartamento sem condominio e implausivel)
z = int((vr.monthly_condo_fee == 0).sum())
vr["monthly_condo_fee"] = vr["monthly_condo_fee"].replace(0, np.nan)
log(f"  monthly_condo_fee: {z} zeros -> NaN "
    f"(agora {vr.monthly_condo_fee.isna().sum()} nulos de {len(vr)})")
z = int((vr.yearly_iptu == 0).sum())
vr["yearly_iptu"] = vr["yearly_iptu"].replace(0, np.nan)
log(f"  yearly_iptu: {z} zeros -> NaN")

vr["bairro"] = vr["suburb"].map(canon_bairro)
nao_map_vr = sorted(set(vr.suburb.map(norm_txt).dropna()) - set(MAPA_BAIRRO))
log(f"  (8) suburbs sem regra: {nao_map_vr if nao_map_vr else 'nenhum'}")
log(f"  bairros nulos: {int(vr.bairro.isna().sum())}")
vr["preco_m2"] = vr.sale_price / vr.usable_area
vr["faixa_quartos"] = vr["bedrooms"].map(faixa_q)

# quais bairros do VivaReal nao existem no Airbnb (ficam de fora do ROI)
so_vr = sorted(set(vr.bairro.dropna()) - set(det.bairro.dropna()))
perdidos = int(vr.bairro.isin(so_vr).sum())
log(f"  bairros que existem no VivaReal mas NAO no Airbnb: {so_vr}")
log(f"    -> {perdidos} anuncios de venda ({100*perdidos/len(vr):.1f}%) ficarao "
    f"fora da matriz de ROI por falta de contraparte de receita")

# =================================================================== gravacao
det.to_csv(os.path.join(OUT, "det_limpo.csv"), index=False)
pr.to_csv(os.path.join(OUT, "price_limpo.csv"), index=False)
vr.to_csv(os.path.join(OUT, "vr_limpo.csv"), index=False)

log("\n" + "=" * 80)
log(f"GRAVADO em analise/saida/")
log(f"  det_limpo.csv   {len(det):>6} linhas x {det.shape[1]} colunas")
log(f"  price_limpo.csv {len(pr):>6} linhas x {pr.shape[1]} colunas")
log(f"  vr_limpo.csv    {len(vr):>6} linhas x {vr.shape[1]} colunas")
log("=" * 80)

with open(os.path.join(OUT, "log_limpeza.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))
