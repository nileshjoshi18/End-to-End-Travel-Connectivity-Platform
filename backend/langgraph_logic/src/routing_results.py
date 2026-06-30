"""
routing_results.py  —  pure module, no FastAPI

Single entry point: get_routes(start_stop, end_stop, user_time)

Merges the old get_connectivity (same-line / single-leg) logic and the old
resultant-routes (multi-leg / interchange) logic into ONE function. Internally:
  - if start and end are on the same line  → single-leg path (was get_connectivity)
  - if they differ                          → multi-leg path (was resultant-routes)

Also fetches crowd scores for source, destination, and any interchange stations
directly here — so the agent never needs DB access (no run_sql tool needed).
"""

import asyncio
import pandas as pd
from sqlalchemy import create_engine, text

from system_brain import changeover_routes, determine_line
from logic_test import get_minutes, fmt
from train_details import get_train_details
from nearest_station import get_nearest_station

engine = create_engine('postgresql://postgres:postgres@localhost:5432/mumbai_transit')


# ──────────────────────────── helpers ──────────────────────────────────

def time_to_minutes(t: str, day_offset: int = 0) -> int:
    h, m = map(int, str(t).split(':')[:2])
    return day_offset * 1440 + h * 60 + m


def minutes_to_time(mins: int) -> str:
    mins = int(mins) % 1440
    return f"{mins // 60:02d}:{mins % 60:02d}"


# ──────────────────── in-memory train finder ───────────────────────────

def find_trains_fast(
    start_stop: str,
    end_stop: str,
    user_time_str: str,
    df_route_stops: pd.DataFrame,
    df_schedules: pd.DataFrame,
    limit: int = 5,
) -> list[dict]:
    """
    Finds trains between two stops on the SAME line using pre-loaded DataFrames.
    No DB calls — caller loads df_route_stops/df_schedules once and reuses.
    """
    user_mins = get_minutes(user_time_str)
    valid_route_data = []

    for rid, group in df_route_stops.groupby('route_id'):
        stops = group.sort_values('sequence_no').reset_index(drop=True)

        if start_stop not in stops['stop_id'].values:
            continue
        if end_stop not in stops['stop_id'].values:
            continue

        idx_start = stops[stops['stop_id'] == start_stop].index[0]
        idx_end   = stops[stops['stop_id'] == end_stop].index[0]

        if idx_start >= idx_end:
            continue

        offset   = pd.to_numeric(stops.iloc[:idx_start + 1]['travel_time_next']).sum()
        duration = pd.to_numeric(stops.iloc[idx_start + 1:idx_end + 1]['travel_time_next']).sum()
        valid_route_data.append({
            'route_id':        rid,
            'offset_to_start': offset,
            'trip_duration':   duration,
        })

    if not valid_route_data:
        return []

    df_valid  = pd.DataFrame(valid_route_data)
    df_merged = pd.merge(df_schedules, df_valid, on='route_id')

    def calc_times(row):
        origin_mins   = get_minutes(row['departure_time'])
        stop_dep_mins = origin_mins + row['offset_to_start']
        arrival_mins  = stop_dep_mins + row['trip_duration']
        return pd.Series([stop_dep_mins, arrival_mins])

    df_merged[['stop_dep_mins', 'arrival_mins']] = df_merged.apply(calc_times, axis=1)

    df_merged['stop_dep_mins_adj'] = df_merged['stop_dep_mins'].where(
        df_merged['stop_dep_mins'] >= user_mins,
        df_merged['stop_dep_mins'] + 1440,
    )

    df_filtered = df_merged[df_merged['stop_dep_mins_adj'] >= user_mins].copy()
    if df_filtered.empty:
        return []

    result = df_filtered.sort_values('stop_dep_mins_adj').head(limit)
    return [
        {
            "train_id":  str(row['schedule_id']),
            "departure": fmt(row['stop_dep_mins']),
            "arrival":   fmt(row['arrival_mins']),
            "duration":  f"{int(row['trip_duration'])} min",
        }
        for _, row in result.iterrows()
    ]


# ──────────────────────────── fare ─────────────────────────────────────

FARE_TABLE = [[0,3,5],[4,8,10],[9,15,15],[16,21,20],[22,30,25],[31,40,30]]

def fare_from_train_details(route_legs: list) -> list[int]:
    costs_per_leg = []
    for leg in route_legs:
        leg_source      = leg['from_stop']
        leg_destination = leg['to_stop']
        leg_stops_list  = leg.get('train_details', {}).get('stops', []) if leg.get('train_details') else []
        src_sequence = des_sequence = None
        for leg_stop in leg_stops_list:
            if leg_stop['stop_id'] == leg_source:
                src_sequence = leg_stop['sequence_no']
            elif leg_stop['stop_id'] == leg_destination and src_sequence is not None:
                des_sequence = leg_stop['sequence_no']
                break
        if src_sequence is None or des_sequence is None:
            costs_per_leg.append(0)
            continue
        counts = des_sequence - src_sequence
        cost = next((c[2] for c in FARE_TABLE if counts <= c[1]), FARE_TABLE[-1][2])
        costs_per_leg.append(cost)
    return costs_per_leg


