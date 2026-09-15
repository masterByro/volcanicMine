import unittest

from analysisUtils import compute_negative_change_fit_slopes


class NegativeChangeFitTests(unittest.TestCase):
    def test_extracts_last_negative_changes_and_returns_slope(self):
        results = [
            {
                "stability_changes": [3, -2, -4, -6, -8],
            },
            {
                "stability_changes": [1, 2, -1, -3, -5, -7],
            },
        ]

        slopes = compute_negative_change_fit_slopes(results)

        self.assertEqual(len(slopes), 2)
        self.assertTrue(all(isinstance(value, float) for value in slopes))
        self.assertAlmostEqual(slopes[0], -2.0)
        self.assertAlmostEqual(slopes[1], -2.0)


if __name__ == "__main__":
    unittest.main()
