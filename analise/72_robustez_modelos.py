# -*- coding: utf-8 -*-
"""
72_robustez_modelos.py — APROFUNDAMENTO 2: "a demanda nao e explicavel" e
conclusao sobre o fenomeno ou artefato do modelo?

R2 negativo em arvore com poucas amostras pode ser overfitting do modelo, nao
ausencia de sinal. Para separar as duas hipoteses:

  1. Modelos REGULARIZADOS (Ridge, Lasso) alem da arvore e do OLS.
  2. RepeatedKFold (5 folds x 10 repeticoes) em vez de um split unico,
     reportando media E desvio entre folds.
  3. OLS com holdout, para comparar R2 fora da amostra com o R2 dentro.
  4. CONTROLE POSITIVO: o mesmo pipeline aplicado ao ADR. Se ele detectar
     sinal no ADR e nao no pickup, o pipeline funciona e a ausencia e real.
  5. CONTROLE NEGATIVO: alvo embaralhado. Da o piso de R2 esperado por acaso.
"""
import pandas as pd, numpy as np, os, warnings
from sklearn.linear_model import RidgeCV, LassoCV, LinearRegression
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import RepeatedKFold, cross_val_score, train_test_split
from sklearn.metrics import r2_score
warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "analise", "saida")
met = pd.read_csv(os.path.join(OUT, "metricas_listing.csv"), low_memory=False)

def montar(df):
    d = df.copy()
    d["tem_rating"] = d.star_rating.notna()
    d["star_rating_f"] = d.star_rating.fillna(d.star_rating.median())
    d["log_reviews"] = np.log1p(d.number_of_reviews)
    d["host_multi"] = (d.anuncios_do_host >= 5)
    AM = [c for c in d.columns if c.startswith("am_") and 0.02 < d[c].mean() < 0.98]
    NUM = ["number_of_bedrooms", "number_of_bathrooms", "number_of_guests",
           "picture_count", "star_rating_f", "log_reviews", "cleaning_fee"]
    BOOL = ["is_superhost", "is_professional", "is_guest_favorite", "can_instant_book",
            "tem_rating", "host_multi"] + AM
    X = d[NUM + BOOL].copy()
    for c in BOOL:
        X[c] = X[c].astype(float)
    X = X.fillna(X.median())
    bd = pd.get_dummies(d.bairro.where(d.bairro.isin(["Meia Praia", "Centro", "Morretes"]),
                                       "Outro"), prefix="b").astype(float)
    return pd.concat([X, bd.drop(columns=["b_Meia Praia"])], axis=1), d

MODELOS = {
    "media (baseline)": DummyRegressor(strategy="mean"),
    "OLS":              make_pipeline(StandardScaler(), LinearRegression()),
    "Ridge (CV)":       make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 4, 40))),
    "Lasso (CV)":       make_pipeline(StandardScaler(), LassoCV(cv=5, random_state=0, max_iter=20000)),
    "RandomForest":     RandomForestRegressor(n_estimators=400, min_samples_leaf=5, random_state=0),
    "GradBoost":        GradientBoostingRegressor(n_estimators=300, max_depth=3,
                                                  learning_rate=0.05, random_state=0),
}
CV = RepeatedKFold(n_splits=5, n_repeats=10, random_state=0)

print("=" * 100)
print("APROFUNDAMENTO 2 — R2 negativo: artefato do modelo ou do fenomeno?")
print("=" * 100)
print(f"\nvalidacao: RepeatedKFold 5 folds x 10 repeticoes = 50 estimativas por modelo")

Xp, dp = montar(met[met.pickup_ajustado.notna()])
Xo, do_ = montar(met[met.ocup_fev.notna()])

ALVOS = [
    ("ADR  [CONTROLE POSITIVO]", np.log(dp.adr), Xp),
    ("pickup ajustado",          dp.pickup_ajustado, Xp),
    ("RevPAN (pickup)",          dp.revpan_pickup, Xp),
    ("ocupacao fevereiro",       do_.ocup_fev, Xo),
    ("RevPAN (ocupacao)",        do_.revpan_ocup, Xo),
]

linhas = []
for nome, y, X in ALVOS:
    ok = y.notna() & np.isfinite(y)
    Xf, yf = X[ok], y[ok].values
    print("\n" + "-" * 100)
    print(f"{nome}   n={len(yf)}")
    print("-" * 100)
    print(f"  {'modelo':<20} {'R2 medio':>9} {'desvio':>8} {'min':>8} {'max':>8} "
          f"{'% folds >0':>11}")
    for mn, mod in MODELOS.items():
        sc = cross_val_score(mod, Xf, yf, cv=CV, scoring="r2")
        print(f"  {mn:<20} {sc.mean():>9.3f} {sc.std():>8.3f} {sc.min():>8.3f} "
              f"{sc.max():>8.3f} {100*(sc>0).mean():>10.0f}%")
        linhas.append({"alvo": nome, "modelo": mn, "r2_medio": sc.mean(),
                       "desvio": sc.std(), "pct_folds_pos": (sc > 0).mean()})

    # OLS: dentro da amostra vs holdout
    Xtr, Xte, ytr, yte = train_test_split(Xf, yf, test_size=0.3, random_state=0)
    ols = make_pipeline(StandardScaler(), LinearRegression()).fit(Xtr, ytr)
    r2_in = r2_score(ytr, ols.predict(Xtr))
    r2_out = r2_score(yte, ols.predict(Xte))
    print(f"  {'OLS holdout 70/30':<20} dentro={r2_in:>6.3f}  fora={r2_out:>6.3f}  "
          f"queda={r2_in-r2_out:>6.3f}")

    # controle negativo: alvo embaralhado
    rng = np.random.default_rng(0)
    sc0 = cross_val_score(make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3,4,40))),
                          Xf, rng.permutation(yf), cv=CV, scoring="r2")
    print(f"  {'Ridge c/ alvo embaralhado':<20} {sc0.mean():>9.3f} "
          f"(piso esperado por acaso)")

res = pd.DataFrame(linhas)
print("\n\n" + "=" * 100)
print("RESUMO — melhor R2 fora da amostra por alvo (excluindo o baseline)")
print("=" * 100)
melhor = (res[res.modelo != "media (baseline)"]
          .sort_values("r2_medio", ascending=False)
          .groupby("alvo", sort=False).head(1)
          .sort_values("r2_medio", ascending=False))
print(melhor.assign(r2_medio=melhor.r2_medio.round(3), desvio=melhor.desvio.round(3),
                    pct_folds_pos=(100*melhor.pct_folds_pos).round(0)).to_string(index=False))

print("\nLEITURA:")
print("  - Se o ADR tem R2 alto e os alvos de demanda ficam perto de zero MESMO com")
print("    Ridge/Lasso (que nao sofrem overfitting como a arvore), a ausencia de")
print("    sinal e do fenomeno, nao do modelo.")
print("  - Se algum modelo regularizado resgatar R2 relevante (>0,15) na demanda,")
print("    a conclusao original estava otimista demais e precisa ser revista.")

res.to_csv(os.path.join(OUT, "robustez_modelos.csv"), index=False)
print("\nGRAVADO: analise/saida/robustez_modelos.csv")