def single_leg_fare(source_stop: str, destination_stop: str, train_id: str) -> int | None:
    """Fare for a same-line journey using the route_stops sequence directly."""
    try:
        df = pd.read_sql("""
            SELECT rs.sequence_no, rs.stop_id FROM route_stops rs
            JOIN schedules s ON rs.route_id = s.route_id
            WHERE s.schedule_id = %(sid)s
            ORDER BY rs.sequence_no
        """, engine, params={"sid": train_id})

        stop_ids = df['stop_id'].tolist()
        src_sequence = des_sequence = None
        for i, stop in enumerate(stop_ids):
            if stop == source_stop:
                src_sequence = i
            elif stop == destination_stop and src_sequence is not None:
                des_sequence = i
                break
        if src_sequence is None or des_sequence is None:
            return None
        counts = des_sequence - src_sequence
        for row in FARE_TABLE:
            if counts <= row[1]:
                return row[2]
        return FARE_TABLE[-1][2]
    except Exception:
        return None


# ──────────────────────────── crowd scores ─────────────────────────────

def fetch_crowd_scores(stop_ids: list[str]) -> dict[str, dict]:
    """
    Fetch crowd_score for a list of stop_ids in one query.
    Returns {stop_id: {"name": str, "crowd_score": float | None}}
    """
    stop_ids = list({s for s in stop_ids if s})  # dedupe, drop falsy
    if not stop_ids:
        return {}
    try:
        placeholders = ", ".join(f"'{s}'" for s in stop_ids)
        query = text(f"""
            SELECT s.stop_id, s.name,
                   COALESCE(cp.crowd_score, s.base_crowd_score) AS crowd_score
            FROM stops s
            LEFT JOIN station_crowd_profile cp ON s.stop_id = cp.stop_id
            WHERE s.stop_id IN ({placeholders})
        """)
        with engine.connect() as conn:
            rows = conn.execute(query).fetchall()
        return {
            r[0]: {"name": r[1], "crowd_score": float(r[2]) if r[2] is not None else None}
            for r in rows
        }
    except Exception as e:
        return {"_error": str(e)}


# ──────────────────── single-leg path (same line) ──────────────────────

async def _get_routes_single_leg(start_info: dict, end_info: dict, user_time: str) -> dict:
    """
    Same-line journey — was the old get_connectivity logic.
    Returns the SAME shape as multi-leg (legs[] with 1 entry) so downstream
    consumers (agent / frontend) only need to handle one format.
    """
    src_stop_id = start_info["stop_id"]
    dst_stop_id = end_info["stop_id"]

    def load_tables():
        df_rs = pd.read_sql(
            "SELECT route_id, stop_id, sequence_no, travel_time_next FROM route_stops",
            engine,
        )
        df_sch = pd.read_sql(
            "SELECT schedule_id, route_id, departure_time FROM schedules",
            engine,
        )
        return df_rs, df_sch

    df_route_stops, df_schedules = await asyncio.to_thread(load_tables)

    trains = find_trains_fast(src_stop_id, dst_stop_id, user_time, df_route_stops, df_schedules, limit=5)

    if not trains:
        raise ValueError("No viable routes found for the given time.")

    best_train = trains[0]

    try:
        details = await asyncio.to_thread(get_train_details, best_train["train_id"])
    except Exception:
        details = None

    line = determine_line(src_stop_id)

    leg = {
        "from_stop":       src_stop_id,
        "to_stop":         dst_stop_id,
        "line":            line,
        "start_latitude":  start_info["lat"],
        "start_longitude": start_info["lng"],
        "end_latitude":    end_info["lat"],
        "end_longitude":   end_info["lng"],
        "train_id":        best_train["train_id"],
        "departure":       best_train["departure"],
        "arrival":         best_train["arrival"],
        "train_details":   details,
    }

    fare_val = await asyncio.to_thread(single_leg_fare, src_stop_id, dst_stop_id, best_train["train_id"])
    fare_list = [fare_val if fare_val is not None else 0]

    # Crowd scores: source + destination only (no interchanges in single-leg)
    crowd = await asyncio.to_thread(fetch_crowd_scores, [src_stop_id, dst_stop_id])

    return {
        "start_stop":     src_stop_id,
        "end_stop":       dst_stop_id,
        "source_station": start_info["station_name"],
        "dest_station":   end_info["station_name"],
        "requested_time": user_time,
        "final_arrival":  best_train["arrival"],
        "legs":           [leg],
        "leg_fares":      fare_list,
        "crowd_scores":   crowd,
    }


# ──────────────────── multi-leg path (interchange) ──────────────────────

