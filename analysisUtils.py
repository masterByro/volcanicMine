import json
import math

import matplotlib.pyplot as plt


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

    thresholds = sorted({feature for feature, _ in data})

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

    a_values = sorted({d["A"] for d in data})
    b_values = sorted({d["B"] for d in data})
    feature_values = sorted({d["feature"] for d in data})

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


def _linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float] | None:
    n = len(xs)
    if n == 0:
        return None

    x_mean = sum(xs) / n
    y_mean = sum(ys) / n

    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    den = sum((x - x_mean) ** 2 for x in xs)

    if den == 0:
        return None

    slope = num / den
    intercept = y_mean - slope * x_mean
    return slope, intercept


def _tail_of_negative_changes(changes: list[float]) -> list[float]:
    """Return the trailing run of negative changes, stopping at the first non-negative value."""

    tail: list[float] = []

    for change in reversed(changes):
        if change < 0:
            tail.append(change)
        else:
            break

    return list(reversed(tail))


def compute_negative_change_fit_slopes(results: list[dict]) -> list[float]:
    """
    For each simulation result, inspect the trailing run of negative stability changes.
    The value is the average de-acceleration: the average difference between consecutive
    negative changes in that tail.
    """

    slopes: list[float] = []

    for result in results:
        if isinstance(result, dict):
            changes = result.get("stability_changes", [])
        else:
            changes = getattr(result, "stability_changes", [])

        tail = _tail_of_negative_changes(changes)

        if len(tail) < 2:
            slopes.append(float("nan"))
            continue

        differences = [tail[i] - tail[i - 1] for i in range(1, len(tail))]

        if not differences:
            slopes.append(float("nan"))
            continue

        average_deacceleration = sum(differences) / len(differences)
        slopes.append(float(average_deacceleration))

    return slopes


def export_negative_change_tails(filename: str, output_filename: str = "stability_change.json") -> list[list[float]]:
    """
    Read simulation results from JSON and export the trailing negative-change tail
    for each result as an array of arrays.
    """

    with open(filename, "r") as f:
        raw_text = f.read().strip()

    if raw_text.endswith("]]" ):
        raw_text = raw_text[:-1].rstrip()

    results = json.loads(raw_text)

    tails = []
    for result in results:
        if isinstance(result, dict):
            changes = result.get("stability_changes", [])
        else:
            changes = getattr(result, "stability_changes", [])

        tail = _tail_of_negative_changes(changes)
        if len(tail) >= 6:
            tails.append(tail)

    def _sort_key(tail: list[float]) -> tuple[float, ...]:
        # Compare each position directly against the repeated -1 pattern so the
        # ordering is driven by the full tail shape, not just a total sum.
        penalty = tuple(abs(value + 1) for value in tail)
        return penalty + (len(tail),)

    tails.sort(key=_sort_key)

    with open(output_filename, "w") as f:
        f.write("[\n")
        for index, tail in enumerate(tails):
            f.write("    " + json.dumps(tail))
            if index < len(tails) - 1:
                f.write(",\n")
            else:
                f.write("\n")
        f.write("]\n")

    return tails


def plot_negative_change_fit_distribution(filename: str, bins: int = 10, show_plot: bool = True) -> list[float]:
    """
    Reads simulation results from JSON and plots the distribution of the fitted
    negative-change slopes for each run.
    """

    with open(filename, "r") as f:
        raw_text = f.read().strip()

    if raw_text.endswith("]]"):
        raw_text = raw_text[:-1].rstrip()

    results = json.loads(raw_text)

    slopes = [value for value in compute_negative_change_fit_slopes(results) if not math.isnan(value)]

    if not slopes:
        raise ValueError("No usable negative change slopes were found")

    plt.figure(figsize=(10, 6))
    plt.hist(slopes, bins=bins, color="steelblue", edgecolor="black")
    plt.title("Distribution of Negative-Change Fit Slopes")
    plt.xlabel("Slope of decline-rate curve")
    plt.ylabel("Count")
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()

    if show_plot:
        plt.show()
    else:
        plt.close()

    return slopes


def _quadratic_fit_3_points(xs: list[float], ys: list[float]) -> tuple[float, float, float] | None:
    if len(xs) != 3 or len(ys) != 3:
        return None

    x1, x2, x3 = xs
    y1, y2, y3 = ys

    den = (x1 - x2) * (x1 - x3) * (x2 - x3)
    if den == 0:
        return None

    a = (
        x3 * (y2 - y1)
        + x2 * (y1 - y3)
        + x1 * (y3 - y2)
    ) / den

    b = (
        (x3 ** 2) * (y1 - y2)
        + (x2 ** 2) * (y3 - y1)
        + (x1 ** 2) * (y2 - y3)
    ) / den

    c = (
        x2 * x3 * (x2 - x3) * y1
        + x3 * x1 * (x3 - x1) * y2
        + x1 * x2 * (x1 - x2) * y3
    ) / den

    return a, b, c


def _exponential_fit(xs: list[float], ys: list[float]) -> tuple[float, float] | None:
    if any(y <= 0 for y in ys):
        return None

    log_ys = [math.log(y) for y in ys]
    params = _linear_fit(xs, log_ys)

    if params is None:
        return None

    b, ln_a = params
    a = math.exp(ln_a)
    return a, b


def _safe_error_metrics(errors: list[float]) -> dict[str, float | None]:
    if not errors:
        return {
            "mae": None,
            "rmse": None,
            "median_abs_error": None,
        }

    abs_errors = [abs(e) for e in errors]
    mae = sum(abs_errors) / len(abs_errors)
    rmse = math.sqrt(sum(e * e for e in errors) / len(errors))

    sorted_abs = sorted(abs_errors)
    mid = len(sorted_abs) // 2

    if len(sorted_abs) % 2 == 1:
        median_abs_error = sorted_abs[mid]
    else:
        median_abs_error = (sorted_abs[mid - 1] + sorted_abs[mid]) / 2

    return {
        "mae": mae,
        "rmse": rmse,
        "median_abs_error": median_abs_error,
    }


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float] | None:
    n = len(matrix)
    augmented = [row[:] + [vector[i]] for i, row in enumerate(matrix)]

    for col in range(n):
        pivot_row = max(range(col, n), key=lambda r: abs(augmented[r][col]))
        pivot = augmented[pivot_row][col]

        if abs(pivot) < 1e-12:
            return None

        augmented[col], augmented[pivot_row] = augmented[pivot_row], augmented[col]

        pivot = augmented[col][col]
        for j in range(col, n + 1):
            augmented[col][j] /= pivot

        for r in range(n):
            if r == col:
                continue

            factor = augmented[r][col]
            if factor == 0:
                continue

            for j in range(col, n + 1):
                augmented[r][j] -= factor * augmented[col][j]

    return [augmented[i][n] for i in range(n)]


