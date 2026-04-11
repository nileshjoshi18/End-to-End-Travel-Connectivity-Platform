# logic_test.py
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:postgres@localhost:5432/mumbai_transit')

def get_minutes(t):
    if t is None: return 0
    if hasattr(t, 'hour'):
        return t.hour * 60 + t.minute
    try:
        parts = str(t).split(':')
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0

def find_trains(start_stop: str, end_stop: str, user_time_str: str) -> list[dict]:
    """
    Returns the next 5 trains from start_stop to end_stop after user_time_str (HH:MM).
    Returns an empty list if none found.
    """
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
                    'route_id': rid,
                    'offset_to_start': offset,
                    'trip_duration': duration
                })

    if not valid_route_data:
        return []

    df_valid_routes = pd.DataFrame(valid_route_data)
    df_final = pd.merge(df_schedules, df_valid_routes, on='route_id')

    def calc_times(row):
        origin_mins    = get_minutes(row['departure_time'])
        stop_dep_mins  = origin_mins + row['offset_to_start']
        arrival_mins   = stop_dep_mins + row['trip_duration']
        return pd.Series([stop_dep_mins, arrival_mins])

    df_final[['stop_dep_mins', 'arrival_mins']] = df_final.apply(calc_times, axis=1)
    df_filtered = df_final[df_final['stop_dep_mins'] >= user_mins].copy()

    if df_filtered.empty:
        return []

    def fmt(mins):
        return f"{int((mins % 1440) // 60):02d}:{int(mins % 60):02d}"

    result = df_filtered.sort_values('stop_dep_mins').head(5)

    return [
        {
            "train_id":  str(row['schedule_id']),
            "departure": fmt(row['stop_dep_mins']),
            "arrival":   fmt(row['arrival_mins']),
            "duration":  f"{int(row['trip_duration'])} min",
        }
        for _, row in result.iterrows()
    ]


if __name__ == "__main__":
    trains = find_trains('CHU_WR', 'GOR_WR', '08:00')
    for t in trains:
        print(t)