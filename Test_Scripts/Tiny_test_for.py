import pandas as pd

Enlace_list=pd.read_csv("WebScraperTest/Scam adviser sample.csv",sep=";",header=0)
empty=[]

for index, row in Enlace_list.iterrows():
    if not pd.isna(row["Enlace"]) and row["Enlace"] != "":
        Enlaces_completed = "https://" + row["Enlace"]
        empty.append(Enlaces_completed)

print(empty)
