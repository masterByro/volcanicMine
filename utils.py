import math
import random

from rulesUtils import apply_action
from SimResult import SimulationResult
from XpUtils import BOULDERS, CAP_PTS, CHECK_PTS, FINISH_PTS, PROSPECTORS, XP_PER_POINT

TICK_SECONDS = 0.6
EXIT_TIME_SECONDS = 32
EXIT_EPSILON_SECONDS = 0.001

# Boulders are mined in this fixed order; stage N mines at position "B{N}".
BOULDER_POSITIONS = ["B1", "B2", "B3", "B4", "B5"]

# Direct travel time (ticks) between boulders when no player rule overrides it.
DEFAULT_TRAVEL_TICKS = {
    ("start", "B1"): 20,
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

    if target_tick <= start_tick:
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
    elif action["type"] == "cap":
        counters["flips"] += 1
        counters["points"] += CAP_PTS
    elif action["type"] == "flip":
        state["A"], state["B"], state["C"] = apply_action(action, state["A"], state["B"], state["C"])
        counters["flips"] += 1
        counters["points"] += CAP_PTS


def _trigger_matches(
    trigger: dict,
    state: dict,
    current_tick: float | None = None,
    clock_limit: int | None = None,
    rules_by_time: dict | None = None,
    time_limit: int | None = None,
    player_rules: list | None = None,
) -> bool:
    condition = trigger.get("condition")
    if condition is not None and not condition(state["A"], state["B"], state["C"], state["STABILITY"]):
        return False

    if "time_remaining_less_than" in trigger:
        if current_tick is None or clock_limit is None:
            return False
        if clock_limit - current_tick >= trigger["time_remaining_less_than"]:
            return False

    if "not_enough_time_for_boulder" in trigger:
        if current_tick is None or clock_limit is None:
            return False
        boulder_name = trigger["not_enough_time_for_boulder"]
        if boulder_name not in BOULDER_POSITIONS:
            return False
        boulder = BOULDERS[BOULDER_POSITIONS.index(boulder_name)]
        exit_start_time = _get_exit_start_time(player_rules or [], clock_limit, state, rules_by_time, current_tick, time_limit) if rules_by_time is not None and time_limit is not None else None
        available_time = (exit_start_time if exit_start_time is not None else clock_limit - EXIT_TIME_SECONDS) - current_tick
        if available_time >= boulder["time"]:
            return False

    return True


def _find_matching_travel_rules(player_rules: list, frm: str, to: str, current_tick: float, boulders_completed: int, state: dict, clock_limit: int):
    matching_rules = []

    for rule in player_rules:
        travel = rule.get("travel")
        if not travel or travel["from"] != frm or travel["to"] != to:
            continue

        trigger = rule["trigger"]
        if "time" in trigger:
            if current_tick == trigger["time"] and _trigger_matches(trigger, state, current_tick, clock_limit):
                matching_rules.append(rule)
        elif "after_boulder" in trigger:
            if boulders_completed != trigger["after_boulder"]:
                continue
            if _trigger_matches(trigger, state, current_tick, clock_limit):
                matching_rules.append(rule)

    return matching_rules


def _find_post_boulder_rules(player_rules: list, boulders_completed: int, state: dict, current_tick: float, clock_limit: int, phase: str, rules_by_time: dict, time_limit: int):
    matching_rules = []

    for rule in player_rules:
        if rule.get("travel") or rule.get("action", {}).get("type") == "exit":
            continue

        trigger = rule.get("trigger", {})
        if trigger.get("after_boulder") != boulders_completed:
            continue
        if trigger.get("phase", "after_boulder") != phase:
            continue

        if _trigger_matches(trigger, state, current_tick, clock_limit, rules_by_time, time_limit, player_rules):
            matching_rules.append(rule)

    return matching_rules


def _predict_blowup_time(state: dict, rules_by_time: dict, current_tick: float, time_limit: int) -> float | None:
    predictor_state = {
        "A": state["A"],
        "B": state["B"],
        "C": state["C"],
        "STABILITY": state["STABILITY"],
        "lowest_stability": state["lowest_stability"],
        "stability_changes": [],
        "vent_changes": [],
        "death_time": None,
        "rand": state["rand"],
    }

    _advance_environment(predictor_state, rules_by_time, current_tick, time_limit, time_limit)
    return predictor_state["death_time"]


def predict_mine_blowup_time(A: int, B: int, C: int, STABILITY: int, rules: list, time_limit: int, rand: int = 0, start_tick: float = 0) -> float | None:
    rules_by_time: dict[int, list] = {}
    for rule in rules:
        if "trigger" not in rule:
            rules_by_time.setdefault(rule["time"], []).append(rule)

    state = {
        "A": A,
        "B": B,
        "C": C,
        "STABILITY": STABILITY,
        "lowest_stability": STABILITY,
        "stability_changes": [],
        "vent_changes": [],
        "death_time": None,
        "rand": rand,
    }

    return _predict_blowup_time(state, rules_by_time, start_tick, time_limit)


def _get_exit_start_time(player_rules: list, clock_limit: int, state: dict | None = None, rules_by_time: dict | None = None, current_tick: float = 0, time_limit: int | None = None) -> float | None:
    for rule in player_rules:
        if rule.get("action", {}).get("type") != "exit":
            continue

        trigger = rule.get("trigger", {})
        if "time_left" in trigger:
            return clock_limit - trigger["time_left"]

        if "predicted_blowup_buffer" in trigger and state is not None and rules_by_time is not None and time_limit is not None:
            blowup_time = _predict_blowup_time(state, rules_by_time, current_tick, time_limit)
            if blowup_time is not None:
                return max(current_tick, blowup_time - trigger["predicted_blowup_buffer"] - EXIT_EPSILON_SECONDS)
            return max(current_tick, clock_limit - EXIT_TIME_SECONDS)

    return None


def _keep_earliest_exit_start(existing_exit_start_time: float | None, next_exit_start_time: float | None) -> float | None:
    if next_exit_start_time is None:
        return existing_exit_start_time
    if existing_exit_start_time is None:
        return next_exit_start_time
    return min(existing_exit_start_time, next_exit_start_time)


def _exit_mine(state: dict, rules_by_time: dict, current_tick: float, time_limit: int, clock_limit: int) -> tuple[float, float | None]:
    exit_end_tick = current_tick + EXIT_TIME_SECONDS
    target_tick = min(exit_end_tick, clock_limit)
    exit_can_complete = exit_end_tick <= clock_limit
    if exit_can_complete:
        target_tick -= EXIT_EPSILON_SECONDS

    reached_tick = _advance_environment(state, rules_by_time, current_tick, target_tick, time_limit)
    if state["death_time"] is not None and state["death_time"] >= exit_end_tick:
        if state["stability_changes"]:
            state["STABILITY"] = max(0, min(100, state["STABILITY"] - state["stability_changes"].pop()))
        state["death_time"] = None
        return exit_end_tick, exit_end_tick

    if state["death_time"] is None and reached_tick >= exit_end_tick:
        return reached_tick, reached_tick

    if state["death_time"] is None and exit_can_complete:
        return exit_end_tick, exit_end_tick

    return reached_tick, None


def _get_post_b5_exit_start_time(player_rules: list, clock_limit: int, state: dict, rules_by_time: dict, current_tick: float, time_limit: int) -> float:
    predicted_exit_start = _get_exit_start_time(player_rules, clock_limit, state, rules_by_time, current_tick, time_limit)
    clock_exit_start = max(current_tick, clock_limit - EXIT_TIME_SECONDS)

    if predicted_exit_start is None:
        return clock_exit_start

    return min(predicted_exit_start, clock_exit_start)


def _run_post_boulder_actions(player_rules: list, boulders_completed: int, state: dict, rules_by_time: dict, counters: dict, current_tick: float, time_limit: int, clock_limit: int, phase: str = "after_boulder") -> float:
    for rule in _find_post_boulder_rules(player_rules, boulders_completed, state, current_tick, clock_limit, phase, rules_by_time, time_limit):
        action = rule["action"]
        if action["type"] == "wait_reset":
            current_tick = _advance_environment(state, rules_by_time, current_tick, current_tick + _ticks_to_seconds(rule["time"].get("duration", 0)), time_limit)
            if state["death_time"] is not None:
                return current_tick

            cap_duration = _ticks_to_seconds(action.get("cap_duration", 0))
            for _ in range(action.get("caps", 0)):
                if counters["flips"] >= action.get("max_per_game", 6) or current_tick + cap_duration > clock_limit:
                    break
                current_tick = _advance_environment(state, rules_by_time, current_tick, current_tick + cap_duration, time_limit)
                if state["death_time"] is not None:
                    return current_tick
                _apply_player_action({"type": "cap"}, state, counters)

            state["player_position"] = action["position"]
            state["player_position_delay"] = max(0.0, current_tick - clock_limit)
            return _advance_environment(state, rules_by_time, current_tick, clock_limit, time_limit)

        max_repeats = action.get("max_per_game", 1)
        repeats = max(0, max_repeats - counters["flips"]) if action["type"] == "cap" else max_repeats
        duration = _ticks_to_seconds(rule["time"]["duration"])

        for _ in range(repeats):
            exit_start_time = _get_post_b5_exit_start_time(player_rules, clock_limit, state, rules_by_time, current_tick, time_limit)
            action_end_tick = current_tick + duration
            if action_end_tick > exit_start_time:
                break

            current_tick = _advance_environment(state, rules_by_time, current_tick, action_end_tick, time_limit)
            if state["death_time"] is not None:
                return current_tick

            _apply_player_action(action, state, counters)

    return current_tick


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
    starting_player_position: str | None = None,
    starting_player_position_delay: float = 0.0,
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
        "player_position": starting_player_position,
        "player_position_delay": starting_player_position_delay,
    }
    counters = {
        "vents_checked": starting_vents_checked,
        "flips": starting_flips,
        "points": starting_points,
        "xp": starting_xp,
    }
    boulder_position = starting_boulder_position
    boulder_health = starting_boulder_health
    exit_start_time = None
    completion_time = None
    b5_completed_time = None
    b5_completed = False
    exit_attempted = False

    # Old-style rules fire at a fixed absolute tick; new-style (player) rules
    # describe a travel/mining detour triggered by time or boulder completion.
    old_style_rules = [rule for rule in rules if "trigger" not in rule]
    player_rules = [rule for rule in rules if "trigger" in rule]

    rules_by_time: dict[int, list] = {}
    for rule in old_style_rules:
        rules_by_time.setdefault(rule["time"], []).append(rule)

    starts_player_path = any(
        rule.get("action", {}).get("type") != "exit" and rule.get("trigger", {}).get("time") == 0
        for rule in player_rules
    )
    should_track_player = bool(starts_player_path or starting_boulder_position or clock_limit == time_limit)

    if clock_limit >= 1 and STABILITY <= 0:
        state["death_time"] = 1
    elif clock_limit >= 1 and should_track_player:
        current_tick = 0
        current_position = "start"
        first_boulder_index = 0
        starting_health_for_current_boulder = None

        if starting_player_position == "A_RESET":
            current_position = "A_RESET"
            current_tick = starting_player_position_delay
            first_boulder_index = BOULDER_POSITIONS.index("B4")
            boulders_completed = 3
        elif starting_boulder_position in BOULDER_POSITIONS:
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

        if boulders_completed >= len(BOULDER_POSITIONS):
            boulder_position = BOULDER_POSITIONS[-1]
            boulder_health = 0
            b5_completed = True
            b5_completed_time = 0
            current_tick = _run_post_boulder_actions(player_rules, 5, state, rules_by_time, counters, current_tick, time_limit, clock_limit)
            if state["death_time"] is None:
                exit_start_time = current_tick
                current_tick, completion_time = _exit_mine(state, rules_by_time, current_tick, time_limit, clock_limit)

        for boulder_index in range(first_boulder_index, len(BOULDER_POSITIONS)):
            if current_tick >= clock_limit or state["death_time"] is not None:
                break

            to = BOULDER_POSITIONS[boulder_index]
            needs_travel = current_position != to
            exit_start_time = _keep_earliest_exit_start(exit_start_time, _get_exit_start_time(player_rules, clock_limit, state, rules_by_time, current_tick, time_limit))

            if needs_travel:
                rules_for_travel = _find_matching_travel_rules(player_rules, current_position, to, current_tick, boulders_completed, state, clock_limit)
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
                    if action_tick > clock_limit or (exit_start_time is not None and action_tick > exit_start_time):
                        break

                    current_tick = _advance_environment(state, rules_by_time, current_tick, action_tick, time_limit)
                    action_condition = rule.get("condition")
                    if state["death_time"] is None and (action_condition is None or action_condition(state["A"], state["B"], state["C"], state["STABILITY"])):
                        _apply_player_action(rule["action"], state, counters)
                    elif state["death_time"] is not None:
                        break

                if state["death_time"] is None:
                    before_post_actions = current_tick
                    current_tick = _run_post_boulder_actions(player_rules, boulders_completed, state, rules_by_time, counters, current_tick, time_limit, clock_limit, phase="after_actions")
                    end_tick += current_tick - before_post_actions

                if exit_start_time is not None and current_tick <= exit_start_time < end_tick:
                    end_tick = exit_start_time

                current_tick = _advance_environment(state, rules_by_time, current_tick, min(end_tick, clock_limit), time_limit)

                if current_tick >= clock_limit or state["death_time"] is not None:
                    break

                current_tick = _run_post_boulder_actions(player_rules, boulders_completed, state, rules_by_time, counters, current_tick, time_limit, clock_limit, phase="after_travel")
                if state["death_time"] is not None:
                    break

            exit_start_time = _keep_earliest_exit_start(exit_start_time, _get_exit_start_time(player_rules, clock_limit, state, rules_by_time, current_tick, time_limit))
            if exit_start_time is not None and current_tick >= exit_start_time:
                exit_start_time = current_tick
                exit_attempted = True
                current_tick, completion_time = _exit_mine(state, rules_by_time, current_tick, time_limit, clock_limit)
                break

            # Mine the boulder at this position.
            boulder_position = to
            boulder = BOULDERS[boulder_index]
            starting_health = starting_health_for_current_boulder or boulder["health"]
            duration = boulder["time"] * starting_health / boulder["health"]
            mine_start_tick = current_tick
            mine_end_tick = mine_start_tick + duration
            exit_start_time = _keep_earliest_exit_start(exit_start_time, _get_exit_start_time(player_rules, clock_limit, state, rules_by_time, current_tick, time_limit))
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
                exit_start_time = current_tick
                exit_attempted = True
                current_tick, completion_time = _exit_mine(state, rules_by_time, current_tick, time_limit, clock_limit)
                break

            if elapsed < duration:
                break

            if state["death_time"] is None and elapsed >= duration:
                boulders_completed += 1
                current_position = to
                starting_health_for_current_boulder = None

                if boulder_index == len(BOULDER_POSITIONS) - 1:
                    b5_completed_time = current_tick
                    b5_completed = True
                    counters["points"] += FINISH_PTS
                    current_tick = _run_post_boulder_actions(player_rules, boulders_completed, state, rules_by_time, counters, current_tick, time_limit, clock_limit)
                    if state["death_time"] is not None:
                        break
                    exit_start_time = current_tick
                    exit_attempted = True
                    current_tick, completion_time = _exit_mine(state, rules_by_time, current_tick, time_limit, clock_limit)
                    break

                current_tick = _run_post_boulder_actions(player_rules, boulders_completed, state, rules_by_time, counters, current_tick, time_limit, clock_limit)
                if state["death_time"] is not None:
                    break

        if completion_time is None and not exit_attempted:
            _advance_environment(state, rules_by_time, current_tick, time_limit, time_limit)
    elif clock_limit >= 1:
        _advance_environment(state, rules_by_time, 0, time_limit, time_limit)

    if exit_start_time is not None and completion_time is None:
        exit_end_time = exit_start_time + EXIT_TIME_SECONDS
        if state["death_time"] is None or state["death_time"] >= exit_end_time:
            completion_time = exit_end_time
            if state["death_time"] is not None:
                if state["stability_changes"]:
                    state["STABILITY"] = max(0, min(100, state["STABILITY"] - state["stability_changes"].pop()))
                state["death_time"] = None

    # Create and return the simulation result
    xp_with_points = counters["xp"]
    if b5_completed and b5_completed_time is None:
        b5_completed_time = 0
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
        player_position=state["player_position"],
        player_position_delay=state["player_position_delay"],
        boulder_position=boulder_position,
        boulder_health=boulder_health,
        points=round(counters["points"], 2),
        xp=round(counters["xp"], 2),
        xp_with_points=round(xp_with_points, 2),
        exit_start_time=exit_start_time,
        completion_time=completion_time,
        b5_completed=b5_completed,
        b5_completed_time=b5_completed_time,
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