import json

def load_problem(path):
    with open(path, encoding="utf-8") as f:
        problem = json.load(f)
    validate_problem(problem)
    return problem

def validate_problem(p):
    for key in ("depot", "vehicle_capacity", "bins", "roads"):
        if key not in p:
            raise ValueError(f"Missing required field: {key}")
    if p["vehicle_capacity"] <= 0:
        raise ValueError("Vehicle capacity must be positive.")
    names = [b["name"] for b in p["bins"]]
    if len(names) != len(set(names)):
        raise ValueError("Bin names must be unique.")
    locations = {p["depot"]} | {b["location"] for b in p["bins"]}
    for b in p["bins"]:
        if not 0 <= b["fill_percent"] <= 100:
            raise ValueError(f"Invalid fill percentage for {b['name']}.")
        if b["waste_kg"] < 0:
            raise ValueError("Waste quantity cannot be negative.")
        if b["location"] not in locations:
            raise ValueError("Unknown bin location.")
    for r in p["roads"]:
        if r["from"] not in locations or r["to"] not in locations:
            raise ValueError(f"Road has unknown endpoint: {r}")
        if r["cost"] < 0:
            raise ValueError("Road costs must be non-negative.")

def priority(bin_data):
    if bin_data["fill_percent"] >= 80:
        return "high"
    if bin_data["fill_percent"] >= 50:
        return "medium"
    return "low"

def describe_agent():
    return {
        "Agent": "Goal-based waste collection routing agent",
        "Performance measure": "Collect priority bins with legal capacity and low travel cost",
        "Environment": "Synthetic depot, waste bins, vehicles and road network",
        "Sensors": "Bin fill levels, waste weight, road condition and blocked-road status",
        "Actuators": "Select bins, allocate vehicle loads and output a route",
        "Assumptions": "Road costs are simulated; roads are undirected; one vehicle route is planned"
    }
