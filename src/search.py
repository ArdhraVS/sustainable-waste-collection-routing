import heapq
import itertools

def build_graph(problem):
    graph = {}
    for road in problem["roads"]:
        if road.get("blocked", False):
            continue
        a, b, cost = road["from"], road["to"], float(road["cost"])
        # Road condition can be represented through the provided simulated cost.
        graph.setdefault(a, []).append((b, cost))
        graph.setdefault(b, []).append((a, cost))
    return graph

def shortest_path(problem, start, goal, algorithm="ucs"):
    algorithm = algorithm.lower()
    if algorithm not in ("ucs", "astar"):
        raise ValueError("algorithm must be ucs or astar")
    graph = build_graph(problem)
    if start == goal:
        return {"success": True, "path": [start], "cost": 0, "expanded": 0}
    if start not in graph or goal not in graph:
        return {"success": False, "message": "Start or goal is not connected.", "expanded": 0}

    # Safe heuristic: zero is admissible for all non-negative edge costs.
    # This makes A* equivalent to UCS, but preserves correctness without coordinates.
    def h(_node):
        return 0

    counter = itertools.count()
    heap = [(h(start) if algorithm == "astar" else 0, 0, next(counter), start, [start])]
    best = {start: 0}
    expanded = 0
    while heap:
        _, cost, _, node, path = heapq.heappop(heap)
        if cost != best.get(node):
            continue
        expanded += 1
        if node == goal:
            return {"success": True, "path": path, "cost": cost, "expanded": expanded}
        for nxt, edge_cost in graph.get(node, []):
            new_cost = cost + edge_cost
            if new_cost < best.get(nxt, float("inf")):
                best[nxt] = new_cost
                priority = new_cost + (h(nxt) if algorithm == "astar" else 0)
                heapq.heappush(heap, (priority, new_cost, next(counter), nxt, path + [nxt]))
    return {"success": False, "message": "No route found.", "expanded": expanded}

def plan_route(problem, selected_bins, algorithm="astar"):
    depot = problem["depot"]
    by_name = {b["name"]: b for b in problem["bins"]}
    remaining = [by_name[name] for name in selected_bins]
    current = depot
    route = [depot]
    total_cost = 0
    expanded = 0
    # Greedy next-stop choice using shortest path cost; repeatable demonstration heuristic.
    while remaining:
        choices = []
        for b in remaining:
            result = shortest_path(problem, current, b["location"], algorithm)
            if result["success"]:
                choices.append((result["cost"], b["name"], b, result))
        if not choices:
            return {"success": False, "message": f"No road route from {current} to remaining bins."}
        cost, _, chosen, result = min(choices, key=lambda x: (x[0], x[1]))
        total_cost += cost
        expanded += result["expanded"]
        route.extend(result["path"][1:])
        current = chosen["location"]
        remaining.remove(chosen)
    back = shortest_path(problem, current, depot, algorithm)
    if not back["success"]:
        return {"success": False, "message": "Cannot return to depot."}
    total_cost += back["cost"]
    expanded += back["expanded"]
    route.extend(back["path"][1:])
    return {"success": True, "route": route, "bins": selected_bins,
            "cost": total_cost, "expanded": expanded}
