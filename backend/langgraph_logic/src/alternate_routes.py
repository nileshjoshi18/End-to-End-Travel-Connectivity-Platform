"""
alternate_routes.py  —  pure module, no FastAPI

"See additional routes" feature.

Only applies to MULTI-LEG (cross-line / interchange) journeys. After the
primary best-arrival route is computed by get_routes(), this module returns
up to 2 more alternate routes, selected purely by total duration
(shortest first, excluding the one already shown as primary).

Usage:
    from alternate_routes import get_alternate_routes
    alts = await get_alternate_routes("Panvel", "Virar", "20:00", exclude_legs=primary_result["legs"])
"""

import asyncio
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from system_brain import changeover_routes, determine_line
from train_details import get_train_details
from nearest_station import get_nearest_station
from routing_results import (
    find_trains_fast,
    fare_from_train_details,
    fetch_crowd_scores,
    time_to_minutes,
    minutes_to_time,
)


load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

engine = create_engine(DB_URL)

def _route_signature(legs: list) -> tuple:
    """Build a hashable signature of a route's legs to detect duplicates
    against the primary route (same from_stop/to_stop/line sequence)."""
    return tuple((l["from_stop"], l["to_stop"], l["line"]) for l in legs)


async def get_alternate_routes(
    start_stop: str,
    end_stop: str,
    user_time: str,
    exclude_legs: list | None = None,
    max_alternates: int = 2,
) -> list[dict]:
    """
    Returns up to `max_alternates` alternate multi-leg routes, sorted by
    total duration (ascending), excluding the route matching `exclude_legs`
    (typically the primary route already shown to the user).

    Returns [] if the journey is single-leg (same line) — alternates only
    make sense for interchange journeys with multiple line-path options.

    Each item has the same shape as a get_routes() result.
    """
    start_info, end_info = await asyncio.gather(
        asyncio.to_thread(get_nearest_station, start_stop),
        asyncio.to_thread(get_nearest_station, end_stop),
    )
    if not start_info or not end_info:
        return []

    src_stop_id = start_info["stop_id"]
    dst_stop_id = end_info["stop_id"]

    start_line = determine_line(src_stop_id)
    end_line   = determine_line(dst_stop_id)
    if start_line == end_line:
        return []  # single-leg journeys have no "alternate routes" concept here

    routes = changeover_routes(src_stop_id, dst_stop_id)
    if not routes or len(routes) <= 1:
        return []

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

    exclude_sig = _route_signature(exclude_legs) if exclude_legs else None
    viable_routes = []

    for route in routes:
        sig = tuple((l["from_stop"], l["to_stop"], l["line"]) for l in route)
        if exclude_sig is not None and sig == exclude_sig:
            continue  # skip the primary route — already shown

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

        if full_route_valid and legs_detail:
            total_duration = current_minutes - start_minutes
            viable_routes.append((total_duration, current_minutes, legs_detail))

    if not viable_routes:
        return []

    # Sort purely by total duration (ascending) — shortest journeys first
    viable_routes.sort(key=lambda x: x[0])
    top_alternates = viable_routes[:max_alternates]

    results = []
    for total_duration, final_arrival, legs_detail in top_alternates:
        async def fetch_detail(train_id: str):
            try:
                return await asyncio.to_thread(get_train_details, train_id)
            except Exception:
                return None

        details_list = await asyncio.gather(
            *[fetch_detail(train["train_id"]) for train, _, _, _ in legs_detail]
        )

        legs_response = []
        for (train, leg, abs_dep, abs_arr), details in zip(legs_detail, details_list):
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

        interchange_ids = [l["to_stop"] for l in legs_response[:-1]]
        crowd_targets   = [src_stop_id, dst_stop_id] + interchange_ids
        crowd = await asyncio.to_thread(fetch_crowd_scores, crowd_targets)

        results.append({
            "start_stop":      src_stop_id,
            "end_stop":        dst_stop_id,
            "source_station":  start_info["station_name"],
            "dest_station":    end_info["station_name"],
            "requested_time":  user_time,
            "final_arrival":   minutes_to_time(final_arrival),
            "total_duration_min": int(total_duration),
            "legs":            legs_response,
            "leg_fares":       fare_list,
            "crowd_scores":    crowd,
        })

    return results


if __name__ == "__main__":
    import asyncio, json

    async def _test():
        from routing_results import get_routes
        primary = await get_routes("Panvel", "Virar", "20:00")
        print(f"Primary route: {len(primary['legs'])} legs, arrival {primary['final_arrival']}")

        alts = await get_alternate_routes("Panvel", "Virar", "20:00", exclude_legs=primary["legs"])
        print(f"\nFound {len(alts)} alternate routes:")
        for i, alt in enumerate(alts):
            print(f"  Alt {i+1}: {len(alt['legs'])} legs, "
                  f"duration={alt['total_duration_min']}min, arrival={alt['final_arrival']}")

    asyncio.run(_test())