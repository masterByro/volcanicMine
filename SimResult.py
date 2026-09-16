import json
from dataclasses import asdict, dataclass


@dataclass
class SimulationResult:
    initial_A: int
    initial_B: int
    initial_C: int
    initial_stability: int
    lowest_stability: int
    final_stability: int
    death_time: int | None  # None if stability never reaches 0

    stability_changes: list[int]
    vent_changes: list[list[int]] | None

    # Player action tracking (only populated when rules include travel/mining phases)
    vents_checked: int = 0
    flips: int = 0
    player_position: str | None = None
    player_position_delay: float = 0.0
    boulder_position: str | None = None
    boulder_health: float | None = None
    points: float = 0.0
    xp: float = 0.0
    xp_with_points: float = 0.0
    exit_start_time: float | None = None
    completion_time: float | None = None
    b5_completed: bool = False
    b5_completed_time: float | None = None

    def to_dict(self):
        return asdict(self)



def print_result(result: SimulationResult):
    print(json.dumps(result.to_dict(), indent=4))


def save_result(result: SimulationResult, filename: str):
    with open(filename, "w") as f:
        json.dump(result.to_dict(), f, indent=4)