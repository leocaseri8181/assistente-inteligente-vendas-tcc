import csv
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from tcc_sales.dataset import normalize_product


def read(name):
    with (ROOT / "data/raw/maven" / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def metrics(y, scores, fraction=0.20):
    y = np.asarray(y, dtype=int)
    scores = np.asarray(scores, dtype=float)
    k = max(1, int(np.ceil(len(y) * fraction)))
    selected = y[np.argsort(-scores, kind="stable")[:k]]
    prevalence = float(y.mean())
    return {
        "average_precision": float(average_precision_score(y, scores)),
        "roc_auc": float(roc_auc_score(y, scores)),
        "brier": float(brier_score_loss(y, scores)),
        "top_fraction": fraction,
        "top_count": k,
        "precision_at_top": float(selected.mean()),
        "recall_at_top": float(selected.sum() / y.sum()),
        "lift_at_top": float(selected.mean() / prevalence),
    }


def bootstrap_ap_ci(y, scores, iterations=500):
    y = np.asarray(y, dtype=int)
    scores = np.asarray(scores, dtype=float)
    rng = np.random.default_rng(20260908)
    values = []
    for _ in range(iterations):
        idx = rng.integers(0, len(y), len(y))
        if len(np.unique(y[idx])) == 2:
            values.append(average_precision_score(y[idx], scores[idx]))
    low, high = np.quantile(values, [0.025, 0.975])
    return [float(low), float(high)]


def bootstrap_ap_difference_ci(y, scores, reference, iterations=500):
    y = np.asarray(y, dtype=int)
    scores = np.asarray(scores, dtype=float)
    reference = np.asarray(reference, dtype=float)
    rng = np.random.default_rng(20260908)
    values = []
    for _ in range(iterations):
        idx = rng.integers(0, len(y), len(y))
        if len(np.unique(y[idx])) == 2:
            values.append(average_precision_score(y[idx], scores[idx]) - average_precision_score(y[idx], reference[idx]))
    low, high = np.quantile(values, [0.025, 0.975])
    return [float(low), float(high)]


def main():
    accounts = {r["account"]: r for r in read("accounts.csv")}
    products = {r["product"]: r for r in read("products.csv")}
    agents = {r["sales_agent"]: r for r in read("sales_teams.csv")}
    records = []
    for row in read("sales_pipeline.csv"):
        if row["deal_stage"] not in {"Won", "Lost"}:
            continue
        engaged = date.fromisoformat(row["engage_date"])
        product_name = normalize_product(row["product"])
        account = accounts[row["account"]]
        product = products[product_name]
        agent = agents[row["sales_agent"]]
        x = [
            row["sales_agent"], product_name, row["account"], account["sector"], account["office_location"],
            agent["manager"], agent["regional_office"], float(account["revenue"]), float(account["employees"]),
            float(engaged.year - int(account["year_established"])), float(product["sales_price"]),
            float(engaged.month), float(engaged.weekday()),
        ]
        records.append((engaged, x, int(row["deal_stage"] == "Won"), product_name))
    records.sort(key=lambda item: item[0])
    candidate = records[int(len(records) * 0.80)][0]
    train = [r for r in records if r[0] < candidate]
    test = [r for r in records if r[0] >= candidate]
    X_train, y_train = [r[1] for r in train], np.array([r[2] for r in train])
    X_test, y_test = [r[1] for r in test], np.array([r[2] for r in test])

    category_columns = list(range(7))
    numeric_columns = list(range(7, 13))
    def preprocessing():
        return ColumnTransformer([
            ("categorical", OneHotEncoder(handle_unknown="ignore"), category_columns),
            ("numeric", StandardScaler(), numeric_columns),
        ])

    models = {
        "logistic_regression": Pipeline([
            ("preprocessing", preprocessing()),
            ("classifier", LogisticRegression(max_iter=2000, random_state=20260908)),
        ]),
        "decision_tree": Pipeline([
            ("preprocessing", preprocessing()),
            ("classifier", DecisionTreeClassifier(max_depth=5, min_samples_leaf=50, random_state=20260908)),
        ]),
    }
    scores = {"constant_prevalence": np.full(len(test), y_train.mean())}
    product_totals = defaultdict(lambda: [1, 2])  # suavização de Laplace
    for record in train:
        product_totals[record[3]][0] += record[2]
        product_totals[record[3]][1] += 1
    scores["product_win_rate"] = np.array([product_totals[r[3]][0] / product_totals[r[3]][1] for r in test])
    for name, model in models.items():
        model.fit(X_train, y_train)
        scores[name] = model.predict_proba(X_test)[:, 1]

    evaluation = {}
    for name, values in scores.items():
        evaluation[name] = metrics(y_test, values)
        evaluation[name]["average_precision_bootstrap_95pct"] = bootstrap_ap_ci(y_test, values)
        if name != "constant_prevalence":
            evaluation[name]["average_precision_difference_vs_constant_95pct"] = bootstrap_ap_difference_ci(
                y_test, values, scores["constant_prevalence"]
            )
    result = {
        "experiment": "Retrospective prediction of Won vs Lost at engage_date",
        "random_seed": 20260908,
        "split": {
            "method": "temporal; train engage_date before cutoff, test on/after cutoff",
            "cutoff": candidate.isoformat(),
            "train_rows": len(train),
            "test_rows": len(test),
            "train_win_rate": float(y_train.mean()),
            "test_win_rate": float(y_test.mean()),
        },
        "features": ["sales_agent", "product", "account", "sector", "office_location", "manager", "regional_office", "account_revenue_musd", "employees", "company_age", "sales_price", "engage_month", "engage_weekday"],
        "excluded_as_post_outcome_or_identifier": ["opportunity_id", "deal_stage", "close_date", "close_value"],
        "models": evaluation,
        "limitations": [
            "Fictitious single-company data.",
            "Only resolved Won/Lost cases are evaluated; open recent opportunities are not labeled.",
            "No hyperparameter search was performed; the final test was used once for this comparison.",
            "Scores estimate association with the recorded outcome, not causal benefit of contacting a lead.",
        ],
        "versions": {"python": sys.version.split()[0], "numpy": np.__version__},
    }
    import sklearn
    result["versions"]["scikit_learn"] = sklearn.__version__
    (ROOT / "artifacts").mkdir(exist_ok=True)
    (ROOT / "artifacts/experiment.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
