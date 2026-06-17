from collections import Counter
from itertools import combinations

from app.ml.data import load_records


def generate_association_rules(min_support: float = 0.02, min_confidence: float = 0.4, limit: int = 50) -> dict[str, object]:
    transactions = [set(r["tags"]) for r in load_records() if len(r["tags"]) >= 2]
    total = len(transactions)
    if total == 0:
        return {"rules": [], "transaction_count": 0}

    item_counts: Counter[frozenset[str]] = Counter()
    pair_counts: Counter[frozenset[str]] = Counter()
    for tags in transactions:
        for tag in tags:
            item_counts[frozenset([tag])] += 1
        for pair in combinations(sorted(tags), 2):
            pair_counts[frozenset(pair)] += 1

    rules = []
    for pair, pair_count in pair_counts.items():
        support = pair_count / total
        if support < min_support:
            continue
        left, right = tuple(pair)
        for antecedent, consequent in [(left, right), (right, left)]:
            antecedent_count = item_counts[frozenset([antecedent])]
            consequent_count = item_counts[frozenset([consequent])]
            confidence = pair_count / antecedent_count if antecedent_count else 0
            if confidence < min_confidence:
                continue
            consequent_support = consequent_count / total if total else 0
            lift = confidence / consequent_support if consequent_support else 0
            rules.append({
                "antecedent": [antecedent],
                "consequent": [consequent],
                "support": round(support, 4),
                "confidence": round(confidence, 4),
                "lift": round(lift, 4),
                "count": pair_count,
            })

    rules.sort(key=lambda r: (r["confidence"], r["lift"], r["support"]), reverse=True)
    return {"rules": rules[:limit], "transaction_count": total}
