import pandas as pd
from sqlalchemy import create_engine

# 1. Setup Database Connection
# Adjust the connection string if your password or port is different
engine = create_engine('postgresql://postgres:postgres@localhost:5432/mumbai_transit')

def get_minutes(t):
    """Converts HH:MM or datetime object to total minutes from midnight."""
    if t is None: return 0
    if hasattr(t, 'hour'): 
        return t.hour * 60 + t.minute
    try:
        parts = str(t).split(':')
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0

def find_trains(start_stop, end_stop, user_time_str):
    """
    Finds the next 5 trains from a start station to an end station.
    Calculates arrival times based on cumulative travel offsets.
    """
    # Load Data from PostgreSQL
    df_route_stops = pd.read_sql("SELECT route_id, stop_id, sequence_no, travel_time_next FROM route_stops", engine)
    df_schedules = pd.read_sql("SELECT schedule_id, route_id, departure_time FROM schedules", engine)
    
    user_mins = get_minutes(user_time_str)
    
    valid_route_data = []
    
    # Group by route to find paths containing both stops in the correct order
    for rid, group in df_route_stops.groupby('route_id'):
        stops = group.sort_values('sequence_no').reset_index(drop=True)
        
        # Check if both stops exist in this specific route
        if start_stop in stops['stop_id'].values and end_stop in stops['stop_id'].values:
            idx_start = stops[stops['stop_id'] == start_stop].index[0]
            idx_end = stops[stops['stop_id'] == end_stop].index[0]
            
            # Ensure the train is moving in the right direction
            if idx_start < idx_end:
                # OFFSET: Sum travel_time_next (time from previous) up to the start stop
                # Example: If index is 3, it sums 0,1,2,3 to get total time from origin
                offset = pd.to_numeric(stops.iloc[:idx_start + 1]['travel_time_next']).sum()
                
                # DURATION: Sum travel_time_next for the legs between start and end
                duration = pd.to_numeric(stops.iloc[idx_start + 1 : idx_end + 1]['travel_time_next']).sum()
                
                valid_route_data.append({
                    'route_id': rid,
                    'offset_to_start': offset,
                    'trip_duration': duration
                })
    
    if not valid_route_data:
        print(f"No direct routes found from {start_stop} to {end_stop}.")
        return

    # Convert valid routes to DataFrame and merge with train schedules
    df_valid_routes = pd.DataFrame(valid_route_data)
    df_final = pd.merge(df_schedules, df_valid_routes, on='route_id')

    # Calculate actual Departure/Arrival times for the specific stations
    def calc_times(row):
        origin_mins = get_minutes(row['departure_time'])
        stop_dep_mins = origin_mins + row['offset_to_start']
        arrival_mins = stop_dep_mins + row['trip_duration']
        return pd.Series([stop_dep_mins, arrival_mins])

    df_final[['stop_dep_mins', 'arrival_mins']] = df_final.apply(calc_times, axis=1)
    
    # Filter for trains that depart at or after the user's input time
    df_filtered = df_final[df_final['stop_dep_mins'] >= user_mins].copy()

    if df_filtered.empty:
        print(f"No more trains found from {start_stop} after {user_time_str} today.")
        return

    # Formatting for terminal output
    df_filtered['Departure'] = df_filtered['stop_dep_mins'].apply(lambda x: f"{int((x%1440)//60):02d}:{int(x%60):02d}")
    df_filtered['Arrival'] = df_filtered['arrival_mins'].apply(lambda x: f"{int((x%1440)//60):02d}:{int(x%60):02d}")
    df_filtered['Duration'] = df_filtered['trip_duration'].apply(lambda x: f"{int(x)} min")
    
    # Rename schedule_id to Train_ID to match your request
    df_filtered = df_filtered.rename(columns={'schedule_id': 'Train_ID'})

    # Sort by departure time and take top 5
    result = df_filtered.sort_values('stop_dep_mins').head(5)

    print(f"\n--- Top 5 Trains from {start_stop} to {end_stop} after {user_time_str} ---")
    print(result[['Train_ID', 'Departure', 'Arrival', 'Duration']].to_string(index=False))

# --- Execution ---
if __name__ == "__main__":
    # Test with your specific mid-station query
    find_trains('CHU_WR', 'GOR_WR', '08:00')