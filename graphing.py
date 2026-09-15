# graph_utils.py
import json
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