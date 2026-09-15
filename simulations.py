from rules import RULES
from SimResult import SimulationResult
from utils import simulate

useRule = True
iterator = 5    #Use 1 for precise simulation, will be slower

def simulate_all(initial_stability, sim_range: list[int]) -> list[SimulationResult]:
    results: list[SimulationResult] = []
    lower, upper = sim_range
    rules = RULES if useRule else []

    for A in range(lower, upper + 1, iterator):
        print(f"Simulating for A={A}...")
        for B in range(lower, upper + 1, iterator):
            for C in range(lower, upper + 1, iterator):
                results.append(simulate(A=A, B=B, C=C, STABILITY=initial_stability, rules=rules))

    return results