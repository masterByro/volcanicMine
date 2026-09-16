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
    graph_first_half_sweep_summary,
    graph_full_game_deaths,
    graph_full_game_outcome_deaths,
    graph_full_game_sweep_deaths,
    graph_game_result_summary,
    graph_stability,
)
from jsonUtils import save_results_json
from SimResult import print_result
from simulations import flatten_second_half_results, get_clock_limit, get_first_half_results, get_full_game_outcomes, get_full_game_time_in_mine, get_time_limit, print_game_summary, simulate_all, simulateGame
from utils import simulate
from simulations import run_simulation
from XpUtils import expected_boulder_rewards

STABILITY = 50
half = 1
useRules = True
A = 60
B = 50
C = 50


def main():
    game = simulateGame(useRules=useRules)
    print_game_summary(game)
    timeline_graph = "output/full_game_first_half.png"
    first_half_graph = "output/full_game_first_half_sweep.png"
    deaths_graph = "output/full_game_deaths.png"
    summary_graph = "output/full_game_summary.png"
    first_half_results = get_first_half_results(game)
    second_half_results = flatten_second_half_results(game)
    full_game_outcomes = get_full_game_outcomes(game)
    full_game_results = [result for result, _ in full_game_outcomes]
    full_game_end_times = [end_time for _, end_time in full_game_outcomes]
    full_game_times = get_full_game_time_in_mine(game)
    graph_stability(
        run_simulation(A, B, C, STABILITY, half, useRules=useRules),
        timeline_graph,
        game_end_time=get_clock_limit(1) + get_clock_limit(2),
    )
    graph_first_half_sweep_summary(first_half_results, first_half_graph)
    second_half_offset = get_clock_limit(1)
    graph_full_game_outcome_deaths(
        full_game_outcomes,
        second_half_offset,
        game_end_time=second_half_offset + get_clock_limit(2),
        last_stability_update=second_half_offset + get_time_limit(2),
        output_path=deaths_graph,
    )
    if full_game_results:
        graph_game_result_summary(
            full_game_results,
            summary_graph,
            completion_time_offset=second_half_offset,
            outcome_end_times=full_game_times,
            xp_hr_times=full_game_end_times,
            game_end_time=second_half_offset + get_clock_limit(2),
        )
    print("\nGraphs")
    print(f"  Simulation timeline: {timeline_graph}")
    print(f"  First half sweep: {first_half_graph}")
    print(f"  Full game deaths: {deaths_graph}")
    if full_game_results:
        print(f"  Full game summary: {summary_graph}")

    #results = simulate_all(STABILITY, half, useRules)
    #save_results_json(results, "simulation_results.json")
    #graph_final_stability_distribution(results)
    #graph_cumulative_stability("simulation_results.json")
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