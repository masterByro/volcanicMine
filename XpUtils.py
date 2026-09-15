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

XP_PER_POINT = 3.8
PROSPECTORS = 0.025

#Assumes lvl 103 (lvl 99+ ring)
# time (seconds) = health / MINE_SUCCESS_RATE attempts, each attempt taking
# AVG_TICKS_PER_ATTEMPT ticks (3 ticks normally, 1/4 chance of 2 ticks) at 0.6s/tick
# xp includes the PROSPECTORS boost; xp_hr_points also converts points to xp at XP_PER_POINT * (1 + PROSPECTORS)
BOULDERS = [
    {"stage": 1,"chance": 1/20, "health":40, "rolls": 2.0, "points": 144.66, "xp": 392.15, "time": 69.28, "xp_hr": 20377.56, "xp_hr_points": 49656.17, "xp_with_points": 955.6},
    {"stage": 2,"chance": 1/12, "health":40,  "rolls": 3.333333333333333, "points": 214.43,  "xp": 516.93, "time": 69.28, "xp_hr": 26861.15, "xp_hr_points": 70260.94, "xp_with_points": 1352.13},
    {"stage": 3,"chance": 1/8, "health":40, "rolls": 5.0, "points": 301.64, "xp": 672.89, "time": 69.28, "xp_hr": 34965.52, "xp_hr_points": 96016.27, "xp_with_points": 1847.78},
    {"stage": 4,"chance": 1/5, "health":40, "rolls": 8.0, "points": 458.63, "xp": 953.62, "time": 69.28, "xp_hr": 49552.95, "xp_hr_points": 142377.86, "xp_with_points": 2739.98},
    {"stage": 5,"chance": 1/3, "health":60, "rolls": 20.0, "points": 1106.56, "xp": 2179.05, "time": 103.92, "xp_hr": 75486.63, "xp_hr_points": 224795.57, "xp_with_points": 6489.1},
    # stage 6 = full mine run (stages 1-5 summed); xp_hr/xp_hr_points are averages over the total time
    {"stage": 6, "points": 2225.92, "xp": 4714.64, "time": 381.04, "xp_hr": 44543.1, "xp_hr_points": 126455.29, "xp_with_points": 13384.59},
]

CAP_PTS = 50
CHECK_PTS = 50
FINISH_PTS = 100

def expected_boulder_rewards():
    """
    Returns the expected points and XP for each boulder.
    """

    results = []

    for boulder in BOULDERS:
        rolls = boulder["health"] * boulder["chance"]

        points = 0.0
        xp = 0.0

        parts = boulder["health"] - rolls

        points = parts * ORES["Part of the boulder"]["points"]
        xp = parts * ORES["Part of the boulder"]["xp"]
        for ore in ORES.values():
            probability = ore["weight"] / 100

            points += rolls * probability * ore["points"]
            xp += rolls * probability * ore["xp"]

        xp *= (1 + PROSPECTORS)

        results.append({
            "stage": boulder["stage"],
            "health": boulder["health"],
            "chance": boulder["chance"],
            "rolls": rolls,
            "points": round(points, 2),
            "xp": round(xp, 2),
        })

    return results