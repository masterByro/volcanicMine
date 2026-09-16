import random
import unittest
from typing import cast

import simulations
from rules import RULES_ONE, RULES_TWO
from utils import simulate
from XpUtils import FINISH_PTS, PROSPECTORS, XP_PER_POINT


class SimulateGameTests(unittest.TestCase):
    def test_half_one_default_route_mines_without_rules(self):
        result = simulate(70, 50, 50, 100, [], time_limit=80, clock_limit=80)

        self.assertEqual(result.vents_checked, 0)
        self.assertEqual(result.flips, 0)
        self.assertEqual(result.boulder_position, "B1")
        self.assertGreater(result.points, 0)

    def test_half_one_start_route_checks_a_fixes_if_low_then_checks_b(self):
        result = simulate(30, 50, 50, 100, RULES_ONE, time_limit=80, clock_limit=80)

        self.assertEqual(result.vents_checked, 2)
        self.assertEqual(result.flips, 1)
        self.assertEqual(result.boulder_position, "B1")

    def test_half_one_start_route_skips_a_fix_if_not_low(self):
        result = simulate(70, 50, 50, 100, RULES_ONE, time_limit=80, clock_limit=80)

        self.assertEqual(result.vents_checked, 2)
        self.assertEqual(result.flips, 0)
        self.assertEqual(result.boulder_position, "B1")

    def test_half_one_waits_at_a_reset_after_b3(self):
        result = simulate(
            50,
            30,
            50,
            20,
            RULES_ONE,
            time_limit=200,
            clock_limit=200,
            starting_boulder_position="B3",
            starting_boulder_health=1,
        )

        self.assertIsNone(result.death_time)
        self.assertEqual(result.player_position, "A_RESET")
        self.assertEqual(result.boulder_position, "B3")
        self.assertEqual(result.boulder_health, 0)

    def test_simulate_game_carries_first_half_state_into_reset_sweep(self):
        original_iterator = simulations.iterator
        simulations.iterator = cast(int, 50)

        try:
            random.seed(7)
            game = simulations.simulate_single_game(70, 70, 70, useRules=True)
        finally:
            simulations.iterator = original_iterator

        first_half = game["first_half"]
        second_half_results = game["second_half_results"]

        self.assertEqual(len(second_half_results), 8)
        self.assertEqual(first_half.player_position, "A_RESET")
        self.assertEqual(first_half.boulder_position, "B3")
        self.assertEqual(first_half.boulder_health, 0)

        for result in second_half_results:
            self.assertEqual(result.initial_stability, first_half.final_stability)
            self.assertGreaterEqual(result.vents_checked, first_half.vents_checked)
            self.assertGreaterEqual(result.flips, first_half.flips)
            self.assertGreaterEqual(result.points, first_half.points)
            self.assertGreaterEqual(result.xp, first_half.xp)

            if result.completion_time is not None:
                self.assertAlmostEqual(
                    result.xp_with_points,
                    round(result.xp + result.points * XP_PER_POINT * (1 + PROSPECTORS), 2),
                    delta=0.05,
                )
            else:
                self.assertEqual(result.xp_with_points, result.xp)

            if result.b5_completed:
                self.assertEqual(result.boulder_position, "B5")
                self.assertEqual(result.boulder_health, 0)
                self.assertIsNotNone(result.b5_completed_time)
                self.assertLessEqual(result.b5_completed_time, simulations.get_clock_limit(2))

    def test_half_one_after_b1_fixes_use_route_timings(self):
        result = simulate(
            30,
            30,
            70,
            100,
            RULES_ONE,
            time_limit=125,
            clock_limit=125,
            starting_boulder_position="B1",
            starting_boulder_health=1,
        )

        self.assertGreaterEqual(result.flips, 2)
        self.assertEqual(result.boulder_position, "B2")

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
        self.assertTrue(result.b5_completed)
        self.assertIsNotNone(result.b5_completed_time)
        self.assertEqual(result.boulder_position, "B5")
        self.assertEqual(result.boulder_health, 0)
        self.assertGreaterEqual(result.points, 10 + FINISH_PTS)

    def test_half_two_exits_when_b5_is_already_mined_at_reset(self):
        result = simulations.run_simulation(
            25,
            35,
            65,
            13,
            2,
            useRules=True,
            starting_boulder_position="B5",
            starting_boulder_health=0,
        )

        self.assertIsNone(result.death_time)
        self.assertIsNotNone(result.exit_start_time)
        self.assertIsNotNone(result.completion_time)
        self.assertTrue(result.b5_completed)

    def test_half_two_exit_rule_stops_mining_before_predicted_blowup(self):
        result = simulate(
            25,
            25,
            25,
            20,
            RULES_TWO,
            time_limit=255,
            clock_limit=300,
            starting_boulder_position="B5",
            starting_boulder_health=60,
        )

        self.assertIsNone(result.death_time)
        self.assertIsNotNone(result.completion_time)
        completion_time = cast(float, result.completion_time)
        self.assertAlmostEqual(completion_time, 45, places=2)
        self.assertFalse(result.b5_completed)
        self.assertEqual(result.boulder_position, "B5")
        self.assertIsNotNone(result.boulder_health)
        boulder_health = cast(float, result.boulder_health)
        self.assertGreater(boulder_health, 0)
        self.assertLess(result.points, 1106.56 + FINISH_PTS)
        self.assertAlmostEqual(
            result.xp_with_points,
            round(result.xp + result.points * XP_PER_POINT * (1 + PROSPECTORS), 2),
            delta=0.05,
        )

    def test_half_two_without_carried_boulder_ignores_exit_only_player_rule(self):
        result = simulations.run_simulation(50, 50, 50, 50, 2, useRules=True)

        self.assertIsNone(result.boulder_position)
        self.assertIsNone(result.boulder_health)

    def test_half_two_checks_and_fixes_a_from_reset_before_b4(self):
        result = simulations.run_simulation(
            30,
            70,
            70,
            100,
            2,
            useRules=True,
            starting_boulder_position="B3",
            starting_boulder_health=0,
            starting_player_position="A_RESET",
        )

        self.assertIsNone(result.death_time)
        self.assertGreaterEqual(result.vents_checked, 1)
        self.assertGreaterEqual(result.flips, 1)
        self.assertIn(result.boulder_position, {"B4", "B5"})

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

    def test_half_two_caps_to_limit_after_b4_before_b5(self):
        result = simulations.run_simulation(
            75,
            75,
            75,
            100,
            2,
            useRules=True,
            starting_boulder_position="B4",
            starting_boulder_health=1,
            starting_flips=2,
        )

        self.assertIsNone(result.death_time)
        self.assertEqual(result.flips, 6)
        self.assertEqual(result.boulder_position, "B5")

    def test_simulate_game_skips_second_half_when_first_half_dies(self):
        game = simulations.simulate_single_game(30, 30, 30, useRules=True)

        self.assertEqual(game["first_half"].death_time, 150)
        self.assertEqual(game["second_half_results"], [])

    def test_simulate_game_sweeps_all_starting_values(self):
        original_iterator = simulations.iterator
        simulations.iterator = cast(int, 40)

        try:
            game = simulations.simulateGame(useRules=True)
        finally:
            simulations.iterator = original_iterator

        self.assertEqual(len(game["games"]), 8)
        self.assertEqual(len(simulations.get_first_half_results(game)), 8)
        self.assertGreater(len(simulations.flatten_second_half_results(game)), 0)
        first_half_deaths = sum(result.death_time is not None for result in simulations.get_first_half_results(game))
        self.assertEqual(
            len(simulations.get_full_game_outcomes(game)),
            first_half_deaths * simulations.get_reset_outcome_count() + len(simulations.flatten_second_half_results(game)),
        )


if __name__ == "__main__":
    unittest.main()