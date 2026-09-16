# graph_utils.py
import json
import math
from collections import Counter
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

from SimResult import SimulationResult
from XpUtils import BOULDERS


def _maybe_save_figure(output_path: str | None) -> None:
    if output_path is None:
        return

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=150, bbox_inches="tight")


def graph_stability(result: SimulationResult, output_path: str | None = None, game_end_time: float | None = None):
    """
    Graphs:
    - Stability over time
    - A, B, C vent values over time
    """

    # ------------------
    # Stability timeline
    # ------------------
    stability_times = [0]
    stability_values = [result.initial_stability]

    current_stability = result.initial_stability

    for i, change in enumerate(result.stability_changes):
        current_stability += change
        current_stability = max(0, min(100, current_stability))

        stability_times.append((i + 1) * 15)
        stability_values.append(current_stability)

    # ------------------
    # Vent timeline
    # ------------------
    vent_times = []
    A_values = []
    B_values = []
    C_values = []

    for i, vents in enumerate(result.vent_changes or []):
        vent_times.append((i + 1) * 6)

        A_values.append(vents[0])
        B_values.append(vents[1])
        C_values.append(vents[2])

    # ------------------
    # Plot
    # ------------------
    plt.figure(figsize=(12, 6))

    # Stability
    plt.plot(
        stability_times,
        stability_values,
        label="Stability",
        linewidth=2
    )

    # Vents
    plt.plot(
        vent_times,
        A_values,
        label="A"
    )

    plt.plot(
        vent_times,
        B_values,
        label="B"
    )

    plt.plot(
        vent_times,
        C_values,
        label="C"
    )

    # Max stability line
    plt.axhline(
        y=100,
        color="red",
        linestyle="--",
        label="Max Stability"
    )

    # Death marker
    if result.death_time is not None:
        plt.axvline(
            x=result.death_time,
            color="black",
            linestyle=":",
            label=f"Death ({_format_time_remaining(result.death_time, game_end_time) if game_end_time is not None else str(result.death_time) + 's'})"
        )

    plt.title("Simulation Over Time")
    plt.xlabel("Time remaining" if game_end_time is not None else "Time (seconds)")
    plt.ylabel("Value")

    if game_end_time is None:
        plt.xlim(left=0)
    else:
        _configure_countdown_axis(game_end_time)
    plt.ylim(0, 105)

    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    if output_path is None:
        plt.show()
    else:
        _maybe_save_figure(output_path)
        plt.close()


def graph_final_stability_distribution(results: list[SimulationResult], output_path: str | None = None):
    """
    Plots the distribution of final stability values.

    X-axis: Final Stability (0-100)
    Y-axis: Percentage of simulations ending at that stability.
    """

    if not results:
        raise ValueError("results is empty")

    total = len(results)

    counts = Counter(result.final_stability for result in results)

    x = list(range(101))
    y = [(counts.get(stability, 0) / total) * 100 for stability in x]

    plt.figure(figsize=(12, 6))

    plt.bar(x, y, width=0.9)

    plt.title("Distribution of Final Stability")
    plt.xlabel("Final Stability")
    plt.ylabel("Percentage of Simulations (%)")

    plt.xlim(-0.5, 100.5)
    plt.ylim(bottom=0)

    plt.grid(axis="y")

    plt.tight_layout()
    if output_path is None:
        plt.show()
    else:
        _maybe_save_figure(output_path)
        plt.close()


#Chance of Reaching At Least a Given Final Stability
def graph_cumulative_stability(filename: str, output_path: str | None = None):
    with open(filename, "r") as f:
        results = json.load(f)

    total = len(results)

    # Count how many games finished at each stability
    counts = Counter(r["final_stability"] for r in results)

    x = list(range(101))
    y = []

    # Percentage of games with stability >= current value
    for stability in x:
        surviving = sum(
            count
            for value, count in counts.items()
            if value >= stability
        )
        y.append(100 * surviving / total)

    plt.figure(figsize=(10, 6))
    plt.plot(x, y, linewidth=2)

    if 1 in x and len(y) > 1:
        plt.annotate(
            f"({1}, {y[1]:.1f})",
            xy=(1, y[1]),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.8),
        )

    plt.title("Chance of Reaching At Least a Given Final Stability")
    plt.xlabel("Final Stability")
    plt.ylabel("% of Games")
    plt.xlim(0, 100)
    plt.ylim(0, 100)
    plt.grid(True)

    if output_path is None:
        plt.show()
    else:
        _maybe_save_figure(output_path)
        plt.close()


