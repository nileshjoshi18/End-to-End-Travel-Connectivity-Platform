import pandas as pd
import re

# Load all
df_main = pd.read_excel('westernline_fromvir_up_merged.xlsx', header=[0, 1])
df_routes = pd.read_excel('route_table_1.xlsx')
df_stops = pd.read_excel('stops_table.xlsx')

# Clean stops (Use the MX_WR fix if you applied it)
df_stops.columns = df_stops.columns.str.strip()
stop_map = dict(zip(df_stops['name'].str.strip().str.upper(), df_stops['stop_id']))

# Flatten
df_main.columns = [f'{str(a).strip()}_{str(b).strip()}' if 'Unnamed' not in str(b) else str(a).strip() for a, b in df_main.columns]
stations = df_main[df_main.columns[0]].str.strip().str.upper().tolist()

# BUILD LOOKUP FROM THE ACTUAL ROUTE TABLE
route_lookup = {}
for _, row in df_routes.iterrows():
    # Store by (pattern_string, suffix)
    suffix = row['route_id'][-2:]
    route_lookup[(row['pattern_key'], suffix)] = row['route_id']

schedule_rows = []
train_cols = [c for c in df_main.columns if c != df_main.columns[0]]

for col in train_cols:
    # Use the EXACT same logic as script 1
    pattern = tuple([1 if bool(re.match(r'^\d{2}:\d{2}$', str(val).strip())) else 0 for val in df_main[col]])
    if sum(pattern) < 2: continue
    
    name = str(col).upper()
    is_ac = ('_AC' in name or 'AIR CONDITION' in name or 
             df_main[col].astype(str).str.contains(r'\bAC\b|AIR CONDITION', case=False, na=False, regex=True).any() or
             name.split('_')[-1].endswith('A'))
    
    indices = [i for i, v in enumerate(pattern) if v == 1]
    is_fast = 0 in pattern[indices[0]:indices[-1]+1]
    suffix = 'AC' if is_ac else ('FT' if is_fast else 'OR')
    
    # MATCH
    r_id = route_lookup.get((str(pattern), suffix))
    
    if r_id:
        train_no = col.split('_')[-1]
        start_idx = pattern.index(1)
        
        schedule_rows.append({
            'schedule_id': f"WRSCH_{train_no}",
            'route_id': r_id,
            'stop_id': stop_map.get(stations[start_idx]),
            'departure_time': str(df_main[col].iloc[start_idx]).strip(),
            'days_of_week': 7 # Modify if you have Sunday logic
        })

pd.DataFrame(schedule_rows).to_excel('schedule_table_1.xlsx', index=False)
print(f"Generated {len(schedule_rows)} schedules.")