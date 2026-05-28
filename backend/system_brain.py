# system_brain.py
from collections import deque
from interchanges import line_graph
def determine_line(stop_id: str):
    """
    stop_id format: "CST_HR", "KUR_CR", "DAD_WR", "VAD_THR"
    Line code is always the part after the last underscore.
    """
    parts = stop_id.split("_")
    if len(parts) < 2:
        return None
    return parts[-1]


def find_line_paths(start_line: str, end_line: str):
    """ BFS on line graph — returns all line-sequences from start to end """
    if start_line == end_line:
        return [[start_line]]

    queue = deque([[start_line]])
    found = []

    while queue:
        path = queue.popleft()
        current = path[-1]
        for neighbor in line_graph.get(current, {}):
            if neighbor in path:              # avoid cycles
                continue
            new_path = path + [neighbor]
            if neighbor == end_line:
                found.append(new_path)
            else:
                queue.append(new_path)
    print(found)
    return found

def swap_line(stop_id: str, new_line: str):
    station_code = stop_id.split("_")[0]
    return f"{station_code}_{new_line}"


def expand_to_station_routes(line_paths, start_stop, end_stop):
    from itertools import product

    all_routes = []
    for line_path in line_paths:
        segment_options = []
        for i in range(len(line_path) - 1):
            a, b = line_path[i], line_path[i + 1]
            segment_options.append(line_graph[a][b])

        for ic_combo in product(*segment_options):
            legs = []
            for i, ic_stop in enumerate(ic_combo):
                current_line = line_path[i]
                from_stop = start_stop if i == 0 else swap_line(ic_combo[i-1], current_line)
                to_stop   = swap_line(ic_stop, current_line)  # ← key fix

                legs.append({'from_stop': from_stop, 'to_stop': to_stop, 'line': current_line})

            last_line = line_path[-1]
            legs.append({
                'from_stop': swap_line(ic_combo[-1], last_line),
                'to_stop':   end_stop,
                'line':      last_line
            })
            all_routes.append(legs)

    return all_routes


def changeover_routes(start_stop: str, end_stop: str):
    start_line = determine_line(start_stop)
    end_line   = determine_line(end_stop)

    if not start_line or not end_line:
        print("Could not determine line for one or both stops")
        return []

    line_paths = find_line_paths(start_line, end_line)
    routes     = expand_to_station_routes(line_paths, start_stop, end_stop)
    return routes

if __name__ == "__main__":
    routes123 = changeover_routes("PAN_HR", "VIR_WR")