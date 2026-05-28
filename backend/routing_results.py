from system_brain import changeover_routes
from logic_test import find_trains
from train_details import get_train_details
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/resultant-routes")
def resultant_routes(start_stop: str, end_stop: str, user_time: str):
    routes = changeover_routes(start_stop, end_stop)

    if not routes:
        raise HTTPException(status_code=404, detail="No routes found between these stops.")

    start_minutes = time_to_minutes(user_time)
    viable_routes = []

    for route in routes:
        current_minutes = start_minutes
        full_route_valid = True
        legs_detail = []

        for leg in route:
            src  = leg['from_stop']
            dest = leg['to_stop']
            line = leg['line']

            current_time_str = minutes_to_time(current_minutes)
            trains = find_trains(src, dest, current_time_str)

            if not trains:
                full_route_valid = False
                break

            train = trains[0]

            dep_mins = time_to_minutes(train['departure'])
            arr_mins = time_to_minutes(train['arrival'])

            day = current_minutes // 1440
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
        details = get_train_details(train['train_id'])
        legs_response.append({
            "from_stop":   leg['from_stop'],
            "to_stop":     leg['to_stop'],
            "line":        leg['line'],
            "train_id":    train['train_id'],
            "departure":   minutes_to_time(abs_dep),
            "arrival":     minutes_to_time(abs_arr),
            "train_details": details,
        })

    return {
        "start_stop":     start_stop,
        "end_stop":       end_stop,
        "requested_time": user_time,
        "final_arrival":  minutes_to_time(best_arrival),
        "legs":           legs_response,
    }

if __name__ == "__main__":
    resultant_routes('VIR_WR', 'PAN_HR', '20:00')