import pandas as pd
import requests
import duckdb
import io
test_str = """transfer_type,product_kind,transaction_type_desc
Normal,TAM,Tam Abonman
Normal,TAM,Tam Kontur
Normal,,Tam Kontur
Aktarma,INDIRIMLI2,Indirimli Tip 2 Aktarma
Normal,UCRETSIZ,Ucretsiz
Aktarma,,Indirimli Aktarma
Normal,INDIRIMLI1,Tam Kontur
Aktarma,UCRETSIZ,Tam Aktarma
Normal,INDIRIMLI1,Indirimli Abonman
Normal,UCRETSIZ,Tam Kontur
Normal,,Indirimli Kontur
Aktarma,INDIRIMLI1,Indirimli Aktarma
Normal,INDIRIMLI2,Indirimli Tip 2 Kontur
Normal,INDIRIMLI1,Indirimli Kontur
Aktarma,,Indirimli Tip 2 Aktarma
Normal,INDIRIMLI2,Indirimli Tip 2 Abonman
Normal,PERSONEL,Tam Kontur
Normal,,Ucretsiz
Aktarma,TAM,Tam Aktarma
Aktarma,,Tam Aktarma
Aktarma,INDIRIMLI2,Tam Aktarma
Normal,,Indirimli Tip 2 Kontur
Normal,INDIRIMLI2,Tam Kontur
Aktarma,INDIRIMLI1,Tam Aktarma
Normal,PERSONEL,Tam Abonman
Normal,TAM,TekliBilet Tarifeli
Aktarma,PERSONEL,Tam Aktarma
Normal,TAM,Marmaray Bilet
Normal,PERSONEL,Ucretsiz
Normal,TAM,Ucretsiz
Normal,UCRETSIZ,Indirimli Tip 2 Kontur
Normal,GIRIS_CIKIS,Tam Kontur
Normal,DENETIM,Ucretsiz
Normal,DENETIM,Tam Kontur
Normal,TAM,Indirimli Kontur
Normal,KULLANILMAYAN_GRUBU,Tam Kontur
Aktarma,TAM,Indirimli Aktarma
Aktarma,KULLANILMAYAN_GRUBU,Tam Aktarma
Aktarma,DENETIM,Tam Aktarma
Aktarma,TAM,Indirimli Tip 2 Aktarma
Normal,TAM,Indirimli Tip 2 Kontur
Aktarma,INDIRIMLI1,Indirimli Tip 2 Aktarma
Normal,INDIRIMLI1,Indirimli Tip 2 Kontur
Normal,INDIRIMLI2,Indirimli Kontur
Aktarma,GIRIS_CIKIS,Tam Aktarma
Normal,INDIRIMLI2,Ucretsiz
Aktarma,UCRETSIZ,Indirimli Tip 2 Aktarma
Normal,GIRIS_CIKIS,Ucretsiz
Normal,,TekliBilet Tarifeli
Aktarma,INDIRIMLI2,Indirimli Aktarma
"""

csv_stream = io.StringIO(test_str)
pseudofile = duckdb.read_csv(csv_stream)
#df = pd.read_excel("New Microsoft Excel Worksheet.xlsx")
print(duckdb.sql("SELECT * from pseudofile"))
#df_selection = df[(df["Year"] == 2024) & (df["Month"] == "December")]

#for url in df_selection["CSV_URL"]:
    #break
    #response = requests.get(url)

    #print(response.json)
# for url in df["FileURL"]:
#     filename = url.split("/")[-1]
#     response = requests.get(url)
#     with open(filename, "wb") as f:
#         f.write(response.content)