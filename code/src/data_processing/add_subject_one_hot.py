"""
Add one-hot encoded subject features to AllCourses_Enhanced_with_productType_onehot.json.

Input:
- AllCourses_Enhanced_with_productType_onehot.json

Output:
- AllCourses_Enhanced_with_subject_onehot.json
  Same structure as input, but each course entry is extended with:
    - subject_<normalized_subject_name> = 0/1

Notes:
- Normalization: spaces and non-alphanumeric characters are replaced with underscores,
  and the name is uppercased. Example:
    'Data Science' -> 'DATA_SCIENCE' -> column 'subject_DATA_SCIENCE'
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set

INPUT_FILE = Path("AllCourses_Enhanced_with_productType_onehot.json")
OUTPUT_FILE = Path("AllCourses_Enhanced_with_subject_onehot.json")


def load_courses() -> Dict:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"{INPUT_FILE} not found. Run one-hot script for productType first.")

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "courses" not in data or not isinstance(data["courses"], list):
        raise ValueError("Input JSON must contain a 'courses' list.")

    return data


def normalize_subject_name(name: str) -> str:
    """Normalize subject into an uppercase identifier for column naming."""
    if not name:
        return "UNKNOWN"
    # Uppercase, strip, replace non-alphanumeric with underscore
    upper = name.strip().upper()
    normalized = re.sub(r"[^A-Z0-9]+", "_", upper).strip("_")
    return normalized or "UNKNOWN"


def collect_subjects(courses: List[Dict]) -> Set[str]:
    subjects: Set[str] = set()
    for course in courses:
        subj = course.get("subject")
        norm = normalize_subject_name(subj) if subj is not None else "UNKNOWN"
        subjects.add(norm)
    # Ensure UNKNOWN is always present
    subjects.add("UNKNOWN")
    return subjects


def add_one_hot_features(data: Dict) -> Dict:
    courses = data["courses"]

    # Collect all normalized subjects present in the data
    subjects = collect_subjects(courses)

    # Stable ordering
    sorted_subjects = sorted(subjects)

    # Update metadata fields
    metadata = data.get("_metadata", {})
    fields = metadata.get("fields", [])
    for subj in sorted_subjects:
        col_name = f"subject_{subj}"
        desc = f"{col_name} - One-hot indicator for subject == '{subj}'"
        if desc not in fields:
            fields.append(desc)
    metadata["fields"] = fields
    data["_metadata"] = metadata

    # Add one-hot columns to each course
    for course in courses:
        subj_raw = course.get("subject")
        subj_norm = normalize_subject_name(subj_raw) if subj_raw is not None else "UNKNOWN"

        for subj in sorted_subjects:
            col_name = f"subject_{subj}"
            course[col_name] = int(subj_norm == subj)

    return data


def main():
    data = load_courses()
    data_with_one_hot = add_one_hot_features(data)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(data_with_one_hot, f, ensure_ascii=False, indent=2)

    total = len(data_with_one_hot.get("courses", []))
    print(
        f"Saved {total} courses with subject one-hot features to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()