def _fit_linear_regression(
    features: list[list[float]],
    targets: list[float],
    ridge: float = 1e-6,
) -> list[float] | None:
    if not features or len(features) != len(targets):
        return None

    num_features = len(features[0])
    xtx = [[0.0 for _ in range(num_features)] for _ in range(num_features)]
    xty = [0.0 for _ in range(num_features)]

    for row, target in zip(features, targets):
        for i in range(num_features):
            xty[i] += row[i] * target
            for j in range(num_features):
                xtx[i][j] += row[i] * row[j]

    for i in range(num_features):
        xtx[i][i] += ridge

    return _solve_linear_system(xtx, xty)


def _ar3_linear_features(context: list[float]) -> list[float]:
    return [1.0, context[0], context[1], context[2]]


def _ar3_quadratic_features(context: list[float]) -> list[float]:
    a, b, c = context
    return [
        1.0,
        a,
        b,
        c,
        a * a,
        b * b,
        c * c,
        a * b,
        b * c,
        a * c,
    ]


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _predict_repeat_last(context: list[float], _: list[float] | None) -> float:
    return context[2]


def _predict_mean_3(context: list[float], _: list[float] | None) -> float:
    return sum(context) / 3.0


def _predict_linear_trend(context: list[float], _: list[float] | None) -> float:
    d1 = context[1] - context[0]
    d2 = context[2] - context[1]
    return context[2] + (d1 + d2) / 2.0


def _predict_ar3_linear(context: list[float], params: list[float] | None) -> float:
    if params is None:
        return float("nan")
    return _dot(_ar3_linear_features(context), params)


def _predict_ar3_quadratic(context: list[float], params: list[float] | None) -> float:
    if params is None:
        return float("nan")
    return _dot(_ar3_quadratic_features(context), params)


def _format_ar3_linear_formula(params: list[float] | None) -> str:
    if params is None:
        return "unavailable"

    b0, b1, b2, b3 = params
    return (
        "next = "
        f"{b0:.6f} + "
        f"{b1:.6f}*x(t-2) + "
        f"{b2:.6f}*x(t-1) + "
        f"{b3:.6f}*x(t)"
    )


def _format_ar3_quadratic_formula(params: list[float] | None) -> str:
    if params is None:
        return "unavailable"

    (
        b0,
        b1,
        b2,
        b3,
        b4,
        b5,
        b6,
        b7,
        b8,
        b9,
    ) = params

    return (
        "next = "
        f"{b0:.6f} + "
        f"{b1:.6f}*x(t-2) + {b2:.6f}*x(t-1) + {b3:.6f}*x(t) + "
        f"{b4:.6f}*x(t-2)^2 + {b5:.6f}*x(t-1)^2 + {b6:.6f}*x(t)^2 + "
        f"{b7:.6f}*x(t-2)*x(t-1) + {b8:.6f}*x(t-1)*x(t) + {b9:.6f}*x(t-2)*x(t)"
    )


