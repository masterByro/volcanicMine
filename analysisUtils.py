import json


#Given only stability
def find_best_early_warning_rule(
    filename: str,
    num_changes: int,
    target_stability: int,
):
    """
    Searches for the best rule of the form:

        sum(first N stability changes) <= threshold

    to predict whether the mine will ever drop below target_stability.
    """

    with open(filename, "r") as f:
        results = json.load(f)

    # (feature_value, outcome)
    data = []

    for r in results:
        feature = sum(r["stability_changes"][:num_changes])
        outcome = r["lowest_stability"] < target_stability

        data.append((feature, outcome))

    thresholds = sorted(set(feature for feature, _ in data))

    best = None

    for threshold in thresholds:

        tp = fp = tn = fn = 0

        for feature, outcome in data:

            prediction = feature <= threshold

            if prediction and outcome:
                tp += 1
            elif prediction and not outcome:
                fp += 1
            elif not prediction and outcome:
                fn += 1
            else:
                tn += 1

        total = tp + tn + fp + fn

        accuracy = (tp + tn) / total
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0

        if accuracy < 0.80:
            continue

        score = (
        precision * 0.7 +
        recall * 0.3
        )

        if best is None or score > best["score"]:
            best = {
                "threshold": threshold,
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "score": score,
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn,
            }
    if best is None:
        print("No rule found with accuracy >= 80%")
        return None

    print("\nBest Rule")
    print("-" * 40)
    print(
        f"If sum(first {num_changes} changes) <= {best['threshold']}"
    )
    print(f"Accuracy : {best['accuracy']:.2%}")
    print(f"Precision: {best['precision']:.2%}")
    print(f"Recall   : {best['recall']:.2%}") 
    print()
    print(f"TP={best['tp']}  FP={best['fp']}")
    print(f"TN={best['tn']}  FN={best['fn']}")

    return best

def find_best_rule_with_ab(
    filename: str,
    num_changes: int = 3,
    target_stability: int = 50,
):
    with open(filename, "r") as f:
        results = json.load(f)

    data = []

    for r in results:
        if len(r["stability_changes"]) < num_changes:
            continue

        data.append({
            "A": r["initial_A"],
            "B": r["initial_B"],
            "feature": sum(r["stability_changes"][:num_changes]),
            "outcome": r["lowest_stability"] < target_stability,
        })

    a_values = sorted(set(d["A"] for d in data))
    b_values = sorted(set(d["B"] for d in data))
    feature_values = sorted(set(d["feature"] for d in data))

    best = None

    for a_threshold in a_values:
        for b_threshold in b_values:
            for feature_threshold in feature_values:

                tp = fp = tn = fn = 0

                for d in data:

                    prediction = (
                        d["A"] <= a_threshold
                        and d["B"] <= b_threshold
                        and d["feature"] <= feature_threshold
                    )

                    if prediction and d["outcome"]:
                        tp += 1
                    elif prediction:
                        fp += 1
                    elif d["outcome"]:
                        fn += 1
                    else:
                        tn += 1

                total = tp + tn + fp + fn

                accuracy = (tp + tn) / total
                precision = tp / (tp + fp) if tp + fp else 0
                recall = tp / (tp + fn) if tp + fn else 0

                score = precision * recall

                if best is None or score > best["score"]:
                    best = {
                        "A": a_threshold,
                        "B": b_threshold,
                        "feature": feature_threshold,
                        "accuracy": accuracy,
                        "precision": precision,
                        "recall": recall,
                        "score": score,
                    }
    if best is None:
        print("No rule found with accuracy >= 80%")
        return None

    print("\nBest Rule")
    print("-" * 40)
    print(
        f"A <= {best['A']}, "
        f"B <= {best['B']}, "
        f"sum(first {num_changes}) <= {best['feature']}"
    )
    print(f"Accuracy : {best['accuracy']:.2%}")
    print(f"Precision: {best['precision']:.2%}")
    print(f"Recall   : {best['recall']:.2%}")

    return best