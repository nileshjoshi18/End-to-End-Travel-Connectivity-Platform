import pandas as pd

# Load all sheets
file = "centralline_fromkasara_up_western_format (1).xlsx"
xls = pd.ExcelFile(file)

dfs = []

for sheet in xls.sheet_names:
    df = pd.read_excel(file, sheet_name=sheet)
    dfs.append(df)  

# Merge all tables
merged_df = pd.concat(dfs, ignore_index=True)

# Save output
merged_df.to_excel("centralline_fromkasara_up.xlsx", index=False)