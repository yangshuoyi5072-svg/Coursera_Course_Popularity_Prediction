"""
Add numeric and one-hot encoded duration features based on productDuration.

Input:
- AllCourses_Enhanced_with_difficulty.json

Output:
- AllCourses_Enhanced_with_duration.json

For each course:
- duration_level_num: float
    UNKNOWN             -> 0.0
    LESS_THAN_TWO_HOURS -> 0.5
    ONE_TO_FOUR_WEEKS   -> 1.0
    ONE_TO_THREE_MONTHS -> 2.0
    THREE_TO_SIX_MONTHS -> 3.0
    ONE_TO_FOUR_YEARS   -> 4.0

- duration_LESS_THAN_TWO_HOURS
  duration_ONE_TO_FOUR_WEEKS
  duration_ONE_TO_THREE_MONTHS
  duration_THREE_TO_SIX_MONTHS
  duration_ONE_TO_FOUR_YEARS
  duration_UNKNOWN
  (all are 0/1 one-hot flags)
"""

import json
from pathlib import Path
from typing import Dict, List

INPUT_FILE = Path("AllCourses_Enhanced_with_difficulty.json")
OUTPUT_FILE = Path("AllCourses_Enhanced_with_duration.json")


DURATION_NUM_MAP = {
    "LESS_THAN_TWO_HOURS": 0.5,
    "ONE_TO_FOUR_WEEKS": 1.0,
    "ONE_TO_THREE_MONTHS": 2.0,
    "THREE_TO_SIX_MONTHS": 3.0,
    "ONE_TO_FOUR_YEARS": 4.0,
    "UNKNOWN": 0.0,
}

DURATION_LEVELS = [
    "LESS_THAN_TWO_HOURS",
    "ONE_TO_FOUR_WEEKS",
    "ONE_TO_THREE_MONTHS",
    "THREE_TO_SIX_MONTHS",
    "ONE_TO_FOUR_YEARS",
    "UNKNOWN",
]


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


def add_duration_features(data: Dict) -> Dict:
    courses: List[Dict] = data["courses"]

    for course in courses:
        raw = course.get("productDuration")
        level = raw if raw is not None else "UNKNOWN"
        level = str(level)
        if level not in DURATION_LEVELS:
            level = "UNKNOWN"

        # numeric mapping
        course["duration_level_num"] = DURATION_NUM_MAP.get(level, 0.0)

        # one-hot flags
        for lv in DURATION_LEVELS:
            col = f"duration_{lv}"
            course[col] = int(level == lv)

    # update metadata
    metadata = data.get("_metadata", {})
    fields = metadata.get("fields", [])
    new_fields = [
        "duration_level_num - Ordered numeric encoding of productDuration "
        "(UNKNOWN=0.0, LESS_THAN_TWO_HOURS=0.5, ONE_TO_FOUR_WEEKS=1.0, "
        "ONE_TO_THREE_MONTHS=2.0, THREE_TO_SIX_MONTHS=3.0, ONE_TO_FOUR_YEARS=4.0)",
    ]
    for lv in DURATION_LEVELS:
        new_fields.append(
            f"duration_{lv} - One-hot indicator for productDuration == '{lv}'"
        )

    for desc in new_fields:
        if desc not in fields:
            fields.append(desc)

    metadata["fields"] = fields
    data["_metadata"] = metadata
    return data


def main():
    data = load_data()
    data_with_duration = add_duration_features(data)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(data_with_duration, f, ensure_ascii=False, indent=2)

    print(
        f"Saved {len(data_with_duration.get('courses', []))} courses with duration features to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()



