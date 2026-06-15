from system_brain import changeover_routes
from logic_test import find_trains
from train_details import get_train_details
from nearest_station import get_nearest_station
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:postgres@localhost:5432/mumbai_transit')

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def time_to_minutes(t: str, day_offset: int = 0) -> int:
    h, m = map(int, t.split(':'))
    return day_offset * 1440 + h * 60 + m

def minutes_to_time(mins: int) -> str:
    mins = mins % 1440
    return f"{mins // 60:02d}:{mins % 60:02d}"

def fare(route_legs: list):
    costs_by_sequence = [[0,3,5],[4,8,10],[9,15,15],[16,21,20],[22,30,25],[31,40,30]]
    costs_per_leg = []
    # print(route_legs)
    for leg in route_legs:
        leg_source = leg['from_stop']
        leg_destination = leg['to_stop']
        leg_stops_list = leg['train_details']['stops']
        for leg_stops in leg_stops_list:
            if leg_stops['stop_id'] == leg_source:
                src_sequence = leg_stops['sequence_no']

            elif leg_stops['stop_id'] == leg_destination:
                des_sequence = leg_stops['sequence_no']
                break
        counts = des_sequence-src_sequence
        for list_cost_by_sequence in costs_by_sequence:
            if(counts <= list_cost_by_sequence[1]):
                costs_per_leg.append(list_cost_by_sequence[2])
                break
    return costs_per_leg

@app.get("/resultant-routes")
async def resultant_routes(start_stop: str, end_stop: str, user_time: str):

    start_info = get_nearest_station(start_stop)
    end_info   = get_nearest_station(end_stop)

    if not start_info or not end_info:
        raise HTTPException(status_code=404, detail="Could not resolve stations for given addresses.")

    start_stop = start_info["stop_id"]
    end_stop   = end_info["stop_id"]
    start_info_lat, start_info_long = start_info["lat"], start_info["lng"]
    end_info_lat, end_info_long = end_info["lat"], end_info["lng"]
    if not start_stop or not end_stop:
        raise HTTPException(status_code=404, detail=f"No stop ID found for one or both stations.")

    routes = changeover_routes(start_stop, end_stop)

    if not routes:
        raise HTTPException(status_code=404, detail="No routes found between these stops.")

    start_minutes = time_to_minutes(user_time)
    viable_routes = []

    for route in routes:
        current_minutes  = start_minutes
        full_route_valid = True
        legs_detail      = []
        for leg in route:
            src  = leg['from_stop']
            dest = leg['to_stop']
            line = leg['line']
            trains = find_trains(src, dest, minutes_to_time(current_minutes))
            if not trains:
                full_route_valid = False
                break
            train = trains[0]

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
        raise HTTPException(status_code=404, detail="No viable routes found for the given time.")

    viable_routes.sort(key=lambda x: x[0])
    best_arrival, best_legs = viable_routes[0]

    legs_response = []
    for train, leg, abs_dep, abs_arr in best_legs:
        try:
            details = get_train_details(train['train_id'])
        except HTTPException:
            details = None

        legs_response.append({
            "from_stop":     leg['from_stop'],
            "to_stop":       leg['to_stop'],
            "line":          leg['line'],
            "start_latitude":      start_info_lat,
            "start_longitude":     start_info_long,
            "end_latitude":        end_info_lat,
            "end_longitude":       end_info_long,
            "train_id":      train['train_id'],
            "departure":     minutes_to_time(abs_dep),
            "arrival":       minutes_to_time(abs_arr),
            "train_details": details,
        })
    fare_list = fare(legs_response)
    return {
        "start_stop":     start_stop,
        "end_stop":       end_stop,
        "source_station": start_info["station_name"],
        "dest_station":   end_info["station_name"],
        "requested_time": user_time,
        "final_arrival":  minutes_to_time(best_arrival),
        "legs":           legs_response,
        "leg_fares":      fare_list,
    }


if __name__ == "__main__":
    import asyncio
    # FIX: resultant_routes is async — must be awaited
    result = asyncio.run(resultant_routes("seawoods station", "virar station", "20:00"))
    print(result)