import json

from analysisUtils import (
    evaluate_n_negative_trigger_steps_to_zero,
    evaluate_full_series_predictors,
    find_best_early_warning_rule,
    find_best_rule_with_ab,
    plot_negative_change_fit_distribution,
    predict_remaining_steps_live_n_negative,
)
from graphing import (
    graph_cumulative_stability,
    graph_final_stability_distribution,
    graph_stability,
)
from jsonUtils import save_results_json
from SimResult import print_result
from simulations import simulate_all
from utils import simulate
from XpUtils import expected_boulder_rewards

STABILITY = 50
round = 1
useRules = True

def main():
    #result = simulate(A, B, C, STABILITY, RULES)
    #print_result(result)
    #graph_stability(result)

    results = simulate_all(STABILITY, round, useRules)
    save_results_json(results, "simulation_results.json")
    #graph_final_stability_distribution(results)
    graph_cumulative_stability("simulation_results.json")
    #find_best_early_warning_rule("simulation_results.json", num_changes=3, target_stability=10)
    #find_best_rule_with_ab("simulation_results.json", num_changes=3, target_stability=10)
    #plot_negative_change_fit_distribution("simulation_results.json", n=5)
    #evaluate_full_series_predictors("simulation_results.json")
    #evaluate_n_negative_trigger_steps_to_zero("simulation_results.json", n=2)
    #print(predict_remaining_steps_live_n_negative("simulation_results.json", [15, 17, 18, 0, 0, -1, -3], n=2))
    #plot_negative_change_fit_distribution("simulation_results.json")
    #results = expected_boulder_rewards()
    #print(json.dumps(results, indent=4))


if __name__ == "__main__":
    main()