from collections import Counter
from statistics import mean

from rules import RULES_ONE, RULES_TWO
from SimResult import SimulationResult
from utils import simulate

iterator: int = 10    #Use 1 for precise simulation, will be slower

RANGES = {
    "START": [30, 70],
    "SOLO_RESET": [25, 75],
    "GROUP_RESET": [0, 100]
}

def get_rules(half: int, useRules: bool):
    if useRules:
        return RULES_ONE if half == 1 else RULES_TWO
    return []

def get_range(half: int) -> list[int]:
    return RANGES["START"] if half == 1 else RANGES["SOLO_RESET"]

def get_time_limit(half: int) -> int:
    return 300 if half == 1 else 255

def get_clock_limit(half: int) -> int:
    return 300

def run_simulation(
    A,
    B,
    C,
    STABILITY,
    half,
    useRules: bool = True,
    starting_boulder_position: str | None = None,
    starting_boulder_health: float | None = None,
    starting_vents_checked: int = 0,
    starting_flips: int = 0,
    starting_points: float = 0.0,
    starting_xp: float = 0.0,
    starting_player_position: str | None = None,
    starting_player_position_delay: float = 0.0,
):
    RULES = get_rules(half, useRules=useRules)
    return simulate(
        A,
        B,
        C,
        STABILITY,
        RULES,
        time_limit=get_time_limit(half=half),
        clock_limit=get_clock_limit(half=half),
        starting_boulder_position=starting_boulder_position,
        starting_boulder_health=starting_boulder_health,
        starting_vents_checked=starting_vents_checked,
        starting_flips=starting_flips,
        starting_points=starting_points,
        starting_xp=starting_xp,
        starting_player_position=starting_player_position,
        starting_player_position_delay=starting_player_position_delay,
    )

def simulate_all(
    initial_stability,
    half: int,
    useRules: bool,
    starting_boulder_position: str | None = None,
    starting_boulder_health: float | None = None,
    starting_vents_checked: int = 0,
    starting_flips: int = 0,
    starting_points: float = 0.0,
    starting_xp: float = 0.0,
    starting_player_position: str | None = None,
    starting_player_position_delay: float = 0.0,
) -> list[SimulationResult]:
    results: list[SimulationResult] = []
    lower, upper = get_range(half)
    rules = get_rules(half, useRules)

    for A in range(lower, upper + 1, iterator):
        #print(f"Simulating for A={A}...")
        for B in range(lower, upper + 1, iterator):
            for C in range(lower, upper + 1, iterator):
                results.append(simulate(
                    A=A,
                    B=B,
                    C=C,
                    STABILITY=initial_stability,
                    rules=rules,
                    time_limit=get_time_limit(half),
                    clock_limit=get_clock_limit(half),
                    starting_boulder_position=starting_boulder_position,
                    starting_boulder_health=starting_boulder_health,
                    starting_vents_checked=starting_vents_checked,
                    starting_flips=starting_flips,
                    starting_points=starting_points,
                    starting_xp=starting_xp,
                    starting_player_position=starting_player_position,
                    starting_player_position_delay=starting_player_position_delay,
                ))

    return results


def simulate_single_game(A, B, C, useRules: bool = True):
    first_half = run_simulation(A, B, C, 50, 1, useRules=useRules)
    if first_half.death_time is not None:
        return {
            "initial_A": A,
            "initial_B": B,
            "initial_C": C,
            "first_half": first_half,
            "second_half_results": [],
        }

    second_half_results = simulate_all(
        first_half.final_stability,
        2,
        useRules,
        starting_boulder_position=first_half.boulder_position,
        starting_boulder_health=first_half.boulder_health,
        starting_vents_checked=first_half.vents_checked,
        starting_flips=first_half.flips,
        starting_points=first_half.points,
        starting_xp=first_half.xp,
        starting_player_position=first_half.player_position,
        starting_player_position_delay=first_half.player_position_delay,
    )

    return {
        "initial_A": A,
        "initial_B": B,
        "initial_C": C,
        "first_half": first_half,
        "second_half_results": second_half_results,
    }


def simulateGame(useRules: bool = True):
    games = []
    lower, upper = get_range(1)

    for A in range(lower, upper + 1, iterator):
        print(f"Simulating full games for starting A={A}...")
        for B in range(lower, upper + 1, iterator):
            for C in range(lower, upper + 1, iterator):
                games.append(simulate_single_game(A, B, C, useRules=useRules))

    return {"games": games}