def evaluate_full_series_predictors(
    filename: str,
    context_size: int = 3,
    max_horizon: int | None = None,
) -> dict:
    """
    Given any 3 stability changes (including positives), predicts all
    following stability changes and compares those forecasts to reality.

    Uses rolling windows across the full dataset and evaluates multiple
    predictor families to identify the best next-change equation.
    """

    if context_size != 3:
        raise ValueError("This method currently requires context_size=3")

    with open(filename, "r") as f:
        results = json.load(f)

    next_step_contexts: list[list[float]] = []
    next_step_targets: list[float] = []

    for r in results:
        changes = r["stability_changes"]
        if len(changes) <= context_size:
            continue

        for i in range(0, len(changes) - context_size):
            context = [float(changes[i]), float(changes[i + 1]), float(changes[i + 2])]
            target = float(changes[i + context_size])
            next_step_contexts.append(context)
            next_step_targets.append(target)

    ar3_linear_params = _fit_linear_regression(
        features=[_ar3_linear_features(ctx) for ctx in next_step_contexts],
        targets=next_step_targets,
    )

    ar3_quadratic_params = _fit_linear_regression(
        features=[_ar3_quadratic_features(ctx) for ctx in next_step_contexts],
        targets=next_step_targets,
    )

    predictor_specs = {
        "repeat_last": {
            "predict_fn": _predict_repeat_last,
            "params": None,
            "formula": "next = x(t)",
        },
        "mean_3": {
            "predict_fn": _predict_mean_3,
            "params": None,
            "formula": "next = (x(t-2) + x(t-1) + x(t)) / 3",
        },
        "linear_trend": {
            "predict_fn": _predict_linear_trend,
            "params": None,
            "formula": "next = x(t) + ((x(t)-x(t-1)) + (x(t-1)-x(t-2))) / 2",
        },
        "ar3_linear": {
            "predict_fn": _predict_ar3_linear,
            "params": ar3_linear_params,
            "formula": _format_ar3_linear_formula(ar3_linear_params),
        },
        "ar3_quadratic": {
            "predict_fn": _predict_ar3_quadratic,
            "params": ar3_quadratic_params,
            "formula": _format_ar3_quadratic_formula(ar3_quadratic_params),
        },
    }

    model_names = list(predictor_specs.keys())
    per_model_errors: dict[str, list[float]] = {name: [] for name in model_names}
    per_model_cases: dict[str, int] = {name: 0 for name in model_names}
    per_model_points: dict[str, int] = {name: 0 for name in model_names}
    per_model_within_1: dict[str, int] = {name: 0 for name in model_names}
    per_model_within_2: dict[str, int] = {name: 0 for name in model_names}
    per_model_sign_hits: dict[str, int] = {name: 0 for name in model_names}

    total_cases = 0
    skipped_too_short = 0

    for r in results:
        changes = r["stability_changes"]
        if len(changes) <= context_size:
            skipped_too_short += 1
            continue

        for start in range(0, len(changes) - context_size):
            context = [
                float(changes[start]),
                float(changes[start + 1]),
                float(changes[start + 2]),
            ]

            actual_future = [float(x) for x in changes[start + context_size:]]
            if max_horizon is not None:
                actual_future = actual_future[:max_horizon]

            if not actual_future:
                continue

            total_cases += 1

            for model_name in model_names:
                predict_fn = predictor_specs[model_name]["predict_fn"]
                params = predictor_specs[model_name]["params"]

                state = context[:]
                valid_case = True

                for actual_value in actual_future:
                    predicted_value = predict_fn(state, params)

                    if not math.isfinite(predicted_value):
                        valid_case = False
                        break

                    error = predicted_value - actual_value
                    per_model_errors[model_name].append(error)
                    per_model_points[model_name] += 1

                    abs_error = abs(error)
                    if abs_error <= 1:
                        per_model_within_1[model_name] += 1
                    if abs_error <= 2:
                        per_model_within_2[model_name] += 1

                    if predicted_value == 0 and actual_value == 0:
                        per_model_sign_hits[model_name] += 1
                    elif predicted_value * actual_value > 0:
                        per_model_sign_hits[model_name] += 1

                    state = [state[1], state[2], predicted_value]

                if valid_case:
                    per_model_cases[model_name] += 1

    model_metrics: dict[str, dict[str, float | int | str | None]] = {}

    for model_name in model_names:
        errors = per_model_errors[model_name]
        points = per_model_points[model_name]
        base_metrics = _safe_error_metrics(errors)

        model_metrics[model_name] = {
            "formula": predictor_specs[model_name]["formula"],
            "valid_cases": per_model_cases[model_name],
            "evaluated_points": points,
            "mae": base_metrics["mae"],
            "rmse": base_metrics["rmse"],
            "median_abs_error": base_metrics["median_abs_error"],
            "within_1_rate": (per_model_within_1[model_name] / points) if points else None,
            "within_2_rate": (per_model_within_2[model_name] / points) if points else None,
            "sign_accuracy": (per_model_sign_hits[model_name] / points) if points else None,
        }

    ranked_models = []
    for name, metrics in model_metrics.items():
        if metrics["mae"] is None or metrics["rmse"] is None:
            continue

        ranked_models.append((
            name,
            metrics["mae"],
            metrics["rmse"],
            -(metrics["within_1_rate"] or 0),
        ))

    ranked_models.sort(key=lambda item: (item[1], item[2], item[3]))
    best_model = ranked_models[0][0] if ranked_models else None

    summary = {
        "config": {
            "context_size": context_size,
            "max_horizon": max_horizon,
        },
        "dataset": {
            "total_runs": len(results),
            "total_cases": total_cases,
            "skipped_too_short": skipped_too_short,
            "training_points_for_next_step": len(next_step_targets),
        },
        "models": model_metrics,
        "best_model": best_model,
    }

    print("\nFull Series Predictor Comparison")
    print("-" * 40)
    print(f"Total runs             : {len(results)}")
    print(f"Total forecast cases   : {total_cases}")
    print(f"Skipped (too short)    : {skipped_too_short}")
    print(f"Training next-step pts : {len(next_step_targets)}")

    for name in model_names:
        metrics = model_metrics[name]
        print(f"\n{name.title()} model")
        print(f"Formula           : {metrics['formula']}")
        print(f"Valid cases       : {metrics['valid_cases']}")
        print(f"Evaluated points  : {metrics['evaluated_points']}")
        if metrics["mae"] is None:
            print("No valid forecasts")
            continue

        print(f"MAE               : {metrics['mae']:.3f}")
        print(f"RMSE              : {metrics['rmse']:.3f}")
        print(f"Median abs error  : {metrics['median_abs_error']:.3f}")
        print(f"Within +/-1       : {metrics['within_1_rate']:.2%}")
        print(f"Within +/-2       : {metrics['within_2_rate']:.2%}")
        print(f"Sign accuracy     : {metrics['sign_accuracy']:.2%}")

    print("\nBest model:", best_model if best_model else "None")

    return summary


def _build_capped_observed_changes(
    raw_changes: list[int],
    start_stability: int = 50,
) -> tuple[list[int], list[int]]:
    """
    Converts raw intended stability deltas into observed applied deltas under
    [0, 100] stability capping.

    Returns:
    - observed_changes: applied delta each step after cap
    - stability_after_each_step: stability after each applied change
    """

    stability = start_stability
    observed_changes: list[int] = []
    stability_after_each_step: list[int] = []

    for raw in raw_changes:
        next_stability = max(0, min(100, stability + raw))
        applied_change = next_stability - stability

        observed_changes.append(applied_change)
        stability_after_each_step.append(next_stability)

        stability = next_stability

    return observed_changes, stability_after_each_step


def _find_first_two_negative_trigger(changes: list[int]) -> int | None:
    """Returns the index of the second negative in the first consecutive pair."""
    for i in range(1, len(changes)):
        if changes[i - 1] < 0 and changes[i] < 0:
            return i
    return None


def _find_first_n_negative_trigger(changes: list[int], n: int) -> int | None:
    """Returns index of the nth value in first streak of n consecutive negatives."""
    if n <= 1:
        return None

    streak = 0
    for i, value in enumerate(changes):
        if value < 0:
            streak += 1
            if streak >= n:
                return i
        else:
            streak = 0

    return None


def _collect_n_negative_trigger_records(
    results: list[dict],
    n: int,
    start_stability: int,
) -> tuple[list[tuple[list[float], float, int]], int, int, int]:
    trigger_records: list[tuple[list[float], float, int]] = []
    skipped_no_trigger = 0
    skipped_not_reaching_zero = 0
    runs_with_trigger_and_zero = 0

    for r in results:
        raw_changes = r["stability_changes"]
        trigger_idx = _find_first_n_negative_trigger(raw_changes, n)

        if trigger_idx is None:
            skipped_no_trigger += 1
            continue

        stability = start_stability
        stability_after_each_step: list[int] = []
        for change in raw_changes:
            stability = max(0, min(100, stability + change))
            stability_after_each_step.append(stability)

        current_stability = float(stability_after_each_step[trigger_idx])

        actual_remaining_steps: int | None = None
        for j in range(trigger_idx + 1, len(stability_after_each_step)):
            if stability_after_each_step[j] <= 0:
                actual_remaining_steps = j - trigger_idx
                break

        if actual_remaining_steps is None:
            skipped_not_reaching_zero += 1
            continue

        seen_changes = [float(x) for x in raw_changes[:trigger_idx + 1]]
        trigger_records.append((seen_changes, current_stability, actual_remaining_steps))
        runs_with_trigger_and_zero += 1

    return (
        trigger_records,
        runs_with_trigger_and_zero,
        skipped_no_trigger,
        skipped_not_reaching_zero,
    )


