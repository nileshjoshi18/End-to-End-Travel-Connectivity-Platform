import pandas as pd
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert

engine = create_engine('postgresql://postgres:postgres@localhost:5432/mumbai_transit')
metadata = MetaData()

def push_to_db(file_name, table_name):
    print(f"--- Processing {table_name} ---")
    try:
        df = pd.read_excel(file_name)
        
        # Replace NaN with None so PostgreSQL gets NULL not 'nan'
        df = df.where(pd.notna(df), None)
        
        records = df.to_dict(orient="records")
        if not records:
            print(f"⚠️  No records in {file_name}, skipping.")
            return

        # Reflect the table structure from DB
        table = Table(table_name, metadata, autoload_with=engine)

        # Push in chunks of 100 to avoid parameter limits
        chunk_size = 100
        total_inserted = 0

        with engine.begin() as conn:
            for i in range(0, len(records), chunk_size):
                chunk = records[i:i + chunk_size]
                stmt = insert(table).values(chunk)
                stmt = stmt.on_conflict_do_nothing()  # skip duplicates silently
                conn.execute(stmt)
                total_inserted += len(chunk)

        print(f"✅ Processed {total_inserted} rows into {table_name} (duplicates skipped).")

    except Exception as e:
        print(f"❌ Error pushing to {table_name}: {e}")
        exit()

# Run in dependency order
# push_to_db('stops_table.xlsx',     'stops')
# push_to_db('route_table_2.xlsx',   'routes')
push_to_db('route_stops_2_1.xlsx',   'route_stops')
# push_to_db('schedule_table_2.xlsx','schedules')

print("\n🚀 All tables synchronized!")