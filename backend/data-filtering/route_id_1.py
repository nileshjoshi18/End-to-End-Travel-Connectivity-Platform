#newest version
import pandas as pd
import re

# Read MORE header rows to capture multi-row headers like "Air\nCondition"
df_raw = pd.read_excel('westernline_fromvir_up_merged.xlsx', header=None)

# ✅ Find where the actual time data starts by detecting first HH:MM pattern
def find_header_rows(df_raw):
    for i, row in df_raw.iterrows():
        if any(bool(re.match(r'^\d{1,2}:\d{2}$', str(v).strip())) for v in row):
            return i  # First row with time data
    return 3  # fallback

data_start_row = find_header_rows(df_raw)
header_rows = df_raw.iloc[:data_start_row]  # All rows above data are headers

# ✅ Flatten ALL header rows into one string per column
def flatten_col_header(col_idx):
    parts = []
    for _, row in header_rows.iterrows():
        val = str(row.iloc[col_idx]).strip()
        if val and val.lower() != 'nan':
            parts.append(val)
    return ' '.join(parts)

col_headers = [flatten_col_header(i) for i in range(df_raw.shape[1])]

# Now load only the data rows
df = df_raw.iloc[data_start_row:].reset_index(drop=True)
df.columns = col_headers

station_col = df.columns[0]
train_cols = [c for c in df.columns if c != station_col]
stations = df[station_col].astype(str).str.strip().tolist()


def get_logic_data(col_data, col_name):
    # 1. Time pattern detection
    pattern = tuple([
        1 if bool(re.match(r'^\d{1,2}:\d{2}$', str(val).strip())) else 0
        for val in col_data
    ])

    # 2. ✅ AC Detection — check BOTH column name AND cell values in the column
    name_upper = str(col_name).upper()
    
    ac_in_name = any(kw in name_upper for kw in [
        'AC', 'AIR', 'CONDITION', 'A/C'
    ])
    
    # Also scan non-time cells for AC keywords (catches split headers stored as data)
    ac_in_cells = any(
        any(kw in str(val).upper() for kw in ['AIR', 'CONDITION', 'A/C', ' AC', 'AC '])
        for val in col_data
        if not bool(re.match(r'^\d{1,2}:\d{2}$', str(val).strip()))
        and str(val).strip().lower() not in ['nan', '', '-']
    )
    
    is_ac = ac_in_name or ac_in_cells

    # 3. Fast train detection (gap in stops = skips stations)
    indices = [i for i, v in enumerate(pattern) if v == 1]
    is_fast = False
    if len(indices) >= 2:
        is_fast = 0 in pattern[indices[0]:indices[-1] + 1]

    suffix = 'AC' if is_ac else ('FT' if is_fast else 'OR')
    return pattern, suffix


route_map = {}
route_counter = 91
unique_routes = []

for col in train_cols:
    pattern, suffix = get_logic_data(df[col], col)
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

pd.DataFrame(unique_routes).to_excel('route_table_1.xlsx', index=False)
print(f"✅ Created {len(unique_routes)} unique routes in route_table_1.xlsx")