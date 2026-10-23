# Test Results

Run from the repository root:

```bash
python -m unittest discover -s tests -v
```

Expected checks:
1. UCS and A* return the same shortest-path cost on a small route.
2. Multi-stop route starts and ends at the depot.
3. CSP allocations respect vehicle capacity.
4. Fill-level rules infer high priority for bins at or above 80%.
5. Capacity validation detects an overload.
6. Blocked roads are excluded from route planning.

Record actual test outcomes here after running the suite. Do not claim tests passed until executed.
