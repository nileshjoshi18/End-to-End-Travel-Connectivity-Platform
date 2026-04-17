import pandas as pd
import re

df = pd.read_excel('westernline_fromvir_up_merged.xlsx', header=[0, 1])

# Unified Flattening
df.columns = [f'{str(a).strip()}_{str(b).strip()}' if 'Unnamed' not in str(b) else str(a).strip() for a, b in df.columns]
station_col = df.columns[0]
train_cols = [c for c in df.columns if c != station_col]
stations = df[station_col].astype(str).str.strip().tolist()

def get_logic_data(col_data, col_name):
    # 1. Pattern (Matches HH:MM)
    pattern = tuple([1 if bool(re.match(r'^\d{1,2}:\d{2}$', str(val).strip())) else 0 for val in col_data])
    
    # 2. AC Detection
    name = str(col_name).upper()
    is_ac = ('_AC' in name or 'AIR CONDITION' in name or name.split('_')[-1].endswith('A'))
    
    # 3. Fast Detection
    indices = [i for i, v in enumerate(pattern) if v == 1]
    is_fast = False
    if len(indices) >= 2:
        is_fast = 0 in pattern[indices[0]:indices[-1]+1]
    
    suffix = 'AC' if is_ac else ('FT' if is_fast else 'OR')
    return pattern, suffix

route_map = {}
route_counter = 91
unique_routes = []

for col in train_cols:
    pattern, suffix = get_logic_data(df[col], col)
    if sum(pattern) < 2: continue 
    
    key = (str(pattern), suffix) # Use string of pattern for reliable dictionary matching
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

pd.DataFrame(unique_routes).to_excel('route_table_1.xlsx', index=False)
print(f"✅ Created {len(unique_routes)} unique routes in route_table_1.xlsx")