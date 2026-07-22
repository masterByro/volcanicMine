#Assumes lvl 103 (lvl 99+ ring)
ORES = {
    "Part of the boulder": {
        "weight": 0.0,
        "points": 1,
        "xp": 5,
    },
    "Iron": {
        "weight": 0.38,
        "points": 15,
        "xp": 10,
    },
    "Silver": {
        "weight": 1.20,
        "points": 20,
        "xp": 20,
    },
    "Coal": {
        "weight": 3.67,
        "points": 25,
        "xp": 30,
    },
    "Gold": {
        "weight": 10.21,
        "points": 34,
        "xp": 40,
    },
    "Mithril": {
        "weight": 25.77,
        "points": 44,
        "xp": 60,
    },
    "Adamantite": {
        "weight": 25.57,
        "points": 55,
        "xp": 100,
    },
    "Runite": {
        "weight": 33.20,
        "points": 70,
        "xp": 150,
    },
}

#Assumes lvl 103 (lvl 99+ ring)
BOULDERS = [
    {"stage": 1,"chance": 1/20, "health":40, "expected_rolls": 2.0, "expected_points": 144.66, "expected_xp": 382.59},
    {"stage": 2,"chance": 1/12, "health":40,  "expected_rolls": 3.333333333333333, "expected_points": 214.43,  "expected_xp": 504.32},
    {"stage": 3,"chance": 1/8, "health":40, "expected_rolls": 5.0, "expected_points": 301.64, "expected_xp": 656.48},
    {"stage": 4,"chance": 1/5, "health":40, "expected_rolls": 8.0, "expected_points": 458.63, "expected_xp": 930.36},
    {"stage": 5,"chance": 1/3, "health":60, "expected_rolls": 20.0, "expected_points": 1106.56, "expected_xp": 2125.9},
]
#9 in 229
#11 in 231
#18 in 238
CAP_PTS = 50
CHECK_PTS = 50
FINISH_PTS = 100

def expected_boulder_rewards():
    """
    Returns the expected points and XP for each boulder.
    """

    results = []

    for boulder in BOULDERS:
        expected_rolls = boulder["health"] * boulder["chance"]

        expected_points = 0.0
        expected_xp = 0.0

        expected_parts = boulder["health"] - expected_rolls

        expected_points = expected_parts * ORES["Part of the boulder"]["points"]
        expected_xp = expected_parts * ORES["Part of the boulder"]["xp"]
        for ore in ORES.values():
            probability = ore["weight"] / 100

            expected_points += expected_rolls * probability * ore["points"]
            expected_xp += expected_rolls * probability * ore["xp"]

        results.append({
            "stage": boulder["stage"],
            "health": boulder["health"],
            "chance": boulder["chance"],
            "expected_rolls": expected_rolls,
            "expected_points": round(expected_points, 2),
            "expected_xp": round(expected_xp, 2),
        })

    return results