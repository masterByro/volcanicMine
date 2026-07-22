from rules import RULES
from utils import simulate
from SimResult import SimulationResult


def simulate_all(initial_stability, sim_range: list[int]) -> list[SimulationResult]:
    results: list[SimulationResult] = []
    lower, upper = sim_range

    for A in range(lower, upper + 1, 2):
        print(f"Simulating for A={A}...")
        for B in range(lower, upper + 1, 2):
            for C in range(lower, upper + 1, 2):
                results.append(simulate(A=A, B=B, C=C, STABILITY=initial_stability, rules=RULES))

    return results