def _predict_n_negative_model_steps(
    model_name: str,
    seen_changes: list[float],
    current_stability: float,
    base: list[float],
    base_quad: list[float],
    chain_linear_params: list[float] | None,
    chain_quadratic_params: list[float] | None,
    max_forecast_steps: int,
) -> tuple[int, bool]:
    timeout = False

    seq_mean = sum(seen_changes) / len(seen_changes)
    neg_values = [x for x in seen_changes if x < 0]
    neg_mean = (sum(neg_values) / len(neg_values)) if neg_values else 0.0

    if model_name == "drift_mean_seen":
        if seq_mean >= 0:
            timeout = True
            predicted_remaining_steps = max_forecast_steps
        else:
            predicted_remaining_steps = _clamp_round_steps(
                current_stability / (-seq_mean),
                max_forecast_steps,
            )

    elif model_name == "mean_negative_only":
        if neg_mean == 0:
            timeout = True
            predicted_remaining_steps = max_forecast_steps
        else:
            predicted_remaining_steps = _clamp_round_steps(
                current_stability / (-neg_mean),
                max_forecast_steps,
            )

    elif model_name == "chain_linear_reg":
        if chain_linear_params is None:
            timeout = True
            predicted_remaining_steps = max_forecast_steps
        else:
            predicted_remaining_steps = _clamp_round_steps(
                _dot(base, chain_linear_params),
                max_forecast_steps,
            )

    elif model_name == "chain_quadratic_reg":
        if chain_quadratic_params is None:
            timeout = True
            predicted_remaining_steps = max_forecast_steps
        else:
            predicted_remaining_steps = _clamp_round_steps(
                _dot(base_quad, chain_quadratic_params),
                max_forecast_steps,
            )

    else:
        timeout = True
        predicted_remaining_steps = max_forecast_steps

    return predicted_remaining_steps, timeout


def _predict_next_from_seen(
    model_name: str,
    seen_changes: list[float],
    ar3_linear_params: list[float] | None,
    ar3_quadratic_params: list[float] | None,
) -> float:
    if model_name == "last_change":
        return seen_changes[-1]

    if model_name == "mean_seen":
        return sum(seen_changes) / len(seen_changes)

    if model_name == "last_two_mean":
        return (seen_changes[-1] + seen_changes[-2]) / 2.0

    if model_name == "ar3_linear":
        if ar3_linear_params is None:
            return float("nan")
        context = seen_changes[-3:]
        return _dot(_ar3_linear_features(context), ar3_linear_params)

    if model_name == "ar3_quadratic":
        if ar3_quadratic_params is None:
            return float("nan")
        context = seen_changes[-3:]
        return _dot(_ar3_quadratic_features(context), ar3_quadratic_params)

    return float("nan")


def _zero_semantic_stats(
    seen_changes: list[float],
    start_stability: int,
) -> tuple[float, float, float, float, float]:
    """
    Splits observed zero changes into semantic buckets:
    - zero_at_top: observed 0 while stability was 100 (hidden positive raw change)
    - zero_at_bottom: observed 0 while stability was 0 (hidden negative raw change)
    - zero_interior: observed 0 while stability was strictly between bounds

    Also returns:
    - longest_zero_run
    - trailing_zero_run
    """

    stability = float(start_stability)
    zero_at_top = 0.0
    zero_at_bottom = 0.0
    zero_interior = 0.0

    longest_zero_run = 0.0
    current_zero_run = 0.0

    for delta in seen_changes:
        if delta == 0:
            if stability >= 100:
                zero_at_top += 1.0
            elif stability <= 0:
                zero_at_bottom += 1.0
            else:
                zero_interior += 1.0

            current_zero_run += 1.0
            if current_zero_run > longest_zero_run:
                longest_zero_run = current_zero_run
        else:
            current_zero_run = 0.0

        stability = max(0.0, min(100.0, stability + delta))

    trailing_zero_run = 0.0
    for delta in reversed(seen_changes):
        if delta == 0:
            trailing_zero_run += 1.0
        else:
            break

    return (
        zero_at_top,
        zero_at_bottom,
        zero_interior,
        longest_zero_run,
        trailing_zero_run,
    )


def _full_chain_features(
    seen_changes: list[float],
    current_stability: float,
    start_stability: int,
) -> list[float]:
    n = len(seen_changes)
    seq_sum = sum(seen_changes)
    seq_mean = seq_sum / n if n else 0.0
    seq_min = min(seen_changes) if seen_changes else 0.0
    seq_max = max(seen_changes) if seen_changes else 0.0

    variance = 0.0
    if n:
        variance = sum((x - seq_mean) ** 2 for x in seen_changes) / n
    seq_std = math.sqrt(variance)

    last1 = seen_changes[-1] if n >= 1 else 0.0
    last2 = seen_changes[-2] if n >= 2 else 0.0
    last3 = seen_changes[-3] if n >= 3 else 0.0

    neg_values = [x for x in seen_changes if x < 0]
    neg_count = float(len(neg_values))
    zero_count = float(sum(1 for x in seen_changes if x == 0))
    pos_count = float(sum(1 for x in seen_changes if x > 0))
    neg_mean = (sum(neg_values) / len(neg_values)) if neg_values else 0.0

    (
        zero_at_top,
        zero_at_bottom,
        zero_interior,
        longest_zero_run,
        trailing_zero_run,
    ) = _zero_semantic_stats(seen_changes, start_stability)

    pos_values = [x for x in seen_changes if x > 0]
    pos_mean = (sum(pos_values) / len(pos_values)) if pos_values else 0.0

    return [
        1.0,
        float(current_stability),
        float(n),
        seq_sum,
        seq_mean,
        seq_std,
        seq_min,
        seq_max,
        last1,
        last2,
        last3,
        neg_count,
        zero_count,
        pos_count,
        neg_mean,
        zero_at_top,
        zero_at_bottom,
        zero_interior,
        longest_zero_run,
        trailing_zero_run,
        pos_mean,
    ]


def _full_chain_quadratic_features(base: list[float]) -> list[float]:
    (
        bias,
        current_stability,
        length,
        seq_sum,
        seq_mean,
        seq_std,
        seq_min,
        seq_max,
        last1,
        last2,
        last3,
        neg_count,
        zero_count,
        pos_count,
        neg_mean,
        zero_at_top,
        zero_at_bottom,
        zero_interior,
        longest_zero_run,
        trailing_zero_run,
        pos_mean,
    ) = base

    return [
        bias,
        current_stability,
        length,
        seq_sum,
        seq_mean,
        seq_std,
        seq_min,
        seq_max,
        last1,
        last2,
        last3,
        neg_count,
        zero_count,
        pos_count,
        neg_mean,
        zero_at_top,
        zero_at_bottom,
        zero_interior,
        longest_zero_run,
        trailing_zero_run,
        pos_mean,
        current_stability * current_stability,
        seq_mean * seq_mean,
        seq_std * seq_std,
        last1 * last1,
        last2 * last2,
        last3 * last3,
        neg_mean * neg_mean,
        current_stability * seq_mean,
        current_stability * last1,
        seq_mean * last1,
        seq_mean * last2,
        seq_mean * last3,
        neg_count * seq_mean,
        zero_count * seq_mean,
        zero_at_top * seq_mean,
        zero_interior * seq_mean,
        trailing_zero_run * last1,
    ]


