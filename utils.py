import math
import random

from rulesUtils import apply_action
from SimResult import SimulationResult


def simulate(A: int, B: int, C: int, STABILITY: int, rules: list, time_limit: int) -> SimulationResult:
    isVerbose = True

    initial_A = A
    initial_B = B
    initial_C = C
    initial_stability = STABILITY
    lowest_stability = STABILITY
    stability_changes = []
    vent_changes = []
    death_time = None

    # Nothing changes state except rule times, vent ticks (every 6) and
    # stability ticks (every 15), so only those timesteps need visiting
    # instead of every single tick from 1..time_limit.
    if time_limit >= 1 and STABILITY <= 0:
        death_time = 1
    elif time_limit >= 1:
        rules_by_time: dict[int, list] = {}
        for rule in rules:
            rules_by_time.setdefault(rule["time"], []).append(rule)

        event_times = set(rules_by_time)
        event_times.update(range(6, time_limit + 1, 6))
        event_times.update(range(15, time_limit + 1, 15))

        rand = random.randint(0, 1)
        for i in sorted(t for t in event_times if 1 <= t <= time_limit):
            for rule in rules_by_time.get(i, ()):
                if rule["condition"](A, B, C, STABILITY):
                    A, B, C = apply_action(rule["action"], A, B, C)

            # Update vent
            if i % 6 == 0:
                A, B, C = update_vents(A, B, C)

                if isVerbose:
                    vent_changes.append([A, B, C])

            # Update Stability
            if i % 15 == 0:
                change = calculate_stability(A, B, C) + rand
                rand = 1 if rand == 0 else 0
                stability_changes.append(change)
                STABILITY += change
                STABILITY = max(0, min(100, STABILITY))
                lowest_stability = min(lowest_stability, STABILITY)

                if STABILITY <= 0:
                    death_time = i
                    break

    # Create and return the simulation result
    return SimulationResult(
        initial_A=initial_A,
        initial_B=initial_B,
        initial_C=initial_C,
        initial_stability=initial_stability,
        lowest_stability=lowest_stability,
        final_stability=STABILITY,
        death_time=death_time,
        stability_changes=stability_changes,
        vent_changes=vent_changes if isVerbose else None
    )


def isInFreezeRange(val: int) -> bool:
    return val >= 41 and val <= 59

def vent_score(value: int) -> int:
    return math.ceil((50 - abs(50 - value)) / 3)

def calculate_stability(A: int, B: int, C: int) -> int:
    a = vent_score(A)
    b = vent_score(B)
    c = vent_score(C)

    return -25 + a + b + c


def update_vents(A: int, B: int, C: int) -> tuple[int, int, int]:
    """
    Updates all three vents.

    Update order:
        1. C
        2. B
        3. A

    Rules:
        - All vents move 2 by default.
        - A vent in the 41-59 range moves 1 instead.
        - If A is in 41-59, B and C each move 1 less.
        - If B is in 41-59, C moves 1 less.
        - Movement is floored at 0.
    """

    # ----- Update C -----
    c_move = 1 if isInFreezeRange(C) else 2

    if isInFreezeRange(A):
        c_move -= 1

    if isInFreezeRange(B):
        c_move -= 1

    c_move = max(0, c_move)
    C = max(0, C - c_move)

    # ----- Update B -----
    b_move = 1 if isInFreezeRange(B) else 2

    if isInFreezeRange(A):
        b_move -= 1

    b_move = max(0, b_move)
    B = max(0, B - b_move)

    # ----- Update A -----
    a_move = 1 if isInFreezeRange(A) else 2

    a_move = max(0, a_move)
    A = max(0, A - a_move)

    return A, B, C