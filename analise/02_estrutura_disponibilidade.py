# -*- coding: utf-8 -*-
import pandas as pd, numpy as np, os
pd.set_option("display.width",220)
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
pr = pd.read_csv(os.path.join(D,"Price_AV_Itapema.csv"), low_memory=False)
det = pd.read_csv(os.path.join(D,"Details_Itapema.csv"), low_memory=False)
pr["date"]=pd.to_datetime(pr["date"]); pr["aq"]=pd.to_datetime(pr["aquisition_date"]).dt.normalize()

print("### A. Estrutura por captura (aquisition_date normalizado por dia)")
print("dias de captura distintos:", pr.aq.nunique())
print(pr.groupby(pr.aq.dt.date).agg(listings=("airbnb_listing_id","nunique"),
      linhas=("price","size"), dt_min=("date","min"), dt_max=("date","max")).to_string())

print("\n### B. Dentro de UMA captura: as datas sao contiguas ou tem buracos?")
for aq in sorted(pr.aq.unique())[:3]:
    sub = pr[pr.aq==aq]
    lo, hi = sub.date.min(), sub.date.max()
    span = (hi-lo).days+1
    cov = sub.groupby("airbnb_listing_id").date.nunique()
    print(f"\ncaptura {pd.Timestamp(aq).date()}  janela {lo.date()}..{hi.date()} ({span} dias)  listings={len(cov)}")
    print("  datas cobertas por listing (describe):", cov.describe()[["mean","50%","min","max"]].round(1).to_dict())
    print("  %listings com cobertura completa:", round(100*(cov==span).mean(),1))
    print("  distribuicao cobertura/span:", np.round(np.percentile(cov/span,[10,25,50,75,90]),2).tolist())

print("\n### C. Exemplo concreto de buraco (listing com cobertura parcial)")
aq0 = sorted(pr.aq.unique())[0]
sub = pr[pr.aq==aq0]
lo,hi = sub.date.min(), sub.date.max(); span=(hi-lo).days+1
cov = sub.groupby("airbnb_listing_id").date.nunique()
alvo = cov[(cov>span*0.4)&(cov<span*0.8)]
if len(alvo):
    lid = alvo.index[0]
    d = set(sub[sub.airbnb_listing_id==lid].date.dt.date)
    todas = pd.date_range(lo,hi).date
    falt = [str(x) for x in todas if x not in d]
    print(f"listing {lid}: {len(d)}/{span} datas. Faltando ({len(falt)}):")
    print("  ", falt[:40])
else:
    print("nenhum listing com cobertura parcial nessa faixa")

print("\n### D. Ocupacao implicita ~ vale a pena? % datas faltantes por mes (captura mais ampla)")
aqx = pr.groupby(pr.aq.dt.date).size().idxmax()
sub = pr[pr.aq.dt.date==aqx]
lo,hi = sub.date.min(), sub.date.max()
grade = pd.MultiIndex.from_product([sub.airbnb_listing_id.unique(), pd.date_range(lo,hi)],
                                   names=["airbnb_listing_id","date"]).to_frame(index=False)
m = grade.merge(sub[["airbnb_listing_id","date","price"]], on=["airbnb_listing_id","date"], how="left")
m["ocupado"] = m.price.isna()
print("captura usada:", aqx, "| listings:", sub.airbnb_listing_id.nunique(), "| janela:", lo.date(), hi.date())
print(m.groupby(m.date.dt.to_period("M")).ocupado.mean().round(3).to_string())

print("\n### E. Quem sao os 1005 listings com preco? Sao representativos?")
com = det[det.airbnb_listing_id.isin(pr.airbnb_listing_id)]
sem = det[~det.airbnb_listing_id.isin(pr.airbnb_listing_id)]
cmp = pd.DataFrame({
 "com_preco": [len(com), com.number_of_bedrooms.mean(), com.number_of_reviews.mean(),
               (com.star_rating>0).mean(), com.number_of_guests.mean()],
 "sem_preco": [len(sem), sem.number_of_bedrooms.mean(), sem.number_of_reviews.mean(),
               (sem.star_rating>0).mean(), sem.number_of_guests.mean()]},
 index=["n","quartos_medio","reviews_medio","%com_rating","hospedes_medio"])
print(cmp.round(2).to_string())
print("\nlisting_type:"); print(pd.concat([com.listing_type.value_counts(normalize=True).rename("com"),
      sem.listing_type.value_counts(normalize=True).rename("sem")],axis=1).round(3).to_string())
print("\nquartos:"); print(pd.concat([com.number_of_bedrooms.value_counts(normalize=True).rename("com"),
      sem.number_of_bedrooms.value_counts(normalize=True).rename("sem")],axis=1).sort_index().round(3).to_string())
