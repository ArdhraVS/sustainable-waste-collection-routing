import unittest
from src.agent import load_problem
from src.search import shortest_path, plan_route
from src.csp import allocate_bins
from src.knowledge_base import query_collection_priority, validate_vehicle_load

class WasteRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = load_problem("data/sample_city.json")

    def test_ucs_and_astar_find_same_shortest_path_cost(self):
        u = shortest_path(self.p, "Depot", "A", "ucs")
        a = shortest_path(self.p, "Depot", "A", "astar")
        self.assertTrue(u["success"] and a["success"])
        self.assertEqual(u["cost"], a["cost"])

    def test_route_includes_depot_return(self):
        bins = [b["name"] for b in self.p["bins"] if b["fill_percent"] >= 50]
        result = plan_route(self.p, bins, "astar")
        self.assertTrue(result["success"])
        self.assertEqual(result["route"][0], self.p["depot"])
        self.assertEqual(result["route"][-1], self.p["depot"])

    def test_csp_allocation_respects_capacity(self):
        result = allocate_bins(self.p)
        self.assertTrue(result["success"])
        self.assertTrue(all(load <= self.p["vehicle_capacity"] for load in result["loads_kg"]))

    def test_priority_rule(self):
        b = {"name":"Test Bin", "fill_percent":90, "waste_kg":20}
        self.assertEqual(query_collection_priority(b)["answer"], "high")

    def test_load_capacity_failure(self):
        bins = [{"waste_kg":80}, {"waste_kg":40}]
        self.assertFalse(validate_vehicle_load(bins, 100)["answer"])

    def test_blocked_road_is_not_used(self):
        p = dict(self.p)
        p["roads"] = [dict(r) for r in self.p["roads"]]
        p["roads"].append({"from":"Depot","to":"Z","cost":1,"condition":"closed","blocked":True})
        result = shortest_path(p, "Depot", "Z", "ucs")
        self.assertFalse(result["success"])

if __name__ == "__main__":
    unittest.main()
