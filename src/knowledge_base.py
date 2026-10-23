def query_collection_priority(bin_data):
    facts = [
        f"fill_level({bin_data['name']}, {bin_data['fill_percent']}%)",
        f"waste_weight({bin_data['name']}, {bin_data['waste_kg']}kg)"
    ]
    if bin_data["fill_percent"] >= 80:
        answer = "high"
        rule = "Rule: priority(B, high) if fill_level(B, P) and P >= 80."
    elif bin_data["fill_percent"] >= 50:
        answer = "medium"
        rule = "Rule: priority(B, medium) if 50 <= fill_level(B, P) < 80."
    else:
        answer = "low"
        rule = "Rule: priority(B, low) if fill_level(B, P) < 50."
    return {"answer": answer, "trace": facts + [rule, f"Inference: priority({bin_data['name']}, {answer})."]}

def validate_vehicle_load(assigned_bins, capacity_kg):
    total = sum(b["waste_kg"] for b in assigned_bins)
    valid = total <= capacity_kg
    return {
        "answer": valid, "total_kg": total, "capacity_kg": capacity_kg,
        "trace": [
            f"Fact: total_assigned_waste = {total} kg",
            f"Fact: vehicle_capacity = {capacity_kg} kg",
            "Rule: load_valid if total_assigned_waste <= vehicle_capacity.",
            f"Inference: {total} <= {capacity_kg} is {valid}."
        ]
    }
