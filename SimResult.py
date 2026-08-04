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

    def to_dict(self):
        return asdict(self)



def print_result(result: SimulationResult):
    print(json.dumps(result.to_dict(), indent=4))


def save_result(result: SimulationResult, filename: str):
    with open(filename, "w") as f:
        json.dump(result.to_dict(), f, indent=4)