def flatten_second_half_results(game_sweep):
    if "games" not in game_sweep:
        return game_sweep["second_half_results"]

    results = []
    for game in game_sweep["games"]:
        results.extend(game["second_half_results"])
    return results


def get_first_half_results(game_sweep):
    if "games" not in game_sweep:
        return [game_sweep["first_half"]]

    return [game["first_half"] for game in game_sweep["games"]]


def get_range_count(half: int) -> int:
    lower, upper = get_range(half)
    return len(range(lower, upper + 1, iterator))


def get_reset_outcome_count() -> int:
    count = get_range_count(2)
    return count * count * count


def get_full_game_outcomes(game_sweep):
    reset_outcome_count = get_reset_outcome_count()

    if "games" not in game_sweep:
        first_half = game_sweep["first_half"]
        if first_half.death_time is not None:
            return [(first_half, first_half.death_time)] * reset_outcome_count
        return [(result, get_clock_limit(1) + _get_result_end_time(result)) for result in game_sweep["second_half_results"]]

    outcomes = []
    for game in game_sweep["games"]:
        first_half = game["first_half"]
        if first_half.death_time is not None:
            outcomes.extend([(first_half, first_half.death_time)] * reset_outcome_count)
        else:
            outcomes.extend((result, get_clock_limit(1) + _get_result_end_time(result)) for result in game["second_half_results"])

    return outcomes


def get_full_game_time_in_mine(game_sweep):
    outcomes = []
    reset_outcome_count = get_reset_outcome_count()

    if "games" not in game_sweep:
        first_half = game_sweep["first_half"]
        if first_half.death_time is not None:
            return [first_half.death_time] * reset_outcome_count
        return [get_clock_limit(1) + _get_result_end_time(result) for result in game_sweep["second_half_results"]]

    for game in game_sweep["games"]:
        first_half = game["first_half"]
        if first_half.death_time is not None:
            outcomes.extend([first_half.death_time] * reset_outcome_count)
        else:
            outcomes.extend(get_clock_limit(1) + _get_result_end_time(result) for result in game["second_half_results"])

    return outcomes


def _get_result_end_time(result: SimulationResult) -> float:
    if result.death_time is not None:
        return result.death_time
    if result.completion_time is not None:
        return result.completion_time
    return get_clock_limit(2)


def _get_xp_hr(result: SimulationResult, end_time: float) -> float:
    return result.xp_with_points / (end_time + 34) * 3600 if end_time > 0 else 0