def _clamp_round_steps(predicted: float, max_forecast_steps: int) -> int:
    if not math.isfinite(predicted):
        return max_forecast_steps

    rounded = int(round(predicted))
    if rounded < 0:
        return 0
    if rounded > max_forecast_steps:
        return max_forecast_steps
    return rounded


def _is_censored_observed_step(
    stability_before: float,
    observed_delta: float,
    stability_after: float,
) -> bool:
    """
    Heuristic censoring detector for observed changes under [0, 100] cap.
    True means observed delta may hide larger raw pressure.
    """

    if stability_before >= 100 and observed_delta == 0:
        return True

    if stability_before <= 0 and observed_delta == 0:
        return True

    if stability_before < 100 and stability_after >= 100 and observed_delta > 0:
        return True

    if stability_before > 0 and stability_after <= 0 and observed_delta < 0:
        return True

    return False


def _collect_uncensored_next_step_data(
    capped_sequences: list[list[int]],
    start_stability: int,
) -> tuple[list[list[float]], list[float]]:
    """Collects AR3 next-step training data from likely uncensored transitions only."""

    features: list[list[float]] = []
    targets: list[float] = []

    for changes in capped_sequences:
        if len(changes) < 4:
            continue

        stability = float(start_stability)
        stability_after: list[float] = []
        for change in changes:
            stability = max(0.0, min(100.0, stability + float(change)))
            stability_after.append(stability)

        for idx in range(3, len(changes)):
            context = [
                float(changes[idx - 3]),
                float(changes[idx - 2]),
                float(changes[idx - 1]),
            ]
            target = float(changes[idx])

            before = float(stability_after[idx - 1])
            after = float(stability_after[idx])

            if _is_censored_observed_step(before, target, after):
                continue

            features.append(_ar3_linear_features(context))
            targets.append(target)

    return features, targets


def _impute_seen_changes(
    seen_changes: list[float],
    start_stability: int,
    uncensored_ar3_params: list[float] | None,
) -> list[float]:
    """
    Replaces likely-censored observed deltas with a proxy estimate from
    preceding imputed context while preserving cap-consistent direction.
    """

    if uncensored_ar3_params is None:
        return seen_changes[:]

    imputed: list[float] = []
    stability_before = float(start_stability)

    for observed in seen_changes:
        stability_after = max(0.0, min(100.0, stability_before + observed))
        value = observed

        if len(imputed) >= 3 and _is_censored_observed_step(stability_before, observed, stability_after):
            predicted = _dot(_ar3_linear_features(imputed[-3:]), uncensored_ar3_params)

            if stability_before >= 100:
                value = max(float(observed), max(0.0, predicted))
            elif stability_before <= 0:
                value = min(float(observed), min(0.0, predicted))
            elif stability_after >= 100 and observed > 0:
                value = max(float(observed), predicted)
            elif stability_after <= 0 and observed < 0:
                value = min(float(observed), predicted)

        imputed.append(float(value))
        stability_before = stability_after

    return imputed


