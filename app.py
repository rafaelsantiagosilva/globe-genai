import pandas as pd

DATA_PATH = "./data"

df = pd.read_excel(DATA_PATH + "/institutions-and-researchers.xlsx")
print(df.head())