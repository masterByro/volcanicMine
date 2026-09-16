from collections import Counter
from statistics import mean

from rules import RULES_ONE, RULES_TWO
from SimResult import SimulationResult
from utils import simulate

iterator = 10    #Use 1 for precise simulation, will be slower

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
) -> list[SimulationResult]:
    results: list[SimulationResult] = []
    lower, upper = get_range(half)
    rules = get_rules(half, useRules)

    for A in range(lower, upper + 1, iterator):
        print(f"Simulating for A={A}...")
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
                ))

    return results


def simulateGame(A, B, C, useRules: bool = True):
    first_half = run_simulation(A, B, C, 50, 1, useRules=useRules)
    if first_half.death_time is not None:
        return {
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
    )

    return {
        "first_half": first_half,
        "second_half_results": second_half_results,
    }


def print_game_summary(game):
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
    completed = [result for result in second_half_results if result.completion_time is not None]
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
    print(f"  Completed games: {len(completed)} ({len(completed) / total:.1%})")
    if completed:
        print(f"  Avg completed time after reset: {mean(result.completion_time for result in completed):.2f}s")
        print(f"  Avg completed full-game time: {mean(get_clock_limit(1) + result.completion_time for result in completed):.2f}s")
        print(f"  Avg completed XP with points: {mean(result.xp_with_points for result in completed):.2f}")
    print("  Final boulder positions:")
    for position in ["None", "B1", "B2", "B3", "B4", "B5"]:
        if position in boulder_counts:
            print(f"    {position}: {boulder_counts[position]}")