def evaluate_two_negative_trigger_steps_to_zero(
    filename: str,
    start_stability: int = 50,
    max_forecast_steps: int = 500,
) -> dict:
    """
    Rule set:
    - Stability starts at 50 and is capped to [0, 100].
    - Models only see capped observed changes (applied deltas), not raw changes.
    - For each run, after first two consecutive negative observed changes,
      predict how many more changes are needed to reach stability 0.

    Compares multiple algorithms and ranks by MAE, then RMSE, then exact-match.
    """

    with open(filename, "r") as f:
        results = json.load(f)

    capped_sequences: list[list[int]] = []
    for r in results:
        observed, _ = _build_capped_observed_changes(
            raw_changes=r["stability_changes"],
            start_stability=start_stability,
        )
        capped_sequences.append(observed)

    model_names = [
        "drift_mean_seen",
        "mean_negative_only",
        "chain_linear_reg",
        "chain_quadratic_reg",
        "chain_linear_reg_imputed",
        "chain_quadratic_reg_imputed",
    ]

    errors_by_model: dict[str, list[float]] = {name: [] for name in model_names}
    exact_by_model: dict[str, int] = {name: 0 for name in model_names}
    within_1_by_model: dict[str, int] = {name: 0 for name in model_names}
    within_2_by_model: dict[str, int] = {name: 0 for name in model_names}
    valid_by_model: dict[str, int] = {name: 0 for name in model_names}
    timeout_by_model: dict[str, int] = {name: 0 for name in model_names}

    total_runs = len(results)
    trigger_runs = 0
    skipped_no_trigger = 0
    skipped_not_reaching_zero = 0

    trigger_records: list[tuple[list[float], float, int]] = []

    for capped_changes in capped_sequences:
        trigger_idx = _find_first_two_negative_trigger(capped_changes)
        if trigger_idx is None:
            skipped_no_trigger += 1
            continue

        # Rebuild the stability timeline from observed capped changes.
        stability = start_stability
        stability_after_each_step: list[int] = []
        for change in capped_changes:
            stability = max(0, min(100, stability + change))
            stability_after_each_step.append(stability)

        current_stability = stability_after_each_step[trigger_idx]

        actual_remaining_steps: int | None = None
        for j in range(trigger_idx + 1, len(stability_after_each_step)):
            if stability_after_each_step[j] <= 0:
                actual_remaining_steps = j - trigger_idx
                break

        if actual_remaining_steps is None:
            skipped_not_reaching_zero += 1
            continue

        trigger_runs += 1

        seen_changes = [float(x) for x in capped_changes[:trigger_idx + 1]]

        trigger_records.append((seen_changes, float(current_stability), actual_remaining_steps))

    uncensored_features, uncensored_targets = _collect_uncensored_next_step_data(
        capped_sequences,
        start_stability,
    )
    uncensored_ar3_params = _fit_linear_regression(uncensored_features, uncensored_targets)

    trigger_records_imputed: list[tuple[list[float], float, int]] = []
    for seen_changes, current_stability, actual_steps in trigger_records:
        imputed_seen = _impute_seen_changes(
            seen_changes=seen_changes,
            start_stability=start_stability,
            uncensored_ar3_params=uncensored_ar3_params,
        )
        trigger_records_imputed.append((imputed_seen, current_stability, actual_steps))

    train_linear_features = [
        _full_chain_features(seen_changes, current_stability, start_stability)
        for seen_changes, current_stability, _ in trigger_records
    ]
    train_quadratic_features = [
        _full_chain_quadratic_features(base)
        for base in train_linear_features
    ]
    train_targets = [float(actual_steps) for _, _, actual_steps in trigger_records]

    train_linear_features_imputed = [
        _full_chain_features(seen_changes, current_stability, start_stability)
        for seen_changes, current_stability, _ in trigger_records_imputed
    ]
    train_quadratic_features_imputed = [
        _full_chain_quadratic_features(base)
        for base in train_linear_features_imputed
    ]

    chain_linear_params = _fit_linear_regression(train_linear_features, train_targets)
    chain_quadratic_params = _fit_linear_regression(train_quadratic_features, train_targets)
    chain_linear_params_imputed = _fit_linear_regression(train_linear_features_imputed, train_targets)
    chain_quadratic_params_imputed = _fit_linear_regression(train_quadratic_features_imputed, train_targets)

    for idx, (seen_changes, current_stability, actual_remaining_steps) in enumerate(trigger_records):
        seen_changes_imputed = trigger_records_imputed[idx][0]
        seq_mean = sum(seen_changes) / len(seen_changes)
        neg_values = [x for x in seen_changes if x < 0]
        neg_mean = (sum(neg_values) / len(neg_values)) if neg_values else 0.0

        base = _full_chain_features(seen_changes, current_stability, start_stability)
        base_quad = _full_chain_quadratic_features(base)
        base_imputed = _full_chain_features(seen_changes_imputed, current_stability, start_stability)
        base_quad_imputed = _full_chain_quadratic_features(base_imputed)

        for model_name in model_names:
            valid_by_model[model_name] += 1

            if model_name == "drift_mean_seen":
                if seq_mean >= 0:
                    timeout_by_model[model_name] += 1
                    predicted_remaining_steps = max_forecast_steps
                else:
                    predicted_remaining_steps = _clamp_round_steps(
                        current_stability / (-seq_mean),
                        max_forecast_steps,
                    )

            elif model_name == "mean_negative_only":
                if neg_mean == 0:
                    timeout_by_model[model_name] += 1
                    predicted_remaining_steps = max_forecast_steps
                else:
                    predicted_remaining_steps = _clamp_round_steps(
                        current_stability / (-neg_mean),
                        max_forecast_steps,
                    )

            elif model_name == "chain_linear_reg":
                if chain_linear_params is None:
                    timeout_by_model[model_name] += 1
                    predicted_remaining_steps = max_forecast_steps
                else:
                    predicted_remaining_steps = _clamp_round_steps(
                        _dot(base, chain_linear_params),
                        max_forecast_steps,
                    )

            elif model_name == "chain_quadratic_reg":
                if chain_quadratic_params is None:
                    timeout_by_model[model_name] += 1
                    predicted_remaining_steps = max_forecast_steps
                else:
                    predicted_remaining_steps = _clamp_round_steps(
                        _dot(base_quad, chain_quadratic_params),
                        max_forecast_steps,
                    )

            elif model_name == "chain_linear_reg_imputed":
                if chain_linear_params_imputed is None:
                    timeout_by_model[model_name] += 1
                    predicted_remaining_steps = max_forecast_steps
                else:
                    predicted_remaining_steps = _clamp_round_steps(
                        _dot(base_imputed, chain_linear_params_imputed),
                        max_forecast_steps,
                    )

            elif model_name == "chain_quadratic_reg_imputed":
                if chain_quadratic_params_imputed is None:
                    timeout_by_model[model_name] += 1
                    predicted_remaining_steps = max_forecast_steps
                else:
                    predicted_remaining_steps = _clamp_round_steps(
                        _dot(base_quad_imputed, chain_quadratic_params_imputed),
                        max_forecast_steps,
                    )

            else:
                timeout_by_model[model_name] += 1
                predicted_remaining_steps = max_forecast_steps

            error = predicted_remaining_steps - actual_remaining_steps
            errors_by_model[model_name].append(error)

            abs_error = abs(error)
            if abs_error == 0:
                exact_by_model[model_name] += 1
            if abs_error <= 1:
                within_1_by_model[model_name] += 1
            if abs_error <= 2:
                within_2_by_model[model_name] += 1

    metrics_by_model: dict[str, dict[str, float | int | str | None]] = {}
    for model_name in model_names:
        errors = errors_by_model[model_name]
        valid = valid_by_model[model_name]
        err = _safe_error_metrics(errors)

        if model_name == "last_change":
            formula = "unused"
        elif model_name == "drift_mean_seen":
            formula = "steps ~= current_stability / -mean(all_seen_changes)"
        elif model_name == "mean_negative_only":
            formula = "steps ~= current_stability / -mean(seen_negative_changes)"
        elif model_name == "chain_linear_reg":
            formula = "steps ~= linear_regression(full_seen_chain_features)"
        elif model_name == "chain_quadratic_reg":
            formula = "steps ~= quadratic_regression(full_seen_chain_features)"
        elif model_name == "chain_linear_reg_imputed":
            formula = "steps ~= linear_regression(full_seen_chain_features_with_decap_imputation)"
        elif model_name == "chain_quadratic_reg_imputed":
            formula = "steps ~= quadratic_regression(full_seen_chain_features_with_decap_imputation)"
        else:
            formula = "unknown"

        metrics_by_model[model_name] = {
            "formula": formula,
            "valid_predictions": valid,
            "timeout_or_nonfinite_predictions": timeout_by_model[model_name],
            "mae": err["mae"],
            "rmse": err["rmse"],
            "median_abs_error": err["median_abs_error"],
            "exact_match_rate": (exact_by_model[model_name] / valid) if valid else None,
            "within_1_rate": (within_1_by_model[model_name] / valid) if valid else None,
            "within_2_rate": (within_2_by_model[model_name] / valid) if valid else None,
        }

    ranked = []
    for model_name, metrics in metrics_by_model.items():
        if metrics["mae"] is None or metrics["rmse"] is None:
            continue

        ranked.append((
            model_name,
            metrics["mae"],
            metrics["rmse"],
            -(metrics["exact_match_rate"] or 0),
        ))

    ranked.sort(key=lambda row: (row[1], row[2], row[3]))
    best_model = ranked[0][0] if ranked else None

    summary = {
        "config": {
            "start_stability": start_stability,
            "max_forecast_steps": max_forecast_steps,
            "trigger_rule": "first_two_consecutive_negative_observed_changes",
            "observed_rule": "apply_raw_change_then_cap_stability_to_[0,100]",
            "zero_semantics": "0 at cap boundary means hidden raw change, not necessarily no pressure",
            "decap_imputation": "likely-censored observed deltas replaced by AR3 estimate from uncensored transitions",
        },
        "dataset": {
            "total_runs": total_runs,
            "runs_with_trigger_and_zero": trigger_runs,
            "skipped_no_trigger": skipped_no_trigger,
            "skipped_not_reaching_zero": skipped_not_reaching_zero,
            "training_trigger_points": len(train_targets),
            "training_uncensored_next_step_points": len(uncensored_targets),
        },
        "models": metrics_by_model,
        "best_model": best_model,
    }

    print("\nTwo-Negative Trigger: Steps-To-Zero Prediction")
    print("-" * 52)
    print(f"Total runs                    : {total_runs}")
    print(f"Runs with trigger and zero    : {trigger_runs}")
    print(f"Skipped (no trigger)          : {skipped_no_trigger}")
    print(f"Skipped (never reaches zero)  : {skipped_not_reaching_zero}")
    print(f"Training trigger points       : {len(train_targets)}")

    for model_name in model_names:
        m = metrics_by_model[model_name]
        print(f"\n{model_name} model")
        print(f"Formula           : {m['formula']}")
        print(f"Valid predictions : {m['valid_predictions']}")
        if m["mae"] is None:
            print("No valid predictions")
            continue

        print(f"MAE               : {m['mae']:.3f}")
        print(f"RMSE              : {m['rmse']:.3f}")
        print(f"Median abs error  : {m['median_abs_error']:.3f}")
        print(f"Exact match rate  : {m['exact_match_rate']:.2%}")
        print(f"Within +/-1       : {m['within_1_rate']:.2%}")
        print(f"Within +/-2       : {m['within_2_rate']:.2%}")

    print("\nBest model:", best_model if best_model else "None")

    return summary


