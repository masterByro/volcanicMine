from SimResult import SimulationResult
import json


def save_results_json(results: list[SimulationResult], filename: str):
    """
    Saves a list of SimulationResult objects to a JSON file.
    """

    data = [
        result.to_dict()
        for result in results
    ]

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)