# train_details.py
import pandas as pd
from sqlalchemy import create_engine
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

engine = create_engine('postgresql://postgres:postgres@localhost:5432/mumbai_transit')

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/get-train-details")
def get_train_details(schedule_id: str):
    df_sched = pd.read_sql(
        "SELECT schedule_id, route_id, departure_time FROM schedules WHERE schedule_id = %(sid)s",
        engine, params={"sid": schedule_id}
    )
    if df_sched.empty:
        raise HTTPException(status_code=404, detail=f"Schedule '{schedule_id}' not found.")

    sched        = df_sched.iloc[0]
    route_id     = sched['route_id']
    origin_mins  = get_minutes(sched['departure_time'])

    df_stops = pd.read_sql("""
        SELECT rs.sequence_no, rs.stop_id, rs.travel_time_next, s.name AS stop_name
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.stop_id
        WHERE rs.route_id = %(rid)s
        ORDER BY rs.sequence_no
    """, engine, params={"rid": route_id})

    if df_stops.empty:
        raise HTTPException(status_code=404, detail=f"No stops found for route '{route_id}'.")

    cumulative_mins = origin_mins
    stop_schedule   = []

    # FIX: use enumerate so counter is always 0,1,2,3... regardless of DF index
    for counter, (_, row) in enumerate(df_stops.iterrows()):
        if counter > 0:
            cumulative_mins += pd.to_numeric(row['travel_time_next'], errors='coerce') or 0
        stop_schedule.append({
            "sequence_no":  int(row['sequence_no']),
            "stop_id":      row['stop_id'],
            "stop_name":    row['stop_name'],
            "arrival_time": fmt(cumulative_mins),
        })

    return {
        "schedule_id":      schedule_id,
        "route_id":         route_id,
        "origin_departure": fmt(origin_mins),
        "total_stops":      len(stop_schedule),
        "stops":            stop_schedule,
    }
if __name__ == "__main__":
    trains = get_train_details('HRSPV_98072')
    for t in trains['stops']:
        print(t)