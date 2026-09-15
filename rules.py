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

    # #Fix B at start
    # {
    #     "time": 30,
    #     "condition": lambda A, B, C, STABILITY: B < 50,
    #     "action": {
    #         "type": "flip",
    #         "target": "B"
    #     }
    # },

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

    #Fix A after B1
    {
        "time": 140,
        "condition": lambda A, B, C, STABILITY: A < 42,
        "action": {
            "type": "flip",
            "target": "A"
        }
    },
    #Fix A after B2
    {
        "time": 190,
        "condition": lambda A, B, C, STABILITY: A < 42,
        "action": {
            "type": "flip",
            "target": "A"
        }
    },
    #Fix B after B1
    {
        "time": 140,
        "condition": lambda A, B, C, STABILITY: B < 42,
        "action": {
            "type": "flip",
            "target": "B"
        }
    },
    #Fix B after B2
    {
        "time": 190,
        "condition": lambda A, B, C, STABILITY: B < 42,
        "action": {
            "type": "flip",
            "target": "B"
        }
    },
]

RULES_TWO = [
    #Fix A at start
    # {
    #     "time": 20,
    #     "condition": lambda A, B, C, STABILITY: A < 48,
    #     "action": {
    #         "type": "flip",
    #         "target": "A"
    #     }
    # },
    #Blind fix B
    # {
    #     "time": 110,
    #     "condition": lambda A, B, C, STABILITY: True,
    #     "action": {
    #         "type": "flip",
    #         "target": "B"
    #     }
    # },
    #Blind fix C
    # {
    #     "time": 130,
    #     "condition": lambda A, B, C, STABILITY: True,
    #     "action": {
    #         "type": "flip",
    #         "target": "C"
    #     }
    # }
]