def graph_game_result_summary(
    results: list[SimulationResult],
    output_path: str | None = None,
    completion_time_offset: float = 0,
    outcome_end_times: list[float] | None = None,
    xp_hr_times: list[float] | None = None,
    game_end_time: float | None = None,
):
    if not results:
        raise ValueError("results is empty")

    final_stabilities = [result.final_stability for result in results]
    max_b5_health = BOULDERS[4]["health"]
    b5_health = [
        result.boulder_health if result.boulder_position == "B5" and result.boulder_health is not None else max_b5_health
        for result in results
    ]
    points = [result.points for result in results]
    xp = [result.xp for result in results]
    caps = [result.flips for result in results]
    vent_checks = [result.vents_checked for result in results]
    xp_with_points = [result.xp_with_points for result in results if result.completion_time is not None]
    if outcome_end_times is None:
        outcome_end_times = [completion_time_offset + result.completion_time for result in results if result.completion_time is not None]
        outcome_results_for_time = [result for result in results if result.completion_time is not None]
    else:
        outcome_results_for_time = results
    if xp_hr_times is None:
        xp_hr_times = outcome_end_times

    xp_hr_values = [
        result.xp_with_points / (xp_hr_time + 34) * 3600
        for result, xp_hr_time in zip(outcome_results_for_time, xp_hr_times)
        if xp_hr_time > 0
    ]
    b5_completed_xp_hr_values = [
        result.xp_with_points / (xp_hr_time + 34) * 3600
        for result, xp_hr_time in zip(outcome_results_for_time, xp_hr_times)
        if xp_hr_time > 0 and result.b5_completed
    ]

    plt.figure(figsize=(14, 16))

    plt.subplot(4, 2, 1)
    plt.hist(final_stabilities, bins=range(0, 102, 2), edgecolor="black")
    plt.title("Full Game Final Stability")
    plt.xlabel("Stability")
    plt.ylabel("Simulations")
    plt.xlim(0, 100)
    plt.grid(axis="y")

    plt.subplot(4, 2, 2)
    if b5_health:
        plt.hist(b5_health, bins=30, edgecolor="black")
    plt.title("B5 Final Health")
    plt.xlabel("Health")
    plt.ylabel("Simulations")
    plt.grid(axis="y")

    plt.subplot(4, 2, 3)
    plt.hist(points, bins=30, edgecolor="black")
    plt.title("Total Points")
    plt.xlabel("Points")
    plt.ylabel("Simulations")
    plt.grid(axis="y")

    plt.subplot(4, 2, 4)
    if outcome_end_times:
        average_time = sum(outcome_end_times) / len(outcome_end_times)
        plt.hist(outcome_end_times, bins=30, edgecolor="black")
        average_label = _format_time_remaining(average_time, game_end_time) if game_end_time is not None else _format_elapsed_time(average_time)
        plt.axvline(average_time, color="red", linestyle="--", label=f"Avg {average_label}")
        if game_end_time is not None:
            plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: _format_time_remaining(value, game_end_time)))
        else:
            plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: _format_elapsed_time(value)))
        plt.legend()
    plt.title("Time In Mine")
    plt.xlabel("Time remaining" if game_end_time is not None else "Time")
    plt.ylabel("Simulations")
    plt.grid(axis="y")

    plt.subplot(4, 2, 5)
    if xp_with_points:
        plt.hist(xp_with_points, bins=30, edgecolor="black")
    plt.title("Exit XP With Points")
    plt.xlabel("XP")
    plt.ylabel("Exited Simulations")
    plt.grid(axis="y")

    plt.subplot(4, 2, 6)
    if xp_hr_values:
        average_xp_hr = sum(xp_hr_values) / len(xp_hr_values)
        plt.hist(xp_hr_values, bins=30, edgecolor="black")
        plt.axvline(average_xp_hr, color="red", linestyle="--", label=f"Overall avg {average_xp_hr:.0f}")
        if b5_completed_xp_hr_values:
            average_b5_xp_hr = sum(b5_completed_xp_hr_values) / len(b5_completed_xp_hr_values)
            plt.axvline(average_b5_xp_hr, color="green", linestyle="--", label=f"B5 avg {average_b5_xp_hr:.0f}")
        plt.legend()
    plt.title("XP/hr")
    plt.xlabel("XP/hr")
    plt.ylabel("Simulations")
    plt.grid(axis="y")

    plt.subplot(4, 2, 7)
    plt.hist(caps, bins=range(min(caps), max(caps) + 2), align="left", edgecolor="black")
    plt.title("Caps/Game")
    plt.xlabel("Caps")
    plt.ylabel("Simulations")
    plt.xticks(range(min(caps), max(caps) + 1))
    plt.grid(axis="y")

    plt.subplot(4, 2, 8)
    plt.hist(vent_checks, bins=range(min(vent_checks), max(vent_checks) + 2), align="left", edgecolor="black")
    plt.title("Vent Checks/Game")
    plt.xlabel("Vent checks")
    plt.ylabel("Simulations")
    plt.xticks(range(min(vent_checks), max(vent_checks) + 1))
    plt.grid(axis="y")

    plt.tight_layout()
    if output_path is None:
        plt.show()
    else:
        _maybe_save_figure(output_path)
        plt.close()


