# -*- coding: utf-8 -*-
"""
40_drivers.py — que caracteristicas explicam a receita.

Decompoe o problema em tres modelos, porque RevPAN = PRECO x DEMANDA e os dois
lados respondem a coisas diferentes:
    A) log(ADR)          -> o que faz cobrar mais caro
    B) pickup_ajustado   -> o que faz vender mais rapido
    C) revpan_pickup     -> o efeito liquido (o que interessa para investir)

Uma caracteristica pode subir o preco e derrubar a velocidade de venda; so o
modelo C diz se compensa. Objetivo e PESO E SINAL, nao previsao — por isso OLS
com erros robustos, mais uma arvore (Gradient Boosting) como checagem de
nao-linearidade.
"""
import pandas as pd, numpy as np, os, warnings
import statsmodels.api as sm
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold
warnings.filterwarnings("ignore")
pd.set_option("display.width", 200)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "analise", "saida")
met = pd.read_csv(os.path.join(OUT, "metricas_listing.csv"), low_memory=False)

df = met[met.pickup_ajustado.notna()].copy()
print("=" * 88)
print(f"DRIVERS DE RECEITA — n = {len(df)} anuncios com pickup valido")
print("=" * 88)

AMEN = [c for c in df.columns if c.startswith("am_")]
# descarta amenity degenerada (prevalencia 0 ou 100%)
AMEN = [c for c in AMEN if 0.02 < df[c].mean() < 0.98]
print(f"\namenities usadas ({len(AMEN)}): {[a[3:] for a in AMEN]}")
desc = [a[3:] for a in df.columns if a.startswith("am_") and a not in AMEN]
print(f"amenities descartadas por serem quase constantes: {desc}")

df["tem_rating"] = df.star_rating.notna()
df["star_rating_f"] = df.star_rating.fillna(df.star_rating.median())
df["log_reviews"] = np.log1p(df.number_of_reviews)
df["host_multi"] = (df.anuncios_do_host >= 5)

NUM = ["number_of_bedrooms", "number_of_bathrooms", "number_of_guests",
       "picture_count", "star_rating_f", "log_reviews", "cleaning_fee"]
BOOL = ["is_superhost", "is_professional", "is_guest_favorite", "can_instant_book",
        "tem_rating", "host_multi"] + AMEN

X = df[NUM + BOOL].copy()
for c in BOOL:
    X[c] = X[c].astype(float)
X = X.fillna(X.median())

# bairro como dummy, referencia = Meia Praia (maior mercado)
bd = pd.get_dummies(df.bairro.where(df.bairro.isin(["Meia Praia", "Centro", "Morretes"]),
                                    "Outro"), prefix="bairro").astype(float)
bd = bd.drop(columns=["bairro_Meia Praia"])
X = pd.concat([X, bd], axis=1)

ALVOS = {
    "A) log(ADR) — o que permite cobrar caro": np.log(df.adr),
    "B) pickup ajustado — o que faz vender rapido": df.pickup_ajustado,
    "C) RevPAN (preco x velocidade) — efeito liquido": df.revpan_pickup,
}

resumo = {}
for nome, y in ALVOS.items():
    ok = y.notna() & np.isfinite(y)
    Xf, yf = X[ok], y[ok]
    # coeficientes padronizados: comparaveis entre variaveis de escalas diferentes
    Xz = (Xf - Xf.mean()) / Xf.std().replace(0, 1)
    mod = sm.OLS(yf, sm.add_constant(Xz)).fit(cov_type="HC3")

    print("\n" + "-" * 88)
    print(nome)
    print(f"  n={int(ok.sum())}  R2={mod.rsquared:.3f}  R2_aj={mod.rsquared_adj:.3f}")
    t = pd.DataFrame({"coef_padron": mod.params, "p": mod.pvalues}).drop("const")
    t = t.reindex(t.coef_padron.abs().sort_values(ascending=False).index)
    sig = t[t.p < 0.05]
    print(f"  significantes a 5% ({len(sig)} de {len(t)}):")
    if len(sig):
        print(sig.assign(coef_padron=sig.coef_padron.round(3),
                         p=sig.p.round(4)).to_string())
    else:
        print("    nenhuma")
    resumo[nome] = t

    # checagem nao-linear
    gb = GradientBoostingRegressor(random_state=0, n_estimators=300, max_depth=3,
                                   learning_rate=0.05)
    cv = cross_val_score(gb, Xf, yf, cv=KFold(5, shuffle=True, random_state=0), scoring="r2")
    gb.fit(Xf, yf)
    imp = pd.Series(gb.feature_importances_, index=Xf.columns).sort_values(ascending=False)
    print(f"  [arvore] R2 validacao-cruzada = {cv.mean():.3f} (+/- {cv.std():.3f})")
    print(f"  top 8 importancias: {', '.join(f'{k} {v:.2f}' for k,v in imp.head(8).items())}")