def print_game_summary(game):
    if "games" in game:
        first_half_results = get_first_half_results(game)
        second_half_results = flatten_second_half_results(game)
        first_half_deaths = [result for result in first_half_results if result.death_time is not None]
        first_half_survivors = len(first_half_results) - len(first_half_deaths)
        second_half_deaths = sum(result.death_time is not None for result in second_half_results)
        full_game_outcomes = get_full_game_outcomes(game)
        outcome_results = [result for result, _ in full_game_outcomes]
        total_deaths = sum(result.death_time is not None for result in outcome_results)
        completed = [result for result in outcome_results if result.b5_completed]
        exited = [result for result in outcome_results if result.completion_time is not None]
        total_outcomes = len(full_game_outcomes)

        print("Full game starting sweep")
        print(f"  Starting simulations: {len(first_half_results)}")
        print(f"  First-half deaths: {len(first_half_deaths)} ({len(first_half_deaths) / len(first_half_results):.1%})")
        print(f"  First-half survivors: {first_half_survivors}")
        print(f"  Second-half reset simulations: {len(second_half_results)}")
        print(f"  Reset outcomes per start: {get_reset_outcome_count()}")
        print(f"  Total full-game outcomes: {total_outcomes}")

        if full_game_outcomes:
            avg_game_time = mean(end_time for _, end_time in full_game_outcomes) + 34
            avg_xp_with_points = mean(result.xp_with_points for result in outcome_results)
            xp_hr_values = [_get_xp_hr(result, end_time) for result, end_time in full_game_outcomes]
            b5_completed_xp_hr = [_get_xp_hr(result, end_time) for result, end_time in full_game_outcomes if result.b5_completed]
            safe_partial_xp_hr = [_get_xp_hr(result, end_time) for result, end_time in full_game_outcomes if result.completion_time is not None and not result.b5_completed]
            death_xp_hr = [_get_xp_hr(result, end_time) for result, end_time in full_game_outcomes if result.death_time is not None]
            print(f"  Total deaths: {total_deaths} ({total_deaths / total_outcomes:.1%})")
            print(f"  Second-half deaths: {second_half_deaths} ({second_half_deaths / total_outcomes:.1%} of all outcomes)")
            print(f"  Avg final stability: {mean(result.final_stability for result in outcome_results):.2f}")
            print(f"  Avg points: {mean(result.points for result in outcome_results):.2f}")
            print(f"  Avg XP: {mean(result.xp for result in outcome_results):.2f}")
            print(f"  Successful exits: {len(exited)} ({len(exited) / total_outcomes:.1%})")
            print(f"  Avg game time (+34s): {avg_game_time:.2f}s")
            print(f"  Avg XP/hr: {avg_xp_with_points / avg_game_time * 3600:.2f}")
            print(f"  Avg outcome XP/hr: {mean(xp_hr_values):.2f}")
            if b5_completed_xp_hr:
                print(f"  Avg B5 completed XP/hr: {mean(b5_completed_xp_hr):.2f}")
            if safe_partial_xp_hr:
                print(f"  Avg safe partial-B5 exit XP/hr: {mean(safe_partial_xp_hr):.2f}")
            if death_xp_hr:
                print(f"  Avg death XP/hr: {mean(death_xp_hr):.2f}")
            print(f"  B5 completed games: {len(completed)} ({len(completed) / total_outcomes:.1%})")
        if completed:
            print(f"  Avg B5 completed time after reset: {mean(result.b5_completed_time for result in completed):.2f}s")
            print(f"  Avg B5 completed full-game time: {mean(get_clock_limit(1) + result.b5_completed_time for result in completed):.2f}s")
            print(f"  Avg B5 completed XP with points: {mean(result.xp_with_points for result in completed):.2f}")
        return

    first_half = game["first_half"]
    second_half_results = game["second_half_results"]
    if first_half.death_time is not None:
        print("First half")
        print(f"  Died at: {first_half.death_time}s")
        print(f"  Stability: {first_half.final_stability} (lowest {first_half.lowest_stability})")
        print(f"  Boulder: {first_half.boulder_position} ({first_half.boulder_health} health remaining)")
        print(f"  Vents checked: {first_half.vents_checked}")
        print(f"  Flips: {first_half.flips}")
        print(f"  Points: {first_half.points}")
        print(f"  XP: {first_half.xp}")
        print("\nFull game reset sweep")
        print("  Skipped because the player died before reset.")
        return

    deaths = sum(result.death_time is not None for result in second_half_results)
    completed = [result for result in second_half_results if result.b5_completed]
    exited = [result for result in second_half_results if result.completion_time is not None]
    total = len(second_half_results)
    boulder_counts = Counter(result.boulder_position or "None" for result in second_half_results)

    print("First half")
    print(f"  Stability: {first_half.final_stability} (lowest {first_half.lowest_stability})")
    print(f"  Boulder: {first_half.boulder_position} ({first_half.boulder_health} health remaining)")
    print(f"  Vents checked: {first_half.vents_checked}")
    print(f"  Flips: {first_half.flips}")
    print(f"  Points: {first_half.points}")
    print(f"  XP: {first_half.xp}")

    print("\nFull game reset sweep")
    print(f"  Simulations: {total}")
    print(f"  Deaths: {deaths} ({deaths / total:.1%})")
    print(f"  Avg final stability: {mean(result.final_stability for result in second_half_results):.2f}")
    print(f"  Avg points: {mean(result.points for result in second_half_results):.2f}")
    print(f"  Avg XP: {mean(result.xp for result in second_half_results):.2f}")
    if exited:
        avg_game_time = mean(get_clock_limit(1) + result.completion_time for result in exited) + 34
        avg_xp_with_points = mean(result.xp_with_points for result in exited)
        print(f"  Avg game time (+34s): {avg_game_time:.2f}s")
        print(f"  Avg XP/hr: {avg_xp_with_points / avg_game_time * 3600:.2f}")
    print(f"  Completed games: {len(completed)} ({len(completed) / total:.1%})")
    if completed:
        print(f"  Avg B5 completed time after reset: {mean(result.b5_completed_time for result in completed):.2f}s")
        print(f"  Avg B5 completed full-game time: {mean(get_clock_limit(1) + result.b5_completed_time for result in completed):.2f}s")
        print(f"  Avg completed XP with points: {mean(result.xp_with_points for result in completed):.2f}")
    print("  Final boulder positions:")
    for position in ["None", "B1", "B2", "B3", "B4", "B5"]:
        if position in boulder_counts:
            print(f"    {position}: {boulder_counts[position]}")