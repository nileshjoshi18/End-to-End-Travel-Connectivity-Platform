# logic_test.py
import pandas as pd
from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:postgres@localhost:5432/mumbai_transit')

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_minutes(t) -> int:
    if t is None: return 0
    if hasattr(t, 'hour'):
        return t.hour * 60 + t.minute
    try:
        parts = str(t).split(':')
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0

def fmt(mins: int) -> str:
    return f"{int((mins % 1440) // 60):02d}:{int(mins % 60):02d}"

# ── find_trains ───────────────────────────────────────────────────────────────

def find_trains(start_stop: str, end_stop: str, user_time_str: str) -> list[dict]:
    df_route_stops = pd.read_sql(
        "SELECT route_id, stop_id, sequence_no, travel_time_next FROM route_stops", engine
    )
    df_schedules = pd.read_sql(
        "SELECT schedule_id, route_id, departure_time FROM schedules", engine
    )

    user_mins = get_minutes(user_time_str)
    valid_route_data = []

    for rid, group in df_route_stops.groupby('route_id'):
        stops = group.sort_values('sequence_no').reset_index(drop=True)

        if start_stop in stops['stop_id'].values and end_stop in stops['stop_id'].values:
            idx_start = stops[stops['stop_id'] == start_stop].index[0]
            idx_end   = stops[stops['stop_id'] == end_stop].index[0]

            if idx_start < idx_end:
                offset   = pd.to_numeric(stops.iloc[:idx_start + 1]['travel_time_next']).sum()
                duration = pd.to_numeric(stops.iloc[idx_start + 1: idx_end + 1]['travel_time_next']).sum()
                valid_route_data.append({
                    'route_id':        rid,
                    'offset_to_start': offset,
                    'trip_duration':   duration,
                })

    if not valid_route_data:
        return []

    df_valid_routes = pd.DataFrame(valid_route_data)
    df_final        = pd.merge(df_schedules, df_valid_routes, on='route_id')

    def calc_times(row):
        origin_mins   = get_minutes(row['departure_time'])
        stop_dep_mins = origin_mins + row['offset_to_start']
        arrival_mins  = stop_dep_mins + row['trip_duration']
        return pd.Series([stop_dep_mins, arrival_mins])

    df_final[['stop_dep_mins', 'arrival_mins']] = df_final.apply(calc_times, axis=1)

    # ── Midnight fix ──────────────────────────────────────────────────────────
    # A train whose stop_dep_mins < user_mins might still be valid if it wraps
    # into the next day (e.g. user_time=23:30, train departs at 00:05 next day).
    # Shift such trains forward by 1440 so the >= comparison works correctly.
    df_final['stop_dep_mins_adj'] = df_final['stop_dep_mins'].where(
        df_final['stop_dep_mins'] >= user_mins,
        df_final['stop_dep_mins'] + 1440,
    )

    # Only keep trains that are reachable (adjusted dep >= user_mins)
    df_filtered = df_final[df_final['stop_dep_mins_adj'] >= user_mins].copy()

    if df_filtered.empty:
        return []

    result = df_filtered.sort_values('stop_dep_mins_adj').head(5)

    return [
        {
            "train_id":  str(row['schedule_id']),
            "departure": fmt(row['stop_dep_mins']),      # display as real clock time
            "arrival":   fmt(row['arrival_mins']),
            "duration":  f"{int(row['trip_duration'])} min",
        }
        for _, row in result.iterrows()
    ]

# ── changeover_routes ─────────────────────────────────────────────────────────

def _get_line(stop_id: str) -> str:
    """Extract line code from stop_id, e.g. 'GOR_WR' -> 'WR'."""
    return stop_id.split('_')[-1]

def _stops_for_line(line: str, df_route_stops: pd.DataFrame) -> list[str]:
    """Return all unique stop_ids for a given line."""
    return df_route_stops[
        df_route_stops['stop_id'].str.endswith(f'_{line}')
    ]['stop_id'].unique().tolist()

def changeover_routes(start_stop: str, end_stop: str) -> list[list[dict]]:
    """
    Find all viable sequences of lines connecting start_stop to end_stop,
    including direct (single-line) and multi-line (changeover) paths.

    Returns a list of routes, each route being a list of leg dicts:
        [{'from_stop': ..., 'to_stop': ..., 'line': ...}, ...]
    """
    df_route_stops = pd.read_sql(
        "SELECT DISTINCT route_id, stop_id FROM route_stops", engine
    )

    start_line = _get_line(start_stop)
    end_line   = _get_line(end_stop)

    # ── Direct route (same line) ──────────────────────────────────────────────
    if start_line == end_line:
        return [[{'from_stop': start_stop, 'to_stop': end_stop, 'line': start_line}]]

    # ── Find interchange stops between two lines ──────────────────────────────
    def interchange_stops(line_a: str, line_b: str) -> list[str]:
        """
        Return stop_ids on line_a that have a corresponding stop on line_b
        at the same physical station (same prefix, different suffix).
        e.g. 'DAD_WR' <-> 'DAD_CR'
        """
        stops_a = set(_stops_for_line(line_a, df_route_stops))
        stops_b = set(_stops_for_line(line_b, df_route_stops))
        prefixes_b = {s.rsplit('_', 1)[0] for s in stops_b}
        return [s for s in stops_a if s.rsplit('_', 1)[0] in prefixes_b]

    # ── Single changeover ─────────────────────────────────────────────────────
    routes = []
    direct_interchanges = interchange_stops(start_line, end_line)

    for ix_stop in direct_interchanges:
        prefix  = ix_stop.rsplit('_', 1)[0]
        ix_dest = f"{prefix}_{end_line}"
        routes.append([
            {'from_stop': start_stop, 'to_stop': ix_stop,   'line': start_line},
            {'from_stop': ix_dest,    'to_stop': end_stop,   'line': end_line},
        ])

    if routes:
        return routes

    # ── Two changeovers (via intermediate line) ────────────────────────────────
    # Find all lines that connect start_line -> mid_line -> end_line
    all_lines = df_route_stops['stop_id'].str.split('_').str[-1].unique().tolist()

    for mid_line in all_lines:
        if mid_line in (start_line, end_line):
            continue

        ix_start_mid = interchange_stops(start_line, mid_line)
        ix_mid_end   = interchange_stops(mid_line,   end_line)

        if not ix_start_mid or not ix_mid_end:
            continue

        for ix1 in ix_start_mid:
            prefix1 = ix1.rsplit('_', 1)[0]
            ix1_mid = f"{prefix1}_{mid_line}"

            for ix2 in ix_mid_end:
                prefix2 = ix2.rsplit('_', 1)[0]
                ix2_end = f"{prefix2}_{end_line}"
                routes.append([
                    {'from_stop': start_stop, 'to_stop': ix1,     'line': start_line},
                    {'from_stop': ix1_mid,    'to_stop': ix2,     'line': mid_line},
                    {'from_stop': ix2_end,    'to_stop': end_stop, 'line': end_line},
                ])

    return routes


# ── Smoke test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    trains = find_trains('PAN_HR', 'CST_HR', '10:00')
    print(trains)
    print()
    print(changeover_routes('GOR_THR', 'PAN_HR'))