def graph_first_half_sweep_summary(results: list[SimulationResult], output_path: str | None = None):
    if not results:
        raise ValueError("results is empty")

    final_stabilities = [result.final_stability for result in results]
    boulder_positions = [result.boulder_position or "None" for result in results]
    boulder_position_counts = Counter(boulder_positions)
    ordered_boulder_positions = [position for position in ["None", "B1", "B2", "B3", "B4", "B5"] if position in boulder_position_counts]
    points = [result.points for result in results]

    plt.figure(figsize=(14, 9))

    plt.subplot(2, 2, 1)
    plt.hist(final_stabilities, bins=range(0, 102, 2), edgecolor="black")
    plt.title("Half 1 Final Stability")
    plt.xlabel("Stability")
    plt.ylabel("Starts")
    plt.xlim(0, 100)
    plt.grid(axis="y")

    plt.subplot(2, 2, 2)
    plt.hist(points, bins=30, edgecolor="black")
    plt.title("Half 1 Points")
    plt.xlabel("Points")
    plt.ylabel("Starts")
    plt.grid(axis="y")

    plt.subplot(2, 2, 3)
    plt.bar(ordered_boulder_positions, [boulder_position_counts[position] for position in ordered_boulder_positions])
    plt.title("Half 1 Boulder Position")
    plt.xlabel("Position")
    plt.ylabel("Starts")
    plt.grid(axis="y")

    plt.subplot(2, 2, 4)
    plt.hist([result.xp for result in results], bins=30, edgecolor="black")
    plt.title("Half 1 XP")
    plt.xlabel("XP")
    plt.ylabel("Starts")
    plt.grid(axis="y")

    plt.tight_layout()
    if output_path is None:
        plt.show()
    else:
        _maybe_save_figure(output_path)
        plt.close()


def _format_time_remaining(elapsed_seconds: float, game_end_time: float) -> str:
    remaining = max(0, round(game_end_time - elapsed_seconds))
    minutes = remaining // 60
    seconds = remaining % 60
    return f"{minutes}:{seconds:02d}"


def _format_elapsed_time(elapsed_seconds: float) -> str:
    elapsed = max(0, round(elapsed_seconds))
    minutes = elapsed // 60
    seconds = elapsed % 60
    return f"{minutes}:{seconds:02d}"


def _configure_countdown_axis(game_end_time: float | None) -> None:
    if game_end_time is None:
        plt.xlim(left=0)
        return

    ticks = list(range(0, math.ceil(game_end_time) + 1, 15))
    plt.xlim(0, game_end_time)
    plt.xticks(ticks, [_format_time_remaining(tick, game_end_time) for tick in ticks], rotation=45, ha="right")


def _plot_death_counts(death_times: list[float]) -> None:
    counts = Counter(death_times)
    times = sorted(counts)
    plt.bar(times, [counts[time] for time in times], width=10, align="center", edgecolor="black")


