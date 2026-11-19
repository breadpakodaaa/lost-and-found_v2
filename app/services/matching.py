"""Compare one lost and one found report and explain the resulting score."""

import re
import unicodedata

from rapidfuzz import fuzz


def normalize_text(value):
    """Lowercase text, remove accents and punctuation, and normalize spaces."""
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.casefold()
    value = re.sub(r"[^\w\s]", " ", value)
    return " ".join(value.split())


def text_similarity(left, right):
    """Return a 0–100 fuzzy score; missing text deliberately scores zero."""
    left_text = normalize_text(left)
    right_text = normalize_text(right)
    if not left_text or not right_text:
        return 0.0
    # WRatio handles small spelling differences and reordered words well.
    return float(fuzz.WRatio(left_text, right_text))


def date_similarity(lost_date, found_date, window_days=30):
    """Give closer report dates higher scores, reaching zero outside the window."""
    if lost_date is None or found_date is None or window_days <= 0:
        return 0.0
    distance = abs((lost_date - found_date).days)
    if distance > window_days:
        return 0.0
    return 100.0 * (1 - distance / window_days)


def score_pair(lost_item, found_item, weights, date_window_days=30):
    """Score an opposite-type pair using fixed weights and return score details.

    Missing fields contribute zero while the denominator remains 100, so
    absent information cannot inflate the match score.
    """
    if lost_item.report_type != "lost" or found_item.report_type != "found":
        raise ValueError("score_pair expects a lost report followed by a found report")

    category_lost = normalize_text(lost_item.category)
    category_found = normalize_text(found_item.category)
    components = {
        "name": text_similarity(lost_item.name, found_item.name),
        "description": text_similarity(lost_item.description, found_item.description),
        "category": 100.0 if category_lost and category_lost == category_found else 0.0,
        "colour": text_similarity(lost_item.colour, found_item.colour),
        "location": text_similarity(lost_item.location, found_item.location),
        "date": date_similarity(lost_item.item_date, found_item.item_date, date_window_days),
    }
    total_weight = sum(weights.values())
    if total_weight <= 0:
        raise ValueError("At least one positive matching weight is required")
    score = sum(components[key] * weight for key, weight in weights.items()) / total_weight
    return {"score": round(score, 1), "components": components}


def score_label(score, possible_score=70, strong_score=90):
    """Describe the score for a human reviewer; it is never an identity verdict."""
    if score >= strong_score:
        return "Very strong match"
    if score >= possible_score:
        return "Possible match"
    return "Weak match"
