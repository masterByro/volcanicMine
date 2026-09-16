RULES_ONE = [
    #Fix A at start
    # {
    #     "time": 25,
    #     "condition": lambda A, B, C, STABILITY: A < 48,
    #     "action": {
    #         "type": "flip",
    #         "target": "A"
    #     }
    # },

    # Check B at start
    {
        "time": {"action": 28, "end": 31},
        "action": {"type": "vent", "target": "B"},
        "trigger":{"time": 0},
        "travel": {"from": "start", "to": "B1"}
    },
    # #Fix B at start
    # {
    #     "time": 30,
    #     "condition": lambda A, B, C, STABILITY: B < 50,
    #     "action": {
    #         "type": "flip",
    #         "target": "B"
    #     }
    # },

    #Fix A after B1
    # {
    #     "time": 140,
    #     "condition": lambda A, B, C, STABILITY: A < 42,
    #     "action": {
    #         "type": "flip",
    #         "target": "A"
    #     }
    # },
    #Fix A after B2
    {
        "time": {"action": 29, "end": 42},
        "trigger":{"after_boulder": 2,  "condition": lambda A, B, C, STABILITY: A < 42},
        "action": {"type": "flip", "target": "A"},
        "travel": {"from": "B2", "to": "B3"}
    },
    #Fix B after B1
    # {
    #     "time": 140,
    #     "condition": lambda A, B, C, STABILITY: B < 42,
    #     "action": {
    #         "type": "flip",
    #         "target": "B"
    #     }
    # },
    #Fix B after B2
    # {
    #     "time": 190,
    #     "condition": lambda A, B, C, STABILITY: B < 42,
    #     "action": {
    #         "type": "flip",
    #         "target": "B"
    #     }
    # },
        # #6minute A,B fix
    # {
    #     "time": 230, #leave at 6:18, arrive 6:10
    #     "condition": lambda A, B, C, STABILITY: A < 45 and STABILITY < 70,
    #     "action": {
    #         "type": "flip",
    #         "target": "A"
    #     }
    # },
    # {
    #     "time": 250,
    #     "condition": lambda A, B, C, STABILITY: B < 42,
    #     "action": {
    #         "type": "flip",
    #         "target": "B"
    #     }
    # },
]

RULES_TWO = [
    {
        "trigger": {"time_left": 32},
        "action": {"type": "exit"},
    },
    #Fix A at start
    # {
    #     "time": 20,
    #     "condition": lambda A, B, C, STABILITY: A < 48,
    #     "action": {
    #         "type": "flip",
    #         "target": "A"
    #     }
    # },
    # Blind fix B after B4
    {
        "time": {"action": 0, "end": 28},
        "trigger": {"after_boulder": 4},
        "action": {"type": "flip", "target": "B"},
        "travel": {"from": "B4", "to": "B5"},
    },
    # Blind fix C after B4
    {
        "time": {"action": 0, "end": 38},
        "trigger": {"after_boulder": 4},
        "action": {"type": "flip", "target": "C"},
        "travel": {"from": "B4", "to": "B5"},
    },
]