# -*- coding: utf-8 -*-
"""Viabilidade do sinal de PICKUP: comparar captura 06/01 vs 20/01 para as mesmas datas de estadia.
Se a data estava disponivel em 06/01 e sumiu em 20/01 -> foi reservada (ou bloqueada) nesses 14 dias."""
import pandas as pd, numpy as np, os
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
pr = pd.read_csv(os.path.join(D,"Price_AV_Itapema.csv"), low_memory=False)
pr["date"]=pd.to_datetime(pr["date"]); pr["aq"]=pd.to_datetime(pr["aquisition_date"]).dt.normalize()

A = pr[pr.aq=="2025-01-06"]; B = pr[pr.aq=="2025-01-20"]
listings = sorted(set(A.airbnb_listing_id) & set(B.airbnb_listing_id))
print("listings nas duas capturas:", len(listings))
lo, hi = pd.Timestamp("2025-01-20"), pd.Timestamp("2025-04-06")   # janela comum
dias = pd.date_range(lo,hi); print("janela comum:", lo.date(), hi.date(), f"({len(dias)} dias)")

grade = pd.MultiIndex.from_product([listings,dias],names=["airbnb_listing_id","date"]).to_frame(index=False)
grade = grade.merge(A[["airbnb_listing_id","date","price"]].rename(columns={"price":"p_A"}),how="left")
grade = grade.merge(B[["airbnb_listing_id","date","price"]].rename(columns={"price":"p_B"}),how="left")
grade["disp_A"]=grade.p_A.notna(); grade["disp_B"]=grade.p_B.notna()

n=len(grade)
print("\nMatriz de transicao (06/01 -> 20/01), %% das", f"{n:,}", "celulas listing-data:")
tab = pd.crosstab(grade.disp_A, grade.disp_B, normalize=True).round(3)
tab.index=["indisp_A","disp_A"]; tab.columns=["indisp_B","disp_B"]; print(tab.to_string())

vend = grade[grade.disp_A & ~grade.disp_B]
print(f"\nRESERVADO no periodo (disp->indisp): {len(vend):,} noites-listing "
      f"({100*len(vend)/grade.disp_A.sum():.1f}% das noites que estavam disponiveis)")
print("liberado (indisp->disp, cancelamento/abertura):",
      f"{int((~grade.disp_A & grade.disp_B).sum()):,}")

print("\nTaxa de pickup por mes da estadia:")
g = grade[grade.disp_A].groupby(grade.date.dt.to_period("M")).apply(
    lambda d: pd.Series({"noites_disp_06/01":len(d), "reservadas":int((~d.disp_B).sum()),
                         "pickup_%":round(100*(~d.disp_B).mean(),1)}))
print(g.to_string())

print("\nPickup por listing (proxy de demanda) - describe:")
pk = grade[grade.disp_A].groupby("airbnb_listing_id").disp_B.apply(lambda s:(~s).mean())
print(pk.describe().round(3).to_string())
print("listings com >=20 noites disponiveis em A:", int((grade[grade.disp_A].groupby('airbnb_listing_id').size()>=20).sum()))

print("\nPreco medio: noites reservadas vs nao reservadas (ADR realizado vs ofertado)")
print("reservadas  :", round(grade.loc[grade.disp_A & ~grade.disp_B,"p_A"].mean(),2))
print("nao reservadas:", round(grade.loc[grade.disp_A & grade.disp_B,"p_A"].mean(),2))
