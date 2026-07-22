def flip(value: int) -> int:
    return 100 - value

def apply_action(action, A, B, C):

    if action["type"] == "flip":
        target = action["target"]

        if target == "A":
            A = flip(A)

        elif target == "B":
            B = flip(B)

        elif target == "C":
            C = flip(C)

    return A, B, C