# -------------------------------------------------------------- 2. CONTRAPROVA
# Os modelos B e C deram R2 ~ 0 e a arvore deu R2 de validacao NEGATIVO (pior que
# chutar a media). Antes de concluir "nao ha sinal", testo se o problema e a
# METRICA: o pickup usa 77 noites e tem 30% de zeros. A ocupacao de fevereiro usa
# janela fixa, 780 anuncios e distribuicao bem menos degenerada.
print("\n\n" + "=" * 88)
print("CONTRAPROVA — os mesmos modelos com a metrica de demanda menos ruidosa")
print("=" * 88)

df2 = met[met.ocup_fev.notna()].copy()
df2["tem_rating"] = df2.star_rating.notna()
df2["star_rating_f"] = df2.star_rating.fillna(df2.star_rating.median())
df2["log_reviews"] = np.log1p(df2.number_of_reviews)
df2["host_multi"] = (df2.anuncios_do_host >= 5)
X2 = df2[NUM + BOOL].copy()
for c in BOOL:
    X2[c] = X2[c].astype(float)
X2 = X2.fillna(X2.median())
bd2 = pd.get_dummies(df2.bairro.where(df2.bairro.isin(["Meia Praia", "Centro", "Morretes"]),
                                      "Outro"), prefix="bairro").astype(float)
bd2 = bd2.drop(columns=["bairro_Meia Praia"])
X2 = pd.concat([X2, bd2], axis=1)

for nome, y in {"B') ocupacao de fevereiro": df2.ocup_fev,
                "C') RevPAN via ocupacao": df2.revpan_ocup}.items():
    ok = y.notna() & np.isfinite(y)
    Xf, yf = X2[ok], y[ok]
    Xz = (Xf - Xf.mean()) / Xf.std().replace(0, 1)
    mod = sm.OLS(yf, sm.add_constant(Xz)).fit(cov_type="HC3")
    print(f"\n{nome}  n={int(ok.sum())}  R2={mod.rsquared:.3f}")
    t = pd.DataFrame({"coef_padron": mod.params, "p": mod.pvalues}).drop("const")
    t = t.reindex(t.coef_padron.abs().sort_values(ascending=False).index)
    sig = t[t.p < 0.05]
    print(f"  significantes a 5% ({len(sig)} de {len(t)}):")
    print(sig.assign(coef_padron=sig.coef_padron.round(3), p=sig.p.round(4)).to_string()
          if len(sig) else "    nenhuma")
    gb = GradientBoostingRegressor(random_state=0, n_estimators=300, max_depth=3,
                                   learning_rate=0.05)
    cv = cross_val_score(gb, Xf, yf, cv=KFold(5, shuffle=True, random_state=0), scoring="r2")
    print(f"  [arvore] R2 validacao-cruzada = {cv.mean():.3f} (+/- {cv.std():.3f})")

# ------------------------------------------------- leitura direta em medianas
print("\n\n" + "=" * 88)
print("LEITURA DIRETA — mediana por caracteristica (sem modelo, para conferir sinal)")
print("=" * 88)
for c in ["am_vista_mar", "am_piscina", "am_beira_mar", "am_elevador", "am_churrasqueira",
          "is_superhost", "is_guest_favorite", "is_professional", "host_multi"]:
    g = df.groupby(df[c].astype(bool)).agg(
        n=("adr", "size"), adr=("adr", "median"),
        pickup=("pickup_ajustado", "median"), revpan=("revpan_pickup", "median"))
    if len(g) == 2:
        d = g.loc[True] - g.loc[False]
        print(f"{c[3:] if c.startswith('am_') else c:>18} | "
              f"com={int(g.loc[True,'n']):>3} sem={int(g.loc[False,'n']):>3} | "
              f"ADR {g.loc[True,'adr']:>6.0f} vs {g.loc[False,'adr']:>6.0f} "
              f"({d['adr']:+6.0f}) | RevPAN {g.loc[True,'revpan']:>5.0f} vs "
              f"{g.loc[False,'revpan']:>5.0f} ({d['revpan']:+5.0f})")

# tabela de drivers para o relatorio
pd.concat({k: v for k, v in resumo.items()}, names=["modelo", "variavel"]) \
  .to_csv(os.path.join(OUT, "drivers_coeficientes.csv"))
print("\nGRAVADO: analise/saida/drivers_coeficientes.csv")
