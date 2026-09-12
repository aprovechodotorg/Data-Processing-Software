import pandas as pd
df = pd.read_excel('table templates.xlsx', sheet_name='ISO Tiers')
with open('iso_tiers_dump.txt', 'w', encoding='utf-8') as f:
    f.write(df.to_string())
