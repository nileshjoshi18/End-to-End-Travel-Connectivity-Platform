#use this, handles both routes and route stops
import pandas as pd
import re
from datetime import datetime

# ============================================================
# STEP 1: Load & Flatten
# ============================================================
df_main = pd.read_excel('westernline_fromvir_up_merged.xlsx', header=[0, 1])
df_stops = pd.read_excel('stops_table.xlsx')

df_stops.columns = df_stops.columns.str.strip()
stop_map = dict(zip(df_stops['name'].str.strip().str.upper(), df_stops['stop_id']))

df_main.columns = [
    f'{str(a).strip()}_{str(b).strip()}' if 'Unnamed' not in str(b) else str(a).strip()
    for a, b in df_main.columns
]

station_col = df_main.columns[0]
train_cols = [c for c in df_main.columns if c != station_col]

# ============================================================
# STEP 2: Drop rows where station name is blank/nan
# (This was silently happening in route_table_1.py but not here)
# ============================================================
df_main = df_main[df_main[station_col].astype(str).str.strip().str.lower() != 'nan']
df_main = df_main[df_main[station_col].astype(str).str.strip() != '']
df_main = df_main.reset_index(drop=True)

stations = df_main[station_col].astype(str).str.strip().str.upper().tolist()

print(f"✅ Station count after cleaning: {len(stations)}")
print(f"   First: {stations[0]} | Last: {stations[-1]}")

# ============================================================
# STEP 3: Shared pattern builder (single source of truth)
# ============================================================
def build_pattern(col_data, col_name):
    pattern = tuple([
        1 if bool(re.match(r'^\d{1,2}:\d{2}$', str(val).strip())) else 0
        for val in col_data
    ])

    name = str(col_name).upper()
    is_ac = ('_AC' in name or 'AIR CONDITION' in name or 
             name.split('_')[-1].endswith('A') or 'AIR' in name or 'AC' in name)

    indices = [i for i, v in enumerate(pattern) if v == 1]
    is_fast = False
    if len(indices) >= 2:
        is_fast = 0 in pattern[indices[0]:indices[-1] + 1]

    suffix = 'AC' if is_ac else ('FT' if is_fast else 'OR')
    return pattern, suffix

# ============================================================
# STEP 4: Build Route Table
# ============================================================
route_map = {}       # (pattern_str, suffix) -> route_id
route_counter = 91
unique_routes = []

for col in train_cols:
    pattern, suffix = build_pattern(df_main[col], col)
    if sum(pattern) < 2:
        continue

    key = (str(pattern), suffix)
    if key not in route_map:
        route_id = f'WRTR{str(route_counter).zfill(4)}{suffix}'
        route_map[key] = route_id
        route_counter += 1

        idx = [i for i, v in enumerate(pattern) if v == 1]
        r_name = f"{stations[idx[0]][:3].upper()}_{stations[idx[-1]][:3].upper()}"

        unique_routes.append({
            'route_id': route_id,
            'name': r_name,
            'mode': 'LOCALTR',
            'is_active': True,
            'pattern_key': str(pattern)
        })

routes_df = pd.DataFrame(unique_routes)
routes_df.to_excel('route_table_1.xlsx', index=False)
print(f"✅ Route table: {len(routes_df)} unique routes → route_table_1.xlsx")

# ============================================================
# STEP 5: Build Route Stops Table
# ============================================================
def get_minutes_diff(curr_str, prev_str):
    try:
        fmt = '%H:%M'
        t1 = datetime.strptime(prev_str.strip(), fmt)
        t2 = datetime.strptime(curr_str.strip(), fmt)
        diff = (t2 - t1).total_seconds() / 60
        return int(diff if diff >= 0 else diff + 1440)
    except:
        return 0

all_stop_rows = []
processed_route_ids = set()
missing_stops = set()

for col in train_cols:
    pattern, suffix = build_pattern(df_main[col], col)
    if sum(pattern) < 2:
        continue

    key = (str(pattern), suffix)
    r_id = route_map.get(key)

    if r_id is None or r_id in processed_route_ids:
        continue

    seq = 1
    last_stop_time = None

    for idx, is_stopped in enumerate(pattern):
        if is_stopped:
            curr_time_str = str(df_main[col].iloc[idx]).strip()
            station_name = stations[idx]
            s_id = stop_map.get(station_name)

            if s_id is None:
                missing_stops.add(station_name)

            time_from_prev = 0
            if last_stop_time is not None:
                time_from_prev = get_minutes_diff(curr_time_str, last_stop_time)

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

output_df = pd.DataFrame(all_stop_rows)
output_df.to_excel('route_stops_1.xlsx', index=False)

print(f"✅ Route stops: {len(output_df)} rows → route_stops_1.xlsx")
print(output_df[['route_stop_id', 'route_id', 'sequence_no']].head(10))

if missing_stops:
    print(f"\n⚠️  {len(missing_stops)} station(s) not found in stops_table.xlsx:")
    for s in sorted(missing_stops):
        print(f"   - {s}")