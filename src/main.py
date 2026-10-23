import argparse
from src.agent import load_problem, describe_agent
from src.search import plan_route, shortest_path
from src.csp import allocate_bins
from src.knowledge_base import query_collection_priority, validate_vehicle_load

def main():
    parser = argparse.ArgumentParser(description="Sustainable Waste Collection Routing")
    parser.add_argument("--file", default="data/sample_city.json")
    args = parser.parse_args()
    p = load_problem(args.file)
    print("=== CO1: PEAS / Agent ===")
    for k, v in describe_agent().items():
        print(f"{k}: {v}")
    print("\n=== Bin priorities ===")
    for b in p["bins"]:
        q = query_collection_priority(b)
        print(f"{b['name']}: {q['answer']} priority ({b['fill_percent']}% full)")
        for line in q["trace"]:
            print("  ", line)
    selected = [b["name"] for b in p["bins"] if b["fill_percent"] >= p.get("collection_threshold", 50)]
    print("\nSelected bins (threshold >= 50%):", selected)
    print("\n=== CO2: Route planning ===")
    for algorithm in ("ucs", "astar"):
        route = plan_route(p, selected, algorithm)
        print(f"{algorithm.upper()}: {route}")
    print("\n=== CO3: Vehicle allocation CSP ===")
    csp = allocate_bins(p)
    print(csp["message"])
    for row in csp["assignments"]:
        print(row)
    print("Backtracks:", csp["backtracks"])
    for line in csp["trace"]:
        print("  ", line)
    print("\n=== CO4: Load validation ===")
    by_vehicle = {}
    by_name = {b["name"]: b for b in p["bins"]}
    for row in csp["assignments"]:
        by_vehicle.setdefault(row["vehicle"], []).append(by_name[row["bin"]])
    for vehicle, bins in by_vehicle.items():
        q = validate_vehicle_load(bins, p["vehicle_capacity"])
        print(vehicle, q)
    print("\nNote: road costs and waste values are synthetic. The route planner uses a nearest-next-stop strategy over shortest paths, not a globally optimal multi-stop TSP solver.")

if __name__ == "__main__":
    main()
