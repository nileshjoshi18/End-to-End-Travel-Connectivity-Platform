import pandas as pd
import re
from datetime import datetime

# --- Load Data ---
df_main = pd.read_excel('westernline_fromccg_dn_alltables_merged - Copy.xlsx', header=[0, 1])
df_routes = pd.read_excel('route_table_1.xlsx') 
df_stops = pd.read_excel('stops_table.xlsx')

# Clean stop names
df_stops.columns = df_stops.columns.str.strip()
stop_map = dict(zip(df_stops['name'].str.strip().str.upper(), df_stops['stop_id']))

# Flatten columns
df_main.columns = [f'{str(a).strip()}_{str(b).strip()}' if 'Unnamed' not in str(b) else str(a).strip() for a, b in df_main.columns]
stations = df_main[df_main.columns[0]].str.strip().str.upper().tolist()

# Build lookup from the Route Table
route_lookup = {}
for _, row in df_routes.iterrows():
    suffix = row['route_id'][-2:]
    route_lookup[(str(row['pattern_key']), suffix)] = row['route_id']

def get_minutes_diff(curr_str, prev_str):
    try:
        fmt = '%H:%M'
        t1 = datetime.strptime(prev_str.strip(), fmt)
        t2 = datetime.strptime(curr_str.strip(), fmt)
        diff = (t2 - t1).total_seconds() / 60
        return int(diff if diff >= 0 else diff + 1440)
    except: return 0

all_stop_rows = []
processed_route_ids = set() 
train_cols = [c for c in df_main.columns if c != df_main.columns[0]]

for col in train_cols:
    pattern_list = [1 if bool(re.match(r'^\d{1,2}:\d{2}$', str(val).strip())) else 0 for val in df_main[col]]
    if sum(pattern_list) < 2: continue
    
    name = str(col).upper()
    is_ac = ('_AC' in name or 'AIR CONDITION' in name or name.split('_')[-1].endswith('A'))
    idx_list = [i for i, v in enumerate(pattern_list) if v == 1]
    is_fast = 0 in pattern_list[idx_list[0]:idx_list[-1]+1]
    suffix = 'AC' if is_ac else ('FT' if is_fast else 'OR')

    r_id = route_lookup.get((str(tuple(pattern_list)), suffix))

    if r_id and r_id not in processed_route_ids:
        seq = 1
        last_stop_time = None
        
        for idx, is_stopped in enumerate(pattern_list):
            if is_stopped:
                curr_time_str = str(df_main[col].iloc[idx]).strip()
                s_id = stop_map.get(stations[idx])
                
                time_from_prev = 0
                if last_stop_time is not None:
                    time_from_prev = get_minutes_diff(curr_time_str, last_stop_time)
                
                # --- NEW: Generate Unique route_stop_id ---
                # Format: WRTR0010OR_S01, WRTR0010OR_S02, etc.
                rs_id = f"{r_id}_S{str(seq).zfill(2)}"
                
                all_stop_rows.append({
                    'route_stop_id': rs_id,
                    'route_id': r_id,
                    'stop_id': s_id,
                    'sequence_no': seq,
                    'travel_time_next': time_from_prev 
                })
                
                last_stop_time = curr_time_str
                seq += 1
        
        processed_route_ids.add(r_id)

# Save result
output_df = pd.DataFrame(all_stop_rows)
output_df.to_excel('route_stops.xlsx', index=False)

print(f"✅ Success! Generated {len(output_df)} rows with unique route_stop_ids.")
print(output_df[['route_stop_id', 'route_id', 'sequence_no']].head())