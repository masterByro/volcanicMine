import json

from analysisUtils import find_best_early_warning_rule, find_best_rule_with_ab
from graphing import (
    graph_cumulative_stability,
    graph_final_stability_distribution,
    graph_stability,
)
from jsonUtils import save_results_json
from rules import RULES
from SimResult import print_result
from simulations import simulate_all
from utils import simulate
from XpUtils import expected_boulder_rewards

A = 34
B = 91
C = 52
STABILITY = 60
RANGES = {
    "START": [30, 70],
    "SOLO_RESET": [25, 75],
    "GROUP_RESET": [0, 100]
}

def main():
    # result = simulate(A, B, C, STABILITY, RULES)
    # print_result(result)
    # graph_stability(result)

    results = simulate_all(STABILITY, RANGES["START"])
    save_results_json(results, "simulation_results.json")
    # #graph_final_stability_distribution(results)
    # graph_cumulative_stability("simulation_results.json")
    #find_best_early_warning_rule("simulation_results.json", num_changes=3, target_stability=10)
    find_best_rule_with_ab("simulation_results.json", num_changes=3, target_stability=10)
    
    #results = expected_boulder_rewards()
    #print(json.dumps(results, indent=4))


if __name__ == "__main__":
    main()