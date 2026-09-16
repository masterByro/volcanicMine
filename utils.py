import math
import random

from rulesUtils import apply_action
from SimResult import SimulationResult
from XpUtils import BOULDERS, CAP_PTS, CHECK_PTS, FINISH_PTS, PROSPECTORS, XP_PER_POINT

TICK_SECONDS = 0.6
EXIT_TIME_SECONDS = 32

# Boulders are mined in this fixed order; stage N mines at position "B{N}".
BOULDER_POSITIONS = ["B1", "B2", "B3", "B4", "B5"]

# Direct travel time (ticks) between boulders when no player rule overrides it.
DEFAULT_TRAVEL_TICKS = {
    ("B1", "B2"): 15,
    ("B2", "B3"): 18,
    ("B3", "B4"): 26,
    ("B4", "B5"): 28,
}


def _ticks_to_seconds(ticks: float) -> float:
    return ticks * TICK_SECONDS


def _advance_environment(state: dict, rules_by_time: dict, start_tick: float, target_tick: float, time_limit: int) -> float:
    """Runs the vent/stability tick engine (and any old-style timed rules) from
    start_tick (exclusive) to target_tick (inclusive), stopping early on death.
    Returns the tick actually reached."""

    if state["death_time"] is not None:
        return start_tick

    event_limit = min(target_tick, time_limit)
    if event_limit <= start_tick:
        return target_tick

    target_event_time = math.floor(event_limit)
    event_times = {t for t in rules_by_time if start_tick < t <= event_limit}
    event_times.update(range(((math.floor(start_tick) // 6) + 1) * 6, target_event_time + 1, 6))
    event_times.update(range(((math.floor(start_tick) // 15) + 1) * 15, target_event_time + 1, 15))

    for i in sorted(event_times):
        for rule in rules_by_time.get(i, ()):
            if rule["condition"](state["A"], state["B"], state["C"], state["STABILITY"]):
                state["A"], state["B"], state["C"] = apply_action(rule["action"], state["A"], state["B"], state["C"])

        if i % 6 == 0:
            state["A"], state["B"], state["C"] = update_vents(state["A"], state["B"], state["C"])
            state["vent_changes"].append([state["A"], state["B"], state["C"]])

        if i % 15 == 0:
            change = calculate_stability(state["A"], state["B"], state["C"]) + state["rand"]
            state["rand"] = 1 if state["rand"] == 0 else 0
            state["stability_changes"].append(change)
            state["STABILITY"] += change
            state["STABILITY"] = max(0, min(100, state["STABILITY"]))
            state["lowest_stability"] = min(state["lowest_stability"], state["STABILITY"])

            if state["STABILITY"] <= 0:
                state["death_time"] = i
                return i

    return target_tick


def _apply_player_action(action: dict, state: dict, counters: dict) -> None:
    if action["type"] == "vent":
        counters["vents_checked"] += 1
        counters["points"] += CHECK_PTS
    elif action["type"] == "flip":
        state["A"], state["B"], state["C"] = apply_action(action, state["A"], state["B"], state["C"])
        counters["flips"] += 1
        counters["points"] += CAP_PTS


def _find_matching_travel_rules(player_rules: list, frm: str, to: str, current_tick: float, boulders_completed: int, state: dict):
    matching_rules = []

    for rule in player_rules:
        travel = rule.get("travel")
        if not travel or travel["from"] != frm or travel["to"] != to:
            continue

        trigger = rule["trigger"]
        if "time" in trigger:
            if current_tick == trigger["time"]:
                matching_rules.append(rule)
        elif "after_boulder" in trigger:
            if boulders_completed != trigger["after_boulder"]:
                continue
            condition = trigger.get("condition")
            if condition is None or condition(state["A"], state["B"], state["C"], state["STABILITY"]):
                matching_rules.append(rule)

    return matching_rules


def _get_exit_start_time(player_rules: list, time_limit: int) -> float | None:
    for rule in player_rules:
        if rule.get("action", {}).get("type") != "exit":
            continue

        trigger = rule.get("trigger", {})
        if "time_left" in trigger:
            return time_limit - trigger["time_left"]

    return None


def _exit_mine(state: dict, rules_by_time: dict, current_tick: float, time_limit: int, clock_limit: int) -> tuple[float, float | None]:
    exit_end_tick = current_tick + EXIT_TIME_SECONDS
    reached_tick = _advance_environment(state, rules_by_time, current_tick, min(exit_end_tick, clock_limit), time_limit)
    if state["death_time"] is None and reached_tick >= exit_end_tick:
        return reached_tick, reached_tick

    return reached_tick, None


def simulate(
    A: int,
    B: int,
    C: int,
    STABILITY: int,
    rules: list,
    time_limit: int,
    starting_boulder_position: str | None = None,
    starting_boulder_health: float | None = None,
    starting_vents_checked: int = 0,
    starting_flips: int = 0,
    starting_points: float = 0.0,
    starting_xp: float = 0.0,
    clock_limit: int | None = None,
) -> SimulationResult:
    isVerbose = True
    if clock_limit is None:
        clock_limit = time_limit

    initial_A = A
    initial_B = B
    initial_C = C
    initial_stability = STABILITY

    state = {
        "A": A,
        "B": B,
        "C": C,
        "STABILITY": STABILITY,
        "lowest_stability": STABILITY,
        "stability_changes": [],
        "vent_changes": [],
        "death_time": None,
        "rand": random.randint(0, 1) if clock_limit >= 1 else 0,
    }
    counters = {
        "vents_checked": starting_vents_checked,
        "flips": starting_flips,
        "points": starting_points,
        "xp": starting_xp,
    }
    boulder_position = starting_boulder_position
    boulder_health = starting_boulder_health
    completion_time = None

    # Old-style rules fire at a fixed absolute tick; new-style (player) rules
    # describe a travel/mining detour triggered by time or boulder completion.
    old_style_rules = [rule for rule in rules if "trigger" not in rule]
    player_rules = [rule for rule in rules if "trigger" in rule]
    exit_start_time = _get_exit_start_time(player_rules, clock_limit)

    rules_by_time: dict[int, list] = {}
    for rule in old_style_rules:
        rules_by_time.setdefault(rule["time"], []).append(rule)

    starts_player_path = any(
        rule.get("action", {}).get("type") != "exit" and rule.get("trigger", {}).get("time") == 0
        for rule in player_rules
    )
    should_track_player = bool(starts_player_path or starting_boulder_position)

    if clock_limit >= 1 and STABILITY <= 0:
        state["death_time"] = 1
    elif clock_limit >= 1 and should_track_player:
        current_tick = 0
        current_position = "start"
        first_boulder_index = 0
        starting_health_for_current_boulder = None

        if starting_boulder_position in BOULDER_POSITIONS:
            boulder_index = BOULDER_POSITIONS.index(starting_boulder_position)
            current_position = starting_boulder_position
            carried_health = starting_boulder_health if starting_boulder_health is not None else 0

            if carried_health > 0:
                first_boulder_index = boulder_index
                starting_health_for_current_boulder = carried_health
                boulders_completed = boulder_index
            else:
                first_boulder_index = boulder_index + 1
                boulders_completed = boulder_index + 1
        else:
            boulders_completed = 0

        for boulder_index in range(first_boulder_index, len(BOULDER_POSITIONS)):
            if current_tick >= clock_limit or state["death_time"] is not None:
                break

            to = BOULDER_POSITIONS[boulder_index]
            needs_travel = current_position != to

            if needs_travel:
                rules_for_travel = _find_matching_travel_rules(player_rules, current_position, to, current_tick, boulders_completed, state)
                if rules_for_travel:
                    action_events = sorted(
                        [(current_tick + _ticks_to_seconds(rule["time"]["action"]), rule) for rule in rules_for_travel],
                        key=lambda event: event[0]
                    )
                    end_tick = max(current_tick + _ticks_to_seconds(rule["time"]["end"]) for rule in rules_for_travel)
                else:
                    action_events = []
                    end_tick = current_tick + _ticks_to_seconds(DEFAULT_TRAVEL_TICKS[(current_position, to)])

                for action_tick, rule in action_events:
                    if action_tick > clock_limit:
                        break

                    current_tick = _advance_environment(state, rules_by_time, current_tick, action_tick, time_limit)
                    if state["death_time"] is None:
                        _apply_player_action(rule["action"], state, counters)
                    else:
                        break

                current_tick = _advance_environment(state, rules_by_time, current_tick, min(end_tick, clock_limit), time_limit)

                if current_tick >= clock_limit or state["death_time"] is not None:
                    break

            if exit_start_time is not None and current_tick >= exit_start_time:
                current_tick, completion_time = _exit_mine(state, rules_by_time, current_tick, time_limit, clock_limit)
                break

            # Mine the boulder at this position.
            boulder_position = to
            boulder = BOULDERS[boulder_index]
            starting_health = starting_health_for_current_boulder or boulder["health"]
            duration = boulder["time"] * starting_health / boulder["health"]
            mine_start_tick = current_tick
            mine_end_tick = mine_start_tick + duration
            if exit_start_time is not None and current_tick <= exit_start_time < mine_end_tick:
                mine_end_tick = exit_start_time
            mine_end_tick = min(mine_end_tick, clock_limit)

            current_tick = _advance_environment(state, rules_by_time, current_tick, mine_end_tick, time_limit)

            elapsed = current_tick - mine_start_tick
            mined_fraction = min(1.0, elapsed / duration)
            health_mined = starting_health * mined_fraction
            boulder_health = round(starting_health - health_mined, 2)
            counters["points"] += boulder["points"] * health_mined / boulder["health"]
            counters["xp"] += boulder["xp"] * health_mined / boulder["health"]

            if state["death_time"] is None and exit_start_time is not None and current_tick >= exit_start_time and elapsed < duration:
                current_tick, completion_time = _exit_mine(state, rules_by_time, current_tick, time_limit, clock_limit)
                break

            if state["death_time"] is None and elapsed >= duration:
                boulders_completed += 1
                current_position = to
                starting_health_for_current_boulder = None

                if boulder_index == len(BOULDER_POSITIONS) - 1:
                    counters["points"] += FINISH_PTS
                    current_tick, completion_time = _exit_mine(state, rules_by_time, current_tick, time_limit, clock_limit)
                    break

        if completion_time is None:
            _advance_environment(state, rules_by_time, current_tick, time_limit, time_limit)
    elif clock_limit >= 1:
        _advance_environment(state, rules_by_time, 0, time_limit, time_limit)

    # Create and return the simulation result
    xp_with_points = counters["xp"]
    if completion_time is not None:
        xp_with_points += counters["points"] * XP_PER_POINT * (1 + PROSPECTORS)

    return SimulationResult(
        initial_A=initial_A,
        initial_B=initial_B,
        initial_C=initial_C,
        initial_stability=initial_stability,
        lowest_stability=state["lowest_stability"],
        final_stability=state["STABILITY"],
        death_time=state["death_time"],
        stability_changes=state["stability_changes"],
        vent_changes=state["vent_changes"] if isVerbose else None,
        vents_checked=counters["vents_checked"],
        flips=counters["flips"],
        boulder_position=boulder_position,
        boulder_health=boulder_health,
        points=round(counters["points"], 2),
        xp=round(counters["xp"], 2),
        xp_with_points=round(xp_with_points, 2),
        completion_time=completion_time,
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