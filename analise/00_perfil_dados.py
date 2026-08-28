# -*- coding: utf-8 -*-
"""Perfilamento inicial dos 5 CSVs. Nao assume nada: le, mede, reporta."""
import pandas as pd, os, sys

pd.set_option("display.width", 200)
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

FILES = ["Details_Itapema.csv","Hosts_ids_Itapema.csv","Mesh_Ids_Data_Itapema.csv",
         "Price_AV_Itapema.csv","VivaReal_Itapema.csv"]

def perfil(nome):
    df = pd.read_csv(os.path.join(DATA, nome), low_memory=False)
    print("="*90)
    print(f"ARQUIVO: {nome}   linhas={len(df):,}  colunas={df.shape[1]}")
    print("="*90)
    rows = []
    for c in df.columns:
        s = df[c]
        nn = s.notna().sum()
        nulos = len(s) - nn
        ex = s.dropna().iloc[0] if nn else ""
        ex = str(ex)[:45].replace("\n"," ")
        rows.append({
            "coluna": c, "dtype": str(s.dtype),
            "nulos": nulos, "%nulo": round(100*nulos/len(s),1),
            "distintos": s.nunique(dropna=True), "exemplo": ex,
        })
    print(pd.DataFrame(rows).to_string(index=False))
    print()
    return df

dfs = {f: perfil(f) for f in FILES}
