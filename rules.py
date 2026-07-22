RULES = [
    #Fix A at start
    # {
    #     "time": 30,
    #     "condition": lambda A, B, C, STABILITY: A < 50,
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
    # {
    #     "time": 250,
    #     "condition": lambda A, B, C, STABILITY: A < 42,
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

    #Blind fix B
    # {
    #     "time": 140,
    #     "condition": lambda A, B, C, STABILITY: True,
    #     "action": {
    #         "type": "flip",
    #         "target": "B"
    #     }
    # },
    #Blind fix C
    # {
    #     "time": 120,
    #     "condition": lambda A, B, C, STABILITY: True,
    #     "action": {
    #         "type": "flip",
    #         "target": "C"
    #     }
    # }
]