from rules import RULES_ONE, RULES_TWO
from SimResult import SimulationResult
from utils import simulate

iterator = 5    #Use 1 for precise simulation, will be slower

RANGES = {
    "START": [30, 70],
    "SOLO_RESET": [25, 75],
    "GROUP_RESET": [0, 100]
}

def get_rules(round: int, useRules: bool):
    if useRules:
        return RULES_ONE if round == 1 else RULES_TWO
    return []

def get_range(round: int) -> list[int]:
    return RANGES["START"] if round == 1 else RANGES["SOLO_RESET"]

def get_time_limit(round: int) -> int:
    return 300 if round == 1 else 255

def run_simulation(A, B, C, STABILITY, round, useRules: bool = True):
    RULES = get_rules(round, useRules=useRules)
    return simulate(A, B, C, STABILITY, RULES, time_limit=get_time_limit(round=round))

def simulate_all(initial_stability, round: int, useRules: bool) -> list[SimulationResult]:
    results: list[SimulationResult] = []
    lower, upper = RANGES["START"]
    rules = get_rules(round, useRules)

    for A in range(lower, upper + 1, iterator):
        print(f"Simulating for A={A}...")
        for B in range(lower, upper + 1, iterator):
            for C in range(lower, upper + 1, iterator):
                results.append(simulate(A=A, B=B, C=C, STABILITY=initial_stability, rules=rules, time_limit=get_time_limit(round)))

    return results