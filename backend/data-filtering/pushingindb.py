import pandas as pd
from sqlalchemy import create_engine

# 1. Database Connection
# Adjust 'postgres:postgres' if you changed your password
engine = create_engine('postgresql://postgres:postgres@localhost:5432/mumbai_transit')

def push_to_db(file_name, table_name):
    print(f"--- Processing {table_name} ---")
    try:
        df = pd.read_excel(file_name)
        
        # Use chunksize=100 and method='multi' to avoid parameter limit errors
        df.to_sql(
            table_name, 
            engine, 
            if_exists='append', 
            index=False, 
            chunksize=100, 
            method='multi'
        )
        print(f"✅ Successfully pushed {len(df)} rows to {table_name}.")
    except Exception as e:
        print(f"❌ Error pushing to {table_name}: {e}")
        # Stop the script if a parent table fails
        exit()

# 2. THE CRITICAL ORDER
# If you haven't already, run 'TRUNCATE TABLE schedules, route_stops, routes, stops CASCADE;' in psql
# push_to_db('stops_table.xlsx', 'stops')          # Foundation
push_to_db('route_table_1.xlsx', 'routes')         # Parent
push_to_db('route_stops_1.xlsx', 'route_stops')   # Child of Routes/Stops
push_to_db('schedule_table_1.xlsx', 'schedules')   # Child of Routes/Stops

print("\n🚀 All tables synchronized and pushed to PostgreSQL!")