# graph_utils.py
import json
import math
from collections import Counter
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

from SimResult import SimulationResult


def _maybe_save_figure(output_path: str | None) -> None:
    if output_path is None:
        return

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=150, bbox_inches="tight")


def graph_stability(result: SimulationResult, output_path: str | None = None):
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
            label=f"Death ({result.death_time}s)"
        )

    plt.title("Simulation Over Time")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Value")

    plt.xlim(left=0)
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


def graph_game_result_summary(results: list[SimulationResult], output_path: str | None = None, completion_time_offset: float = 0):
    if not results:
        raise ValueError("results is empty")

    positions = [result.boulder_position or "None" for result in results]
    position_counts = Counter(positions)
    ordered_positions = [position for position in ["None", "B1", "B2", "B3", "B4", "B5"] if position in position_counts]

    final_stabilities = [result.final_stability for result in results]
    points = [result.points for result in results]
    xp = [result.xp for result in results]
    xp_with_points = [result.xp_with_points for result in results if result.completion_time is not None]
    completion_times = [completion_time_offset + result.completion_time for result in results if result.completion_time is not None]

    plt.figure(figsize=(14, 12))

    plt.subplot(3, 2, 1)
    plt.hist(final_stabilities, bins=range(0, 102, 2), edgecolor="black")
    plt.title("Full Game Final Stability")
    plt.xlabel("Stability")
    plt.ylabel("Simulations")
    plt.xlim(0, 100)
    plt.grid(axis="y")

    plt.subplot(3, 2, 2)
    plt.bar(ordered_positions, [position_counts[position] for position in ordered_positions])
    plt.title("Final Boulder Position")
    plt.xlabel("Position")
    plt.ylabel("Simulations")
    plt.grid(axis="y")

    plt.subplot(3, 2, 3)
    plt.hist(points, bins=30, edgecolor="black")
    plt.title("Total Points")
    plt.xlabel("Points")
    plt.ylabel("Simulations")
    plt.grid(axis="y")

    plt.subplot(3, 2, 4)
    plt.hist(xp, bins=30, edgecolor="black")
    plt.title("Total XP")
    plt.xlabel("XP")
    plt.ylabel("Simulations")
    plt.grid(axis="y")

    plt.subplot(3, 2, 5)
    if xp_with_points:
        plt.hist(xp_with_points, bins=30, edgecolor="black")
    plt.title("Completed XP With Points")
    plt.xlabel("XP")
    plt.ylabel("Completed Simulations")
    plt.grid(axis="y")

    plt.subplot(3, 2, 6)
    if completion_times:
        plt.hist(completion_times, bins=30, edgecolor="black")
    plt.title("Completed Game Time")
    plt.xlabel("Seconds")
    plt.ylabel("Completed Simulations")
    plt.grid(axis="y")

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