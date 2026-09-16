import random
import unittest

import simulations
from rules import RULES_TWO
from utils import simulate
from XpUtils import FINISH_PTS, PROSPECTORS, XP_PER_POINT


class SimulateGameTests(unittest.TestCase):
    def test_simulate_game_carries_first_half_state_into_reset_sweep(self):
        original_iterator = simulations.iterator
        simulations.iterator = 50

        try:
            random.seed(7)
            game = simulations.simulateGame(50, 50, 50, useRules=True)
        finally:
            simulations.iterator = original_iterator

        first_half = game["first_half"]
        second_half_results = game["second_half_results"]

        self.assertEqual(len(second_half_results), 8)
        self.assertEqual(first_half.boulder_position, "B4")
        self.assertGreater(first_half.boulder_health, 0)

        for result in second_half_results:
            self.assertEqual(result.initial_stability, first_half.final_stability)
            self.assertGreaterEqual(result.vents_checked, first_half.vents_checked)
            self.assertGreaterEqual(result.flips, first_half.flips)
            self.assertGreaterEqual(result.points, first_half.points)
            self.assertGreaterEqual(result.xp, first_half.xp)

            if result.completion_time is not None:
                self.assertIsNone(result.death_time)
                self.assertLessEqual(result.completion_time, simulations.get_clock_limit(2))
                self.assertAlmostEqual(
                    result.xp_with_points,
                    round(result.xp + result.points * XP_PER_POINT * (1 + PROSPECTORS), 2),
                )
            else:
                self.assertEqual(result.xp_with_points, result.xp)

    def test_finishing_b5_adds_finish_points_before_exit(self):
        result = simulations.run_simulation(
            75,
            75,
            75,
            100,
            2,
            useRules=True,
            starting_boulder_position="B5",
            starting_boulder_health=1,
            starting_points=10,
        )

        self.assertIsNone(result.death_time)
        self.assertIsNotNone(result.completion_time)
        self.assertEqual(result.boulder_position, "B5")
        self.assertEqual(result.boulder_health, 0)
        self.assertGreaterEqual(result.points, 10 + FINISH_PTS)

    def test_half_two_exit_rule_stops_mining_with_32_seconds_left(self):
        result = simulate(
            75,
            75,
            75,
            100,
            RULES_TWO,
            time_limit=100,
            starting_boulder_position="B5",
            starting_boulder_health=60,
        )

        self.assertIsNone(result.death_time)
        self.assertEqual(result.completion_time, 100)
        self.assertEqual(result.boulder_position, "B5")
        self.assertGreater(result.boulder_health, 0)
        self.assertLess(result.points, 1106.56 + FINISH_PTS)

    def test_half_two_without_carried_boulder_ignores_exit_only_player_rule(self):
        result = simulations.run_simulation(50, 50, 50, 50, 2, useRules=True)

        self.assertIsNone(result.boulder_position)
        self.assertIsNone(result.boulder_health)

    def test_half_two_blind_flips_b_and_c_after_mining_b4(self):
        result = simulations.run_simulation(
            75,
            25,
            75,
            100,
            2,
            useRules=True,
            starting_boulder_position="B4",
            starting_boulder_health=1,
        )

        self.assertIsNone(result.death_time)
        self.assertGreaterEqual(result.flips, 2)
        self.assertEqual(result.boulder_position, "B5")

    def test_simulate_game_skips_second_half_when_first_half_dies(self):
        game = simulations.simulateGame(30, 30, 30, useRules=True)

        self.assertEqual(game["first_half"].death_time, 90)
        self.assertEqual(game["second_half_results"], [])


if __name__ == "__main__":
    unittest.main()