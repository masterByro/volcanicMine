from analysisUtils import evaluate_two_negative_trigger_steps_to_zero

out = evaluate_two_negative_trigger_steps_to_zero("simulation_results.json")
for name, m in out["models"].items():
    valid = m["valid_predictions"]
    exact_rate = m["exact_match_rate"] or 0.0
    exact_count = round(exact_rate * valid)
    print(name, "valid=", valid, "exact_rate=", exact_rate, "approx_exact_count=", exact_count)