def evaluate_n_negative_trigger_steps_to_zero(
    filename: str,
    n: int,
    start_stability: int = 100,
    max_forecast_steps: int = 500,
) -> dict:
    """
    Rule set:
    - Stability starts at 100 and is capped to [0, 100].
    - Trigger is first streak of n consecutive negative raw stability changes.
    - Predict how many additional changes are needed to reach stability 0.

    Compares multiple predictors and ranks by MAE, then RMSE, then exact-match.
    """

    if n <= 1:
        raise ValueError("n must be > 1")

    with open(filename, "r") as f:
        results = json.load(f)

    model_names = [
        "drift_mean_seen",
        "mean_negative_only",
        "chain_linear_reg",
        "chain_quadratic_reg",
    ]

    errors_by_model: dict[str, list[float]] = {name: [] for name in model_names}
    exact_by_model: dict[str, int] = {name: 0 for name in model_names}
    within_1_by_model: dict[str, int] = {name: 0 for name in model_names}
    within_2_by_model: dict[str, int] = {name: 0 for name in model_names}
    valid_by_model: dict[str, int] = {name: 0 for name in model_names}
    timeout_by_model: dict[str, int] = {name: 0 for name in model_names}

    total_runs = len(results)
    (
        trigger_records,
        runs_with_trigger_and_zero,
        skipped_no_trigger,
        skipped_not_reaching_zero,
    ) = _collect_n_negative_trigger_records(results, n, start_stability)

    train_linear_features = [
        _full_chain_features(seen_changes, current_stability, start_stability)
        for seen_changes, current_stability, _ in trigger_records
    ]
    train_quadratic_features = [
        _full_chain_quadratic_features(base)
        for base in train_linear_features
    ]
    train_targets = [float(actual_steps) for _, _, actual_steps in trigger_records]

    chain_linear_params = _fit_linear_regression(train_linear_features, train_targets)
    chain_quadratic_params = _fit_linear_regression(train_quadratic_features, train_targets)

    for seen_changes, current_stability, actual_remaining_steps in trigger_records:
        base = _full_chain_features(seen_changes, current_stability, start_stability)
        base_quad = _full_chain_quadratic_features(base)

        for model_name in model_names:
            valid_by_model[model_name] += 1

            predicted_remaining_steps, timeout = _predict_n_negative_model_steps(
                model_name=model_name,
                seen_changes=seen_changes,
                current_stability=current_stability,
                base=base,
                base_quad=base_quad,
                chain_linear_params=chain_linear_params,
                chain_quadratic_params=chain_quadratic_params,
                max_forecast_steps=max_forecast_steps,
            )

            if timeout:
                timeout_by_model[model_name] += 1

            error = predicted_remaining_steps - actual_remaining_steps
            errors_by_model[model_name].append(error)

            abs_error = abs(error)
            if abs_error == 0:
                exact_by_model[model_name] += 1
            if abs_error <= 1:
                within_1_by_model[model_name] += 1
            if abs_error <= 2:
                within_2_by_model[model_name] += 1

    metrics_by_model: dict[str, dict[str, float | int | str | None]] = {}
    for model_name in model_names:
        errors = errors_by_model[model_name]
        valid = valid_by_model[model_name]
        err = _safe_error_metrics(errors)

        if model_name == "drift_mean_seen":
            formula = "steps ~= current_stability / -mean(all_seen_changes)"
        elif model_name == "mean_negative_only":
            formula = "steps ~= current_stability / -mean(seen_negative_changes)"
        elif model_name == "chain_linear_reg":
            formula = "steps ~= linear_regression(full_seen_chain_features)"
        else:
            formula = "steps ~= quadratic_regression(full_seen_chain_features)"

        metrics_by_model[model_name] = {
            "formula": formula,
            "valid_predictions": valid,
            "timeout_or_nonfinite_predictions": timeout_by_model[model_name],
            "mae": err["mae"],
            "rmse": err["rmse"],
            "median_abs_error": err["median_abs_error"],
            "exact_match_rate": (exact_by_model[model_name] / valid) if valid else None,
            "within_1_rate": (within_1_by_model[model_name] / valid) if valid else None,
            "within_2_rate": (within_2_by_model[model_name] / valid) if valid else None,
        }

    ranked = []
    for model_name, metrics in metrics_by_model.items():
        if metrics["mae"] is None or metrics["rmse"] is None:
            continue

        ranked.append((
            model_name,
            metrics["mae"],
            metrics["rmse"],
            -(metrics["exact_match_rate"] or 0),
        ))

    ranked.sort(key=lambda row: (row[1], row[2], row[3]))
    best_model = ranked[0][0] if ranked else None

    summary = {
        "config": {
            "start_stability": start_stability,
            "n": n,
            "max_forecast_steps": max_forecast_steps,
            "trigger_rule": "first_streak_of_n_consecutive_negative_raw_changes",
            "stability_rule": "apply_raw_change_then_cap_stability_to_[0,100]",
        },
        "dataset": {
            "total_runs": total_runs,
            "runs_with_trigger_and_zero": runs_with_trigger_and_zero,
            "skipped_no_trigger": skipped_no_trigger,
            "skipped_not_reaching_zero": skipped_not_reaching_zero,
            "training_trigger_points": len(train_targets),
        },
        "models": metrics_by_model,
        "best_model": best_model,
    }

    print("\nN-Negative Trigger: Steps-To-Zero Prediction")
    print("-" * 52)
    print(f"n                             : {n}")
    print(f"Total runs                    : {total_runs}")
    print(f"Runs with trigger and zero    : {runs_with_trigger_and_zero}")
    print(f"Skipped (no trigger)          : {skipped_no_trigger}")
    print(f"Skipped (never reaches zero)  : {skipped_not_reaching_zero}")
    print(f"Training trigger points       : {len(train_targets)}")

    for model_name in model_names:
        m = metrics_by_model[model_name]
        print(f"\n{model_name} model")
        print(f"Formula           : {m['formula']}")
        print(f"Valid predictions : {m['valid_predictions']}")
        if m["mae"] is None:
            print("No valid predictions")
            continue

        print(f"MAE               : {m['mae']:.3f}")
        print(f"RMSE              : {m['rmse']:.3f}")
        print(f"Median abs error  : {m['median_abs_error']:.3f}")
        print(f"Exact match rate  : {m['exact_match_rate']:.2%}")
        print(f"Within +/-1       : {m['within_1_rate']:.2%}")
        print(f"Within +/-2       : {m['within_2_rate']:.2%}")

    print("\nBest model:", best_model if best_model else "None")

    return summary


