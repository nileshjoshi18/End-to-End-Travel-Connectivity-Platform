import pandas as pd
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

engine = create_engine(DB_URL)
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
    
def _get_all_stop_ids_for_name(station_name: str) -> list[str]:
    """
    Return ALL stop_ids whose name matches (case-insensitive) the given
    station name. Handles multi-line stations like Thane, Kurla, Vashi.
    """
    try:
        df = pd.read_sql(
            "SELECT stop_id FROM stops WHERE LOWER(name) = LOWER(%(name)s)",
            engine,
            params={"name": station_name},
        )
        return df["stop_id"].tolist()
    except Exception:
        return []
    
def _has_direct_connection(src_stop_id: str, dst_stop_id: str) -> bool:
    """
    Check route_stops for a real route_id where src_stop_id appears BEFORE
    dst_stop_id in sequence — i.e. an actual train can go from src to dst
    without changing lines. Same line SUFFIX alone isn't enough proof
    (a junction stop_id existing "on" a line doesn't guarantee every train
    on that line's route(s) passes both stops in the right order), so this
    verifies against real route_stops data instead of assuming.
    """
    try:
        df = pd.read_sql(
            """
            SELECT route_id, stop_id, sequence_no FROM route_stops
            WHERE route_id IN (
                SELECT route_id FROM route_stops WHERE stop_id = %(src)s
                INTERSECT
                SELECT route_id FROM route_stops WHERE stop_id = %(dst)s
            )
            """,
            engine,
            params={"src": src_stop_id, "dst": dst_stop_id},
        )
        for _, group in df.groupby("route_id"):
            seq = group.set_index("stop_id")["sequence_no"]
            if src_stop_id in seq.index and dst_stop_id in seq.index:
                if seq[src_stop_id] < seq[dst_stop_id]:
                    return True
        return False
    except Exception:
        return False


def _find_shared_line_stop_ids(
    src_candidates: list[str],
    dst_candidates: list[str],
) -> tuple[str | None, str | None]:
    """
    Given all stop_ids for source and destination (a station can have
    multiple stop_ids — one per line it sits on, e.g. junctions like Vashi
    or Thane), find a pair that shares a line AND actually has a direct
    route connecting them in the right direction.

    No fixed line priority: a shared line suffix is only a candidate, not
    proof of connectivity, so every shared-line pair is verified against
    route_stops via _has_direct_connection before being accepted. The first
    pair that verifies wins.
    """
    def line_of(stop_id: str) -> str:
        return stop_id.rsplit("_", 1)[-1] if "_" in stop_id else ""

    src_by_line: dict[str, list[str]] = {}
    for s in src_candidates:
        src_by_line.setdefault(line_of(s), []).append(s)
    dst_by_line: dict[str, list[str]] = {}
    for d in dst_candidates:
        dst_by_line.setdefault(line_of(d), []).append(d)

    shared_lines = set(src_by_line) & set(dst_by_line)
    if not shared_lines:
        return None, None

    for line in shared_lines:
        for src in src_by_line[line]:
            for dst in dst_by_line[line]:
                if _has_direct_connection(src, dst):
                    return src, dst

    return None, None