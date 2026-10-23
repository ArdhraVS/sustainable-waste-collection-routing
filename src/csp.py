def allocate_bins(problem):
    """CSP: assign bins to vehicles, enforcing total waste <= capacity."""
    bins = sorted(problem["bins"], key=lambda b: (-b["fill_percent"], b["name"]))
    capacity = float(problem["vehicle_capacity"])
    # For this compact prototype, number of vehicles is user configurable in input.
    vehicle_count = int(problem.get("vehicle_count", 2))
    variables = [b["name"] for b in bins]
    domains = {b["name"]: list(range(vehicle_count)) for b in bins}
    by_name = {b["name"]: b for b in bins}
    loads = [0.0] * vehicle_count
    assignment = {}
    trace = []
    backtracks = 0

    def search(index, current_domains):
        nonlocal backtracks
        if index == len(variables):
            return True
        name = variables[index]
        b = by_name[name]
        # Try currently least-loaded vehicles first.
        for vehicle in sorted(current_domains[name], key=lambda v: loads[v]):
            if loads[vehicle] + b["waste_kg"] > capacity:
                trace.append(f"Forward check: {name} cannot go to Vehicle {vehicle+1} (capacity).")
                continue
            assignment[name] = vehicle
            loads[vehicle] += b["waste_kg"]
            trace.append(f"Assign {name} -> Vehicle {vehicle+1}; load={loads[vehicle]:g} kg")
            reduced = {k: list(v) for k, v in current_domains.items()}
            # Forward checking removes a vehicle from a remaining bin's domain
            # if that bin could no longer fit after the current load.
            failed = False
            for other in variables[index+1:]:
                reduced[other] = [
                    v for v in reduced[other]
                    if loads[v] + by_name[other]["waste_kg"] <= capacity
                ]
                if not reduced[other]:
                    failed = True
                    trace.append(f"Forward checking failure: no vehicle can take {other}.")
                    break
            if not failed and search(index+1, reduced):
                return True
            loads[vehicle] -= b["waste_kg"]
            del assignment[name]
            backtracks += 1
            trace.append(f"Backtrack: {name}")
        return False

    success = search(0, domains)
    assignments = [
        {"bin": b["name"], "vehicle": f"Vehicle {assignment[b['name']]+1}",
         "waste_kg": b["waste_kg"], "fill_percent": b["fill_percent"]}
        for b in bins if b["name"] in assignment
    ]
    return {"success": success, "assignments": assignments,
            "vehicle_count": vehicle_count, "capacity_kg": capacity,
            "loads_kg": loads if success else [], "backtracks": backtracks,
            "trace": trace,
            "message": "All bins allocated." if success else "Cannot allocate all bins within vehicle capacities."}