async def _get_routes_multi_leg(start_info: dict, end_info: dict, user_time: str) -> dict:
    """Cross-line journey with interchanges — was the old resultant-routes logic."""
    src_stop_id = start_info["stop_id"]
    dst_stop_id = end_info["stop_id"]

    routes = changeover_routes(src_stop_id, dst_stop_id)
    if not routes:
        raise ValueError("No routes found between these stops.")

    start_minutes = time_to_minutes(user_time)

    def load_tables():
        df_rs = pd.read_sql(
            "SELECT route_id, stop_id, sequence_no, travel_time_next FROM route_stops",
            engine,
        )
        df_sch = pd.read_sql(
            "SELECT schedule_id, route_id, departure_time FROM schedules",
            engine,
        )
        return df_rs, df_sch

    df_route_stops, df_schedules = await asyncio.to_thread(load_tables)

    viable_routes = []
    for route in routes:
        current_minutes  = start_minutes
        full_route_valid = True
        legs_detail      = []

        for leg in route:
            trains = find_trains_fast(
                leg['from_stop'], leg['to_stop'],
                minutes_to_time(current_minutes),
                df_route_stops, df_schedules,
            )
            if not trains:
                full_route_valid = False
                break

            train    = trains[0]
            dep_mins = time_to_minutes(train['departure'])
            arr_mins = time_to_minutes(train['arrival'])

            day     = current_minutes // 1440
            abs_dep = day * 1440 + dep_mins
            if abs_dep < current_minutes:
                abs_dep += 1440
            abs_arr = abs_dep + (arr_mins - dep_mins) % 1440

            legs_detail.append((train, leg, abs_dep, abs_arr))
            current_minutes = abs_arr

        if full_route_valid:
            viable_routes.append((current_minutes, legs_detail))

    if not viable_routes:
        raise ValueError("No viable routes found for the given time.")

    viable_routes.sort(key=lambda x: x[0])
    best_arrival, best_legs = viable_routes[0]

    async def fetch_detail(train_id: str):
        try:
            return await asyncio.to_thread(get_train_details, train_id)
        except Exception:
            return None

    details_list = await asyncio.gather(
        *[fetch_detail(train["train_id"]) for train, _, _, _ in best_legs]
    )

    legs_response = []
    for (train, leg, abs_dep, abs_arr), details in zip(best_legs, details_list):
        legs_response.append({
            "from_stop":       leg['from_stop'],
            "to_stop":         leg['to_stop'],
            "line":            leg['line'],
            "start_latitude":  start_info["lat"],
            "start_longitude": start_info["lng"],
            "end_latitude":    end_info["lat"],
            "end_longitude":   end_info["lng"],
            "train_id":        train['train_id'],
            "departure":       minutes_to_time(abs_dep),
            "arrival":         minutes_to_time(abs_arr),
            "train_details":   details,
        })

    fare_list = fare_from_train_details(legs_response)

    # Crowd scores: source, destination, and every interchange (to_stop of all
    # legs except the last)
    interchange_ids = [l["to_stop"] for l in legs_response[:-1]]
    crowd_targets   = [src_stop_id, dst_stop_id] + interchange_ids
    crowd = await asyncio.to_thread(fetch_crowd_scores, crowd_targets)

    return {
        "start_stop":     src_stop_id,
        "end_stop":       dst_stop_id,
        "source_station": start_info["station_name"],
        "dest_station":   end_info["station_name"],
        "requested_time": user_time,
        "final_arrival":  minutes_to_time(best_arrival),
        "legs":           legs_response,
        "leg_fares":      fare_list,
        "crowd_scores":   crowd,
    }


# ──────────────────────────── public entry point ────────────────────────

async def get_routes(start_stop: str, end_stop: str, user_time: str) -> dict:
    """
    SINGLE entry point replacing both old get_connectivity and resultant-routes.

    start_stop / end_stop: station names, addresses, OR stop_ids (e.g. 'PAN_HR').
    Resolution to stop_id happens internally via get_nearest_station.

    Returns the SAME shape regardless of single-leg vs multi-leg:
      {
        start_stop, end_stop, source_station, dest_station, requested_time,
        final_arrival, legs: [...], leg_fares: [...], crowd_scores: {...}
      }
    """
    start_info, end_info = await asyncio.gather(
        asyncio.to_thread(get_nearest_station, start_stop),
        asyncio.to_thread(get_nearest_station, end_stop),
    )

    if not start_info or not end_info:
        raise ValueError("Could not resolve stations for given addresses.")

    src_stop_id = start_info["stop_id"]
    dst_stop_id = end_info["stop_id"]

    if not src_stop_id or not dst_stop_id:
        raise ValueError("No stop ID found for one or both stations.")

    start_line = determine_line(src_stop_id)
    end_line   = determine_line(dst_stop_id)

    if start_line == end_line:
        return await _get_routes_single_leg(start_info, end_info, user_time)
    else:
        return await _get_routes_multi_leg(start_info, end_info, user_time)


if __name__ == "__main__":
    import asyncio, json, time

    async def _test():
        # Single-leg test (same line)
        t0 = time.time()
        r1 = await get_routes("Panvel", "Vashi", "20:00")
        print(f"Single-leg test ({time.time()-t0:.1f}s): legs={len(r1['legs'])}")
        print(json.dumps(r1, indent=2, default=str)[:800])
        print()
    asyncio.run(_test())