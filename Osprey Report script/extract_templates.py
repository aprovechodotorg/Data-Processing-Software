import pandas as pd
xls = pd.ExcelFile('table templates.xlsx')

print("=== VAR NAMES ===")
df_vars = pd.read_excel(xls, sheet_name='var names')
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
print(df_vars.head(100))

print("\n=== Multi-Test Series Avg ===")
df_avg = pd.read_excel(xls, sheet_name='Multi-Test Series Avg')
print(df_avg.head(100))

print("\n=== Multi-Test All Tests ===")
df_all = pd.read_excel(xls, sheet_name='Multi-Test All Tests')
print(df_all.head(100))
