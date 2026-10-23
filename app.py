"""Streamlit dashboard for the Sustainable Waste Collection Routing project."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.agent import priority, describe_agent, validate_problem
from src.search import plan_route
from src.csp import allocate_bins
from src.knowledge_base import query_collection_priority, validate_vehicle_load

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "data" / "sample_city.json"

st.set_page_config(
    page_title="Sustainable Waste Collection Routing",
    page_icon="♻️",
    layout="wide",
)

st.title("♻️ Sustainable Waste Collection Routing")
st.caption("AI mini project · SDGs 11, 12 and 13 · Simulated bins, vehicles and road conditions")
st.info(
    "This dashboard uses synthetic data for demonstration. Route cost is a simulated travel-cost unit, "
    "not a measured distance, fuel use, or verified emissions estimate."
)

@st.cache_data(show_spinner=False)
def load_default_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

if "problem" not in st.session_state:
    st.session_state.problem = load_default_data(str(DEFAULT_DATA))

original = copy.deepcopy(st.session_state.problem)

with st.sidebar:
    st.header("Planning settings")
    st.write("Adjust the simulation and click **Generate plan**.")
    capacity = st.number_input(
        "Capacity per vehicle (kg)", min_value=1, max_value=10000,
        value=int(original.get("vehicle_capacity", 100)), step=5,
    )
    vehicle_count = st.number_input(
        "Number of vehicles", min_value=1, max_value=20,
        value=int(original.get("vehicle_count", 2)), step=1,
    )
    threshold = st.slider("Collect bins at or above fill level (%)", 0, 100, 50, 5)
    algorithm_label = st.radio("Shortest-path search", ["A* Search", "Uniform-Cost Search (UCS)"])
    algorithm = "astar" if algorithm_label == "A* Search" else "ucs"
    st.caption("A* currently uses h(n) = 0 because the sample map has no coordinates, so its shortest-path results match UCS.")
    if st.button("Reset sample data", use_container_width=True):
        st.session_state.problem = load_default_data(str(DEFAULT_DATA))
        st.rerun()

st.subheader("1. Edit simulated bin data")
bins_df = pd.DataFrame(original["bins"])
bins_df = st.data_editor(
    bins_df,
    key="bins_editor",
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    column_config={
        "name": st.column_config.TextColumn("Bin name", required=True),
        "location": st.column_config.TextColumn("Road node", required=True),
        "fill_percent": st.column_config.NumberColumn("Fill level (%)", min_value=0, max_value=100, step=5, required=True),
        "waste_kg": st.column_config.NumberColumn("Estimated waste (kg)", min_value=0, step=1, required=True),
    },
)

st.subheader("2. Review road conditions")
roads_df = pd.DataFrame(original["roads"])
roads_df = st.data_editor(
    roads_df,
    key="roads_editor",
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    column_config={
        "from": st.column_config.TextColumn("From", required=True),
        "to": st.column_config.TextColumn("To", required=True),
        "cost": st.column_config.NumberColumn("Travel cost", min_value=0, step=1, required=True),
        "condition": st.column_config.SelectboxColumn("Condition", options=["good", "wet", "rough", "congested"], required=True),
        "blocked": st.column_config.CheckboxColumn("Blocked", help="Blocked roads cannot be used."),
    },
)

if st.button("🚛 Generate collection plan", type="primary", use_container_width=True):
    try:
        problem = copy.deepcopy(original)
        problem["vehicle_capacity"] = float(capacity)
        problem["vehicle_count"] = int(vehicle_count)
        problem["bins"] = bins_df.to_dict(orient="records")
        problem["roads"] = roads_df.to_dict(orient="records")
        for b in problem["bins"]:
            b["fill_percent"] = float(b["fill_percent"])
            b["waste_kg"] = float(b["waste_kg"])
        for r in problem["roads"]:
            r["cost"] = float(r["cost"])
            r["blocked"] = bool(r["blocked"])
        validate_problem(problem)
        st.session_state.problem = problem
        st.session_state.plan_result = {
            "problem": problem,
            "threshold": int(threshold),
            "algorithm": algorithm,
        }
    except Exception as exc:
        st.error(f"Could not generate the plan: {exc}")

result = st.session_state.get("plan_result")
if result:
    problem = result["problem"]
    threshold_used = result["threshold"]
    algorithm_used = result["algorithm"]
    selected_bins = [b for b in problem["bins"] if b["fill_percent"] >= threshold_used]

    st.divider()
    st.subheader("3. Plan summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bins selected", len(selected_bins), help=f"Fill level ≥ {threshold_used}%")
    c2.metric("High-priority bins", sum(b["fill_percent"] >= 80 for b in selected_bins))
    c3.metric("Vehicles available", problem["vehicle_count"])
    c4.metric("Vehicle capacity", f"{problem['vehicle_capacity']:g} kg")

    if not selected_bins:
        st.warning("No bins meet the selected fill threshold. Lower the threshold and generate the plan again.")
    else:
        selected_problem = copy.deepcopy(problem)
        selected_problem["bins"] = selected_bins
        allocation = allocate_bins(selected_problem)
        if not allocation["success"]:
            st.error(allocation["message"])
            st.write("The selected bins cannot all be assigned without exceeding vehicle capacity. Try adding a vehicle, increasing capacity, or lowering the collection threshold.")
            with st.expander("CSP reasoning trace"):
                st.code("\n".join(allocation["trace"]) or "No trace available.")
        else:
            st.success("All selected bins were allocated within vehicle capacity.")
            assign_df = pd.DataFrame(allocation["assignments"])
            if not assign_df.empty:
                assign_df = assign_df.rename(columns={
                    "bin": "Bin", "vehicle": "Assigned vehicle",
                    "waste_kg": "Waste (kg)", "fill_percent": "Fill (%)"
                })
                st.markdown("**Vehicle allocation (CSP: backtracking and forward checking)**")
                st.dataframe(assign_df, use_container_width=True, hide_index=True)

            st.markdown("**Vehicle routes**")
            route_rows = []
            route_successes = []
            total_cost = 0.0
            total_expanded = 0
            for vehicle_index in range(int(problem["vehicle_count"])):
                vehicle_name = f"Vehicle {vehicle_index + 1}"
                vehicle_bins = [a["bin"] for a in allocation["assignments"] if a["vehicle"] == vehicle_name]
                if not vehicle_bins:
                    route_rows.append({"Vehicle": vehicle_name, "Assigned bins": "—", "Route": problem["depot"], "Travel cost": 0, "Status": "No bins assigned"})
                    continue
                route_result = plan_route(problem, vehicle_bins, algorithm=algorithm_used)
                if route_result.get("success"):
                    total_cost += float(route_result["cost"])
                    total_expanded += int(route_result.get("expanded", 0))
                    route_successes.append(route_result)
                    route_rows.append({
                        "Vehicle": vehicle_name,
                        "Assigned bins": ", ".join(vehicle_bins),
                        "Route": " → ".join(route_result["route"]),
                        "Travel cost": round(float(route_result["cost"]), 2),
                        "Nodes expanded": route_result.get("expanded", 0),
                        "Status": "Route found",
                    })
                else:
                    route_rows.append({
                        "Vehicle": vehicle_name, "Assigned bins": ", ".join(vehicle_bins),
                        "Route": "—", "Travel cost": "—", "Nodes expanded": "—",
                        "Status": route_result.get("message", "No route found"),
                    })
            st.dataframe(pd.DataFrame(route_rows), use_container_width=True, hide_index=True)

            if len(route_successes) == sum(bool([a for a in allocation["assignments"] if a["vehicle"] == f"Vehicle {i+1}"]) for i in range(int(problem["vehicle_count"]))):
                m1, m2 = st.columns(2)
                m1.metric("Combined simulated travel cost", f"{total_cost:g}")
                m2.metric("Shortest-path nodes expanded", total_expanded)
            else:
                st.warning("At least one assigned bin group has no feasible road route. Review blocked roads and connectivity.")

            st.markdown("**Vehicle load checks**")
            load_rows = []
            for vehicle_index in range(int(problem["vehicle_count"])):
                vehicle_name = f"Vehicle {vehicle_index + 1}"
                assigned_names = [a["bin"] for a in allocation["assignments"] if a["vehicle"] == vehicle_name]
                assigned = [b for b in selected_bins if b["name"] in assigned_names]
                check = validate_vehicle_load(assigned, problem["vehicle_capacity"])
                load_rows.append({"Vehicle": vehicle_name, "Assigned waste (kg)": check["total_kg"], "Capacity (kg)": check["capacity_kg"], "Valid": "✅ Yes" if check["answer"] else "❌ No"})
            st.dataframe(pd.DataFrame(load_rows), use_container_width=True, hide_index=True)

    st.subheader("4. Bin priority and logic inference (CO4)")
    priority_rows = []
    for b in problem["bins"]:
        result_priority = query_collection_priority(b)
        priority_rows.append({
            "Bin": b["name"], "Fill level (%)": b["fill_percent"],
            "Waste (kg)": b["waste_kg"], "Priority": result_priority["answer"].title(),
            "Selected for collection": "Yes" if b["fill_percent"] >= threshold_used else "No",
        })
    st.dataframe(pd.DataFrame(priority_rows), use_container_width=True, hide_index=True)
    with st.expander("Show sample inference trace"):
        if problem["bins"]:
            chosen = max(problem["bins"], key=lambda b: b["fill_percent"])
            trace = query_collection_priority(chosen)
            st.write(f"**Query:** What is the priority of {chosen['name']}?")
            st.code("\n".join(trace["trace"]))
        st.write("**Road rule:** blocked roads are excluded from the graph before shortest-path search.")
        st.write("**Capacity rule:** assigned waste must be less than or equal to the configured vehicle capacity.")

    st.subheader("5. Agent PEAS (CO1)")
    st.json(describe_agent())

    st.subheader("6. Sustainability indicators")
    st.markdown(
        "- **SDG 11:** number of selected bins serviced and whether high-priority bins remain unserved.\n"
        "- **SDG 12:** waste collected per trip and vehicle capacity utilisation.\n"
        "- **SDG 13:** simulated route cost can be compared with a baseline, but it is not a verified CO₂ estimate."
    )

    st.download_button(
        "Download current simulation input (JSON)",
        data=json.dumps(problem, indent=2),
        file_name="waste_collection_simulation.json",
        mime="application/json",
    )
else:
    st.markdown("### How to use")
    st.markdown(
        "1. Edit bin fill levels or waste weights.\n"
        "2. Mark roads as blocked or adjust their simulated travel cost.\n"
        "3. Choose vehicle capacity, fleet size, and collection threshold in the sidebar.\n"
        "4. Click **Generate collection plan** to see vehicle assignments, routes, load checks, and priority reasoning."
    )

st.divider()
st.caption("Prototype note: multi-stop ordering uses a nearest-next-bin heuristic; it is not guaranteed to be globally optimal.")
