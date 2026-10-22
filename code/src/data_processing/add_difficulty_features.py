"""
Add numeric and one-hot encoded difficulty features based on productDifficultyLevel.

Input:
- AllCourses_Enhanced_with_subject_onehot.json

Output:
- AllCourses_Enhanced_with_difficulty.json

For each course:
- difficulty_level_num: float
    UNKNOWN (None)      -> 0.0
    BEGINNER            -> 1.0
    INTERMEDIATE        -> 2.0
    MIXED               -> 2.0   (treated as mid-level)
    ADVANCED            -> 3.0

- difficulty_BEGINNER, difficulty_INTERMEDIATE, difficulty_ADVANCED,
  difficulty_MIXED, difficulty_UNKNOWN: one-hot 0/1 flags.
"""

import json
from pathlib import Path
from typing import Dict, List

INPUT_FILE = Path("AllCourses_Enhanced_with_subject_onehot.json")
OUTPUT_FILE = Path("AllCourses_Enhanced_with_difficulty.json")


DIFFICULTY_NUM_MAP = {
    "BEGINNER": 1.0,
    "INTERMEDIATE": 2.0,
    "MIXED": 2.0,
    "ADVANCED": 3.0,
    "UNKNOWN": 0.0,
}

DIFFICULTY_LEVELS = ["BEGINNER", "INTERMEDIATE", "MIXED", "ADVANCED", "UNKNOWN"]


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


def add_difficulty_features(data: Dict) -> Dict:
    courses: List[Dict] = data["courses"]

    for course in courses:
        raw = course.get("productDifficultyLevel")
        level = raw if raw is not None else "UNKNOWN"
        level = str(level)
        if level not in DIFFICULTY_LEVELS:
            level = "UNKNOWN"

        # numeric mapping
        course["difficulty_level_num"] = DIFFICULTY_NUM_MAP.get(level, 0.0)

        # one-hot flags
        for lv in DIFFICULTY_LEVELS:
            col = f"difficulty_{lv}"
            course[col] = int(level == lv)

    # update metadata
    metadata = data.get("_metadata", {})
    fields = metadata.get("fields", [])
    new_fields = [
        "difficulty_level_num - Ordered numeric encoding of productDifficultyLevel "
        "(UNKNOWN=0, BEGINNER=1, INTERMEDIATE=2, MIXED=2, ADVANCED=3)",
    ]
    for lv in DIFFICULTY_LEVELS:
        new_fields.append(
            f"difficulty_{lv} - One-hot indicator for productDifficultyLevel == '{lv}'"
        )

    for desc in new_fields:
        if desc not in fields:
            fields.append(desc)

    metadata["fields"] = fields
    data["_metadata"] = metadata
    return data


def main():
    data = load_data()
    data_with_diff = add_difficulty_features(data)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(data_with_diff, f, ensure_ascii=False, indent=2)

    print(
        f"Saved {len(data_with_diff.get('courses', []))} courses with difficulty features to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()