def graph_full_game_sweep_deaths(
    games: list[dict],
    second_half_offset: float,
    game_end_time: float | None = None,
    last_stability_update: float | None = None,
    output_path: str | None = None,
):
    death_times = []

    for game in games:
        first_half = game["first_half"]
        if first_half.death_time is not None:
            death_times.append(first_half.death_time)
        else:
            death_times.extend(
                second_half_offset + result.death_time
                for result in game["second_half_results"]
                if result.death_time is not None
            )

    plt.figure(figsize=(12, 6))
    if death_times:
        _plot_death_counts(death_times)
    else:
        plt.text(0.5, 0.5, "No deaths for this sweep", ha="center", va="center", transform=plt.gca().transAxes)

    plt.axvline(second_half_offset, color="black", linestyle="--", label="5 minute reset")
    if last_stability_update is not None:
        plt.axvline(last_stability_update, color="red", linestyle=":", label="last stability update")
    if game_end_time is not None:
        plt.axvline(game_end_time, color="gray", linestyle="--", label="game end")
    plt.title("Deaths on Full Game Timeline")
    plt.xlabel("Time remaining")
    plt.ylabel("Deaths")
    _configure_countdown_axis(game_end_time)
    plt.grid(axis="y")
    plt.legend()
    plt.tight_layout()

    if output_path is None:
        plt.show()
    else:
        _maybe_save_figure(output_path)
        plt.close()


def graph_full_game_outcome_deaths(
    outcomes: list[tuple[SimulationResult, float]],
    second_half_offset: float,
    game_end_time: float | None = None,
    last_stability_update: float | None = None,
    output_path: str | None = None,
):
    death_times = [end_time for result, end_time in outcomes if result.death_time is not None]

    plt.figure(figsize=(12, 6))
    if death_times:
        _plot_death_counts(death_times)
    else:
        plt.text(0.5, 0.5, "No deaths for this sweep", ha="center", va="center", transform=plt.gca().transAxes)

    plt.axvline(second_half_offset, color="black", linestyle="--", label="5 minute reset")
    if last_stability_update is not None:
        plt.axvline(last_stability_update, color="red", linestyle=":", label="last stability update")
    if game_end_time is not None:
        plt.axvline(game_end_time, color="gray", linestyle="--", label="game end")
    plt.title("Deaths on Full Game Timeline")
    plt.xlabel("Time remaining")
    plt.ylabel("Full-game outcomes")
    _configure_countdown_axis(game_end_time)
    plt.grid(axis="y")
    plt.legend()
    plt.tight_layout()

    if output_path is None:
        plt.show()
    else:
        _maybe_save_figure(output_path)
        plt.close()


def graph_full_game_deaths(
    first_half: SimulationResult,
    second_half_results: list[SimulationResult],
    second_half_offset: float,
    game_end_time: float | None = None,
    last_stability_update: float | None = None,
    output_path: str | None = None,
):
    death_times = []

    if first_half.death_time is not None:
        death_times.append(first_half.death_time)
    else:
        death_times.extend(
            second_half_offset + result.death_time
            for result in second_half_results
            if result.death_time is not None
        )

    plt.figure(figsize=(12, 6))
    if death_times:
        x_limit = game_end_time or math.ceil(max(death_times))
        bins = range(0, math.ceil(x_limit) + 16, 15)
        plt.hist(death_times, bins=bins, edgecolor="black")
    else:
        plt.text(0.5, 0.5, "No deaths for this starter/sweep", ha="center", va="center", transform=plt.gca().transAxes)

    plt.axvline(second_half_offset, color="black", linestyle="--", label="5 minute reset")
    if last_stability_update is not None:
        plt.axvline(last_stability_update, color="red", linestyle=":", label="last stability update")
    if game_end_time is not None:
        plt.axvline(game_end_time, color="gray", linestyle="--", label="game end")
    plt.title("Deaths on Full Game Timeline")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Deaths")
    plt.xlim(0, game_end_time or None)
    plt.grid(axis="y")
    plt.legend()
    plt.tight_layout()

    if output_path is None:
        plt.show()
    else:
        _maybe_save_figure(output_path)
        plt.close()