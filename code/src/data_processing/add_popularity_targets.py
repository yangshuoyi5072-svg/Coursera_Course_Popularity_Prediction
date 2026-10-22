"""
Add popularity-related numeric features and target scores.

Input:
- AllCourses_Enhanced_with_duration.json

Output:
- AllCourses_Enhanced_with_popularity.json

Computed fields per course:
- subscribers_raw: integer subscriber count (cleaned from 'suscribers')
- subscribers_log: log1p(subscribers_raw) when available, else 0.0
- has_subscribers: 1 if subscribers_raw > 0, else 0

- ratings_log: log1p(numProductRatings)
- has_ratings: 1 if numProductRatings > 0, else 0

- adjusted_rating: Bayesian-smoothed rating
    adjusted_rating = (v / (v + m)) * R + (m / (v + m)) * C
    where:
      v = numProductRatings
      R = avgProductRating
      C = global mean rating across courses with avgProductRating not null
      m = 50 (smoothing strength)

- popularity_score (for rows with has_subscribers == 1, otherwise 0.0):
    0.5 * subscribers_log + 0.3 * ratings_log + 0.2 * adjusted_rating

- popularity_score_global (defined for all rows):
    0.7 * ratings_log + 0.3 * adjusted_rating
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

INPUT_FILE = Path("AllCourses_Enhanced_with_duration.json")
OUTPUT_FILE = Path("AllCourses_Enhanced_with_popularity.json")

M_SMOOTH = 50.0


def load_data() -> Dict:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"{INPUT_FILE} not found. Run previous feature scripts first."
        )

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "courses" not in data or not isinstance(data["courses"], list):
        raise ValueError("Input JSON must contain a 'courses' list.")

    return data


def clean_subscribers(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    s = str(value).strip().replace(",", "")
    if not s:
        return None
    try:
        v = int(s)
        return v if v > 0 else None
    except ValueError:
        return None


def compute_global_mean_rating(courses: List[Dict]) -> float:
    total = 0.0
    count = 0
    for c in courses:
        v = c.get("numProductRatings")
        r = c.get("avgProductRating")
        if isinstance(v, (int, float)) and v and isinstance(r, (int, float)):
            total += float(r)
            count += 1
    if count == 0:
        return 0.0
    return total / count


def add_popularity_features(data: Dict) -> Tuple[Dict, float]:
    courses: List[Dict] = data["courses"]
    global_mean = compute_global_mean_rating(courses)

    for course in courses:
        # isCourseFree numeric flag
        is_free = bool(course.get("isCourseFree"))
        course["isCourseFree_int"] = 1 if is_free else 0

        # Subscribers
        subs_raw = clean_subscribers(course.get("suscribers"))
        has_subs = 1 if subs_raw is not None else 0
        subs_log = math.log1p(subs_raw) if subs_raw is not None else 0.0

        course["subscribers_raw"] = subs_raw if subs_raw is not None else 0
        course["has_subscribers"] = has_subs
        course["subscribers_log"] = subs_log

        # Ratings
        num_ratings = course.get("numProductRatings")
        if isinstance(num_ratings, (int, float)) and num_ratings >= 0:
            v = float(num_ratings)
        else:
            v = 0.0
        has_ratings = 1 if v > 0 else 0
        ratings_log = math.log1p(v)

        course["has_ratings"] = has_ratings
        course["ratings_log"] = ratings_log

        # Adjusted rating
        raw_rating = course.get("avgProductRating")
        if isinstance(raw_rating, (int, float)) and has_ratings:
            R = float(raw_rating)
            adjusted = (v / (v + M_SMOOTH)) * R + (M_SMOOTH / (v + M_SMOOTH)) * global_mean
        else:
            # No ratings: fall back to global mean
            adjusted = global_mean

        course["adjusted_rating"] = float(adjusted)

        # Popularity scores
        if has_subs:
            popularity = (
                0.5 * subs_log + 0.3 * ratings_log + 0.2 * float(adjusted)
            )
        else:
            popularity = 0.0

        popularity_global = 0.7 * ratings_log + 0.3 * float(adjusted)

        course["popularity_score"] = float(popularity)
        course["popularity_score_global"] = float(popularity_global)

    return data, global_mean


def update_metadata(data: Dict, global_mean: float) -> Dict:
    metadata = data.get("_metadata", {})
    fields = metadata.get("fields", [])

    new_fields = [
        "isCourseFree_int - Numeric encoding of isCourseFree "
        "(1 for True, 0 for False or missing)",
        "subscribers_raw - Integer subscriber count cleaned from 'suscribers' "
        "(0 when missing or non-positive)",
        "has_subscribers - 1 if subscribers_raw > 0, else 0",
        "subscribers_log - log1p(subscribers_raw) when available, else 0.0",
        "has_ratings - 1 if numProductRatings > 0, else 0",
        "ratings_log - log1p(numProductRatings)",
        "adjusted_rating - Bayesian-smoothed rating using global mean and m=50",
        "popularity_score - Popularity score for rows with subscribers "
        "(0.5 * subscribers_log + 0.3 * ratings_log + 0.2 * adjusted_rating; "
        "0.0 when has_subscribers=0)",
        "popularity_score_global - Global popularity score for all rows "
        "(0.7 * ratings_log + 0.3 * adjusted_rating)",
    ]

    for desc in new_fields:
        if desc not in fields:
            fields.append(desc)

    metadata["fields"] = fields
    metadata["popularity_global_mean_rating_C"] = global_mean
    metadata["popularity_smoothing_m"] = M_SMOOTH
    data["_metadata"] = metadata
    return data


def main():
    data = load_data()
    data_with_pop, global_mean = add_popularity_features(data)
    data_with_pop = update_metadata(data_with_pop, global_mean)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(data_with_pop, f, ensure_ascii=False, indent=2)

    print(
        f"Saved {len(data_with_pop.get('courses', []))} courses with popularity features "
        f"to {OUTPUT_FILE} (global_mean_rating={global_mean:.4f})"
    )


if __name__ == "__main__":
    main()


