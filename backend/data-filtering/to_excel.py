"""
Update lat/lng (and optionally the PostGIS 'geom' column) for the 'stops'
table in the PostgreSQL database, using values from an edited Excel file.

Only rows where BOTH lat and lng are filled in will be updated - rows that
are still blank in the spreadsheet are left untouched in the database.

Requirements:
    pip install pandas sqlalchemy psycopg2-binary openpyxl

Usage:
    python update_stops_latlng.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# CONNECTION SETTINGS - edit these or set as environment variables
# ---------------------------------------------------------------------------
DB_HOST = os.environ.get("PGHOST", "localhost")
DB_PORT = os.environ.get("PGPORT", "5432")
DB_NAME = os.environ.get("PGDATABASE", "mumbai_transit")
DB_USER = os.environ.get("PGUSER", "postgres")
DB_PASS = os.environ.get("PGPASSWORD", "postgres")

EXCEL_FILE = "database_export.xlsx"   # path to the edited file
SHEET_NAME = "stops"

# Set to True to also update the PostGIS 'geom' point from lat/lng (SRID 4326).
# Set to False if you only want to update the lat/lng columns.
UPDATE_GEOM = True


def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def main():
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

    # Only rows where both lat and lng have a value
    updates = df.dropna(subset=["lat", "lng"])
    skipped = len(df) - len(updates)
    print(f"{len(updates)} rows have lat/lng filled in -> will be updated")
    print(f"{skipped} rows still blank -> will be left untouched")

    engine = get_engine()

    if UPDATE_GEOM:
        sql = text("""
            UPDATE stops
            SET lat  = :lat,
                lng  = :lng,
                geom = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)
            WHERE stop_id = :stop_id
        """)
    else:
        sql = text("""
            UPDATE stops
            SET lat = :lat,
                lng = :lng
            WHERE stop_id = :stop_id
        """)

    updated = 0
    not_found = []

    with engine.begin() as conn:  # commits automatically if no errors
        for _, row in updates.iterrows():
            result = conn.execute(sql, {
                "stop_id": row["stop_id"],
                "lat": float(row["lat"]),
                "lng": float(row["lng"]),
            })
            if result.rowcount == 0:
                not_found.append(row["stop_id"])
            else:
                updated += result.rowcount

    print(f"\nSuccessfully updated {updated} rows in 'stops'.")
    if not_found:
        print(f"Warning: {len(not_found)} stop_id(s) not found in the database:")
        print(", ".join(not_found))


if __name__ == "__main__":
    main()