def predict_remaining_steps_live_n_negative(
    filename: str,
    changes: list[int],
    n: int,
    start_stability: int = 100,
    max_forecast_steps: int = 500,
) -> dict:
    """
    Trains models from filename and predicts remaining steps to zero for one
    live sequence using the best-ranked model from training.
    """

    if n <= 1:
        raise ValueError("n must be > 1")

    with open(filename, "r") as f:
        results = json.load(f)

    trigger_idx_live = _find_first_n_negative_trigger(changes, n)
    if trigger_idx_live is None:
        return {
            "predicted_remaining_steps": None,
            "best_model": None,
            "trigger_found": False,
            "message": "No streak of n consecutive negative changes found in input.",
        }

    (
        training_records,
        _,
        _,
        _,
    ) = _collect_n_negative_trigger_records(results, n, start_stability)

    if not training_records:
        return {
            "predicted_remaining_steps": None,
            "best_model": None,
            "trigger_found": True,
            "trigger_index": trigger_idx_live,
            "message": "No valid training records available for this n.",
        }

    train_linear_features = [
        _full_chain_features(seen_changes, current_stability, start_stability)
        for seen_changes, current_stability, _ in training_records
    ]
    train_quadratic_features = [
        _full_chain_quadratic_features(base)
        for base in train_linear_features
    ]
    train_targets = [float(actual_steps) for _, _, actual_steps in training_records]

    chain_linear_params = _fit_linear_regression(train_linear_features, train_targets)
    chain_quadratic_params = _fit_linear_regression(train_quadratic_features, train_targets)

    model_names = [
        "drift_mean_seen",
        "mean_negative_only",
        "chain_linear_reg",
        "chain_quadratic_reg",
    ]

    # Pick best model on training records with same ranking rules as evaluator.
    score_rows: list[tuple[str, float, float, float]] = []
    for model_name in model_names:
        model_errors: list[float] = []
        exact_hits = 0

        for seen_changes, current_stability, actual_remaining_steps in training_records:
            base = _full_chain_features(seen_changes, current_stability, start_stability)
            base_quad = _full_chain_quadratic_features(base)

            predicted, _ = _predict_n_negative_model_steps(
                model_name=model_name,
                seen_changes=seen_changes,
                current_stability=current_stability,
                base=base,
                base_quad=base_quad,
                chain_linear_params=chain_linear_params,
                chain_quadratic_params=chain_quadratic_params,
                max_forecast_steps=max_forecast_steps,
            )

            err = predicted - actual_remaining_steps
            model_errors.append(err)
            if err == 0:
                exact_hits += 1

        metrics = _safe_error_metrics(model_errors)
        if metrics["mae"] is None or metrics["rmse"] is None:
            continue

        exact_rate = exact_hits / len(model_errors) if model_errors else 0.0
        score_rows.append((model_name, metrics["mae"], metrics["rmse"], -exact_rate))

    score_rows.sort(key=lambda row: (row[1], row[2], row[3]))
    best_model = score_rows[0][0] if score_rows else None

    if best_model is None:
        return {
            "predicted_remaining_steps": None,
            "best_model": None,
            "trigger_found": True,
            "trigger_index": trigger_idx_live,
            "message": "No model could be scored from training data.",
        }

    stability = start_stability
    stability_after_each_step: list[int] = []
    for change in changes:
        stability = max(0, min(100, stability + change))
        stability_after_each_step.append(stability)

    current_stability_live = float(stability_after_each_step[trigger_idx_live])
    seen_changes_live = [float(x) for x in changes[:trigger_idx_live + 1]]
    base_live = _full_chain_features(seen_changes_live, current_stability_live, start_stability)
    base_quad_live = _full_chain_quadratic_features(base_live)

    predicted_steps, timeout = _predict_n_negative_model_steps(
        model_name=best_model,
        seen_changes=seen_changes_live,
        current_stability=current_stability_live,
        base=base_live,
        base_quad=base_quad_live,
        chain_linear_params=chain_linear_params,
        chain_quadratic_params=chain_quadratic_params,
        max_forecast_steps=max_forecast_steps,
    )

    return {
        "predicted_remaining_steps": predicted_steps,
        "best_model": best_model,
        "trigger_found": True,
        "trigger_index": trigger_idx_live,
        "current_stability_at_trigger": current_stability_live,
        "used_max_forecast_fallback": timeout,
    }