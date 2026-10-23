GROUP 7 MEMBERS
Ardhra VS   CCE23CS027
Arya Sudheer CCE23CS038
Ashna Tony  CCE23CS039
Ashwin Antony Nelson  CCE23CS040
Austin Shajan   CCE23CS041
Blessy CB   CCE23CS042




# Sustainable Waste Collection Routing

**Group:** Fill in your group number and members  
**Topic:** Sustainable Waste Collection Routing  
**SDGs:** 11, 12 and 13

## Overview
A small AI prototype that prioritizes simulated waste bins and plans collection routes using bin fill level, waste weight, vehicle capacity and road availability. All input data is synthetic.

## CO mapping
- **CO1:** Goal-based routing agent and PEAS description (`src/agent.py`)
- **CO2:** Uniform Cost Search and A* shortest-path search (`src/search.py`)
- **CO3:** CSP vehicle allocation with backtracking and forward checking (`src/csp.py`)
- **CO4:** Rule-based bin priority and vehicle load validation (`src/knowledge_base.py`)

## Requirements
Python 3.10+. Install the dashboard dependencies with:
```bash
pip install -r requirements.txt
```

## Run the Streamlit web app
From this project folder, run:
```bash
python -m streamlit run app.py
```
Streamlit will print a local URL (usually http://localhost:8501) to open in your browser.

## Run the command-line prototype (optional)
```bash
python -m src.main
```
Or choose another JSON input:
```bash
python -m src.main --file data/sample_city.json
```

## Tests
```bash
python -m unittest discover -s tests -v
```

## Input model
- `depot`: starting and ending depot node
- `vehicle_capacity`: maximum kilograms per vehicle
- `bins`: unique bin name, road-network location, fill percentage and waste kg
- `roads`: endpoints, simulated travel cost, road condition and blocked flag
- `vehicle_count`: optional number of vehicles for CSP (default 2)
- `collection_threshold`: optional fill threshold (default 50%)

## Method notes
The route planner repeatedly selects the nearest remaining selected bin using shortest paths and returns to the depot. This is a practical heuristic, not a guaranteed globally optimal multi-stop route. A* uses a zero heuristic because the sample has no coordinates; this is admissible but means A* behaves like UCS. For a stronger A* demonstration, add grounded map coordinates and a validated distance heuristic.

## Sustainability link
The prototype can demonstrate reduced simulated travel cost and prioritization of fuller bins. It does not prove real fuel or emissions savings without real-world measurements.
