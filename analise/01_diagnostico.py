# -*- coding: utf-8 -*-
import pandas as pd, os
pd.set_option("display.width", 220)
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
r = lambda f: pd.read_csv(os.path.join(D,f), low_memory=False)

det = r("Details_Itapema.csv"); hos = r("Hosts_ids_Itapema.csv")
mesh = r("Mesh_Ids_Data_Itapema.csv"); pr = r("Price_AV_Itapema.csv"); vr = r("VivaReal_Itapema.csv")

print("### 1. PRICE_AV — cobertura e granularidade")
pr["date"]=pd.to_datetime(pr["date"]); pr["aq"]=pd.to_datetime(pr["aquisition_date"])
print("listings com preco:", pr.airbnb_listing_id.nunique(), "de", det.airbnb_listing_id.nunique(),
      f"({100*pr.airbnb_listing_id.nunique()/det.airbnb_listing_id.nunique():.1f}%)")
print("range date estadia:", pr.date.min().date(), "->", pr.date.max().date())
print("range aquisition   :", pr.aq.min().date(), "->", pr.aq.max().date())
print("n datas distintas:", pr.date.nunique(), "| n dias no range:", (pr.date.max()-pr.date.min()).days+1)
print("duplicatas (listing,date):", pr.duplicated(["airbnb_listing_id","date"]).sum())
print("duplicatas (listing,date,aq):", pr.duplicated(["airbnb_listing_id","date","aquisition_date"]).sum())
print("\ncapturas por (listing,date) - distribuicao:")
print(pr.groupby(["airbnb_listing_id","date"]).size().value_counts().head(10).to_string())
print("\nlinhas por listing - describe:")
print(pr.groupby("airbnb_listing_id").size().describe().to_string())
print("\nprice describe:"); print(pr.price.describe().to_string())
print("price<=0:", (pr.price<=0).sum(), "| price>20000:", (pr.price>20000).sum())
print("\ndatas presentes (amostra ordenada):")
d=sorted(pr.date.dt.date.unique()); print(d[:8], "...", d[-8:])
print("\nlinhas por data de estadia (top/bottom):")
g=pr.groupby(pr.date.dt.date).size(); print(g.head(5).to_string()); print("..."); print(g.tail(5).to_string())

print("\n### 2. Um listing exemplo (multiplas capturas)")
lid = pr.airbnb_listing_id.value_counts().index[0]
print("listing", lid, "n linhas:", (pr.airbnb_listing_id==lid).sum())
print(pr[pr.airbnb_listing_id==lid].sort_values(["date","aq"]).head(15).to_string(index=False))

print("\n### 3. DETAILS — colunas degeneradas / suspeitas")
for c in ["latitude","longitude","min_nights","guest_satisfaction_overall","star_rating","number_of_reviews","listing_type","number_of_bedrooms"]:
    print(f"-- {c}: {det[c].value_counts(dropna=False).head(8).to_dict()}")
print("star_rating==0:", (det.star_rating==0).sum(), "| number_of_reviews==0:", (det.number_of_reviews==0).sum())
print("duplicatas listing_id:", det.airbnb_listing_id.duplicated().sum())

print("\n### 4. MESH — bairros")
print(mesh.suburb.value_counts(dropna=False).to_string())
print("lat/long zerados:", ((mesh.latitude==0)|(mesh.longitude==0)).sum())

print("\n### 5. HOSTS — duplicatas")
print("linhas:", len(hos), "owner_id distintos:", hos.owner_id.nunique())
print("dup completas:", hos.duplicated().sum())
print("owner_id com >1 linha divergente:", hos.drop_duplicates().owner_id.duplicated().sum())
print("owners em details sem match em hosts:", (~det.owner_id.isin(hos.owner_id)).sum())

print("\n### 6. VIVAREAL")
print("dup listing_id:", vr.listing_id.duplicated().sum(), "| dup link_url:", vr.link_url.duplicated().sum())
print("business_types:", vr.business_types.value_counts().to_dict())
print("listing_type:", vr.listing_type.value_counts().to_dict())
print("sale_price describe:"); print(vr.sale_price.describe().to_string())
print("sale_price<=1000:", (vr.sale_price<=1000).sum(), "| ==0:", (vr.sale_price==0).sum())
print("usable_area describe:"); print(vr.usable_area.describe().to_string())
print("usable_area<=0:", (vr.usable_area<=0).sum())
print("bedrooms:", vr.bedrooms.value_counts().sort_index().to_dict())
print("condo_fee==0:", (vr.monthly_condo_fee==0).sum())
print("\nsuburb VivaReal:"); print(vr.suburb.value_counts(dropna=False).to_string())
