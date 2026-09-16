RULES_ONE = [
    # Check A at start, then continue to B vent and B1
    {
        "time": {"action": 31, "end": 54},
        "action": {"type": "vent", "target": "A"},
        "trigger": {"time": 0},
        "travel": {"from": "start", "to": "B1"},
    },
    # Fix A from start route if the checked A vent needs it
    {
        "time": {"action": 43, "end": 74},
        "action": {"type": "flip", "target": "A"},
        "trigger": {"time": 0, "condition": lambda A, B, C, STABILITY: A < 48},
        "travel": {"from": "start", "to": "B1"},
    },
    # Check B on start route when A did not need fixing
    {
        "time": {"action": 51, "end": 54},
        "action": {"type": "vent", "target": "B"},
        "trigger": {"time": 0, "condition": lambda A, B, C, STABILITY: A >= 48},
        "travel": {"from": "start", "to": "B1"},
    },
    # Check B on start route after fixing A
    {
        "time": {"action": 71, "end": 74},
        "action": {"type": "vent", "target": "B"},
        "trigger": {"time": 0, "condition": lambda A, B, C, STABILITY: A < 48},
        "travel": {"from": "start", "to": "B1"},
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

    # Fix A after B1
    {
        "time": {"action": 44.22, "end": 61.72},
        "trigger": {"after_boulder": 1, "condition": lambda A, B, C, STABILITY: A < 42 and B >= 42},
        "action": {"type": "flip", "target": "A"},
        "travel": {"from": "B1", "to": "B2"},
    },
    # Fix B after B1
    {
        "time": {"action": 47.22, "end": 75.22},
        "trigger": {"after_boulder": 1, "condition": lambda A, B, C, STABILITY: B < 42 and A >= 42},
        "action": {"type": "flip", "target": "B"},
        "travel": {"from": "B1", "to": "B2"},
    },
    # Fix A and B after B1
    {
        "time": {"action": 44.22, "end": 101.94},
        "trigger": {"after_boulder": 1, "condition": lambda A, B, C, STABILITY: A < 42 and B < 42},
        "action": {"type": "flip", "target": "A"},
        "travel": {"from": "B1", "to": "B2"},
    },
    {
        "time": {"action": 73.94, "end": 101.94},
        "trigger": {"after_boulder": 1, "condition": lambda A, B, C, STABILITY: A < 42 and B < 42},
        "action": {"type": "flip", "target": "B"},
        "travel": {"from": "B1", "to": "B2"},
    },
    # Fix A after B2
    {
        "time": {"action": 29.2, "end": 41.72},
        "trigger": {"after_boulder": 2, "condition": lambda A, B, C, STABILITY: A < 42 and B >= 42},
        "action": {"type": "flip", "target": "A"},
        "travel": {"from": "B2", "to": "B3"},
    },
    # Fix B after B2
    {
        "time": {"action": 33.2, "end": 54.22},
        "trigger": {"after_boulder": 2, "condition": lambda A, B, C, STABILITY: B < 42 and A >= 42},
        "action": {"type": "flip", "target": "B"},
        "travel": {"from": "B2", "to": "B3"},
    },
    # Fix A and B after B2
    {
        "time": {"action": 29.2, "end": 80.94},
        "trigger": {"after_boulder": 2, "condition": lambda A, B, C, STABILITY: A < 42 and B < 42},
        "action": {"type": "flip", "target": "A"},
        "travel": {"from": "B2", "to": "B3"},
    },
    {
        "time": {"action": 57.4, "end": 80.94},
        "trigger": {"after_boulder": 2, "condition": lambda A, B, C, STABILITY: A < 42 and B < 42},
        "action": {"type": "flip", "target": "B"},
        "travel": {"from": "B2", "to": "B3"},
    },
    # Move to A after B3 and wait for the 5 minute reset
    {
        "time": {"duration": 17},
        "trigger": {"after_boulder": 3},
        "action": {"type": "wait_reset", "position": "A_RESET", "caps": 2, "cap_duration": 4, "max_per_game": 6},
    },
        # #6minute A,B fix
    {
        "time": 230, #leave at 6:18, arrive 6:10
        "condition": lambda A, B, C, STABILITY: A < 45 and STABILITY < 70,
        "action": {
            "type": "flip",
            "target": "A"
        }
    },
    # {
    #     "time": 250,
    #     "condition": lambda A, B, C, STABILITY: B < 42,
    #     "action": {
    #         "type": "flip",
    #         "target": "B"
    #     }
    # },
        # Fix B just before B4
    {
        "time": {"action": 26, "end": 26},
        "trigger": {"after_boulder": 3},
        "condition": lambda A, B, C, STABILITY: B < 45 and STABILITY < 60,
        "action": {"type": "flip", "target": "B"},
        "travel": {"from": "B3", "to": "B4"},
    },
]

RULES_TWO = [
    {
        "trigger": {"predicted_blowup_buffer": 32},
        "action": {"type": "exit"},
    },
    # Check A at reset and continue to B4 when no fix is needed
    {
        "time": {"action": 0, "end": 69},
        "trigger": {"after_boulder": 3, "condition": lambda A, B, C, STABILITY: A >= 48},
        "action": {"type": "vent", "target": "A"},
        "travel": {"from": "A_RESET", "to": "B4"},
    },
    # Check A at reset before fixing it
    {
        "time": {"action": 0, "end": 66},
        "trigger": {"after_boulder": 3, "condition": lambda A, B, C, STABILITY: A < 48},
        "action": {"type": "vent", "target": "A"},
        "travel": {"from": "A_RESET", "to": "B4"},
    },
    # Fix A after reset and take the shorter B4 path
    {
        "time": {"action": 6, "end": 66},
        "trigger": {"after_boulder": 3, "condition": lambda A, B, C, STABILITY: A < 48},
        "action": {"type": "flip", "target": "A"},
        "travel": {"from": "A_RESET", "to": "B4"},
    },
    # Blind fix B after B4
    {
        "time": {"action": 0, "end": 28},
        "trigger": {"after_boulder": 4},
        "action": {"type": "flip", "target": "B"},
        "travel": {"from": "B4", "to": "B5"},
    },
    # Blind fix C after B4
    # {
    #     "time": {"action": 0, "end": 38},
    #     "trigger": {"after_boulder": 4},
    #     "action": {"type": "flip", "target": "C"},
    #     "travel": {"from": "B4", "to": "B5"},
    # },

    #Capping after B4 (guarantees 6 caps)
    {
        "time": {"duration": 2},
        "trigger": {"after_boulder": 4, "phase": "after_actions"},
        "action": {"type": "cap", "max_per_game": 6},
    },

    #Capping after B5
    # {
    #     "time": {"duration": 2},
    #     "trigger": {"after_boulder": 5},
    #     "action": {"type": "cap", "max_per_game": 6},
    # },

    #Check B for points (130000 xp/hr)
    {
        "time": {"duration": 9},
        "trigger": {"after_boulder": 5},
        "action": {"type": "vent", "target": "B"},
    },
    #Check C for points (97375 xp/hr)
    {
        "time": {"duration": 12},
        "trigger": {"after_boulder": 5},
        "action": {"type": "vent", "target": "C"},
    },
]