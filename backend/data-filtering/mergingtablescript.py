import pandas as pd

# Load all sheets
file = "THB_UP_western_format.xlsx"
xls = pd.ExcelFile(file)

dfs = []

for sheet in xls.sheet_names:
    df = pd.read_excel(file, sheet_name=sheet)
    dfs.append(df)  

# Merge all tables
merged_df = pd.concat(dfs, ignore_index=True)

# Save output
merged_df.to_excel("thane_line_ulti.xlsx", index=False)