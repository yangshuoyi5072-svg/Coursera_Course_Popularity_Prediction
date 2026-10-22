"""
Add one-hot encoded productType features to AllCourses_Enhanced_with_subscribers.json.

Input:
- AllCourses_Enhanced_with_subscribers.json

Output:
- AllCourses_Enhanced_with_productType_onehot.json
  Same structure as input, but each course entry is extended with:
    - productType_COURSE
    - productType_SPECIALIZATION
    - productType_GUIDED_PROJECT
    - productType_PROJECT
    - productType_DEGREE
    - productType_PROFESSIONAL_CERTIFICATE
    - productType_UNKNOWN  (for missing/unexpected values)
"""

import json
from pathlib import Path
from typing import Dict, List, Set

INPUT_FILE = Path("AllCourses_Enhanced_with_subscribers.json")
OUTPUT_FILE = Path("AllCourses_Enhanced_with_productType_onehot.json")


def load_courses() -> Dict:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"{INPUT_FILE} not found. Run merge script first.")

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "courses" not in data or not isinstance(data["courses"], list):
        raise ValueError("Input JSON must contain a 'courses' list.")

    return data


def collect_product_types(courses: List[Dict]) -> Set[str]:
    types: Set[str] = set()
    for course in courses:
        pt = course.get("productType")
        if pt is None or pt == "":
            types.add("UNKNOWN")
        else:
            types.add(str(pt))
    return types


def add_one_hot_features(data: Dict) -> Dict:
    courses = data["courses"]

    # Collect all product types present in the data
    product_types = collect_product_types(courses)

    # Ensure UNKNOWN exists as a catch-all
    product_types.add("UNKNOWN")

    # Create stable ordering for reproducibility
    sorted_types = sorted(product_types)

    # Add metadata description
    metadata = data.get("_metadata", {})
    fields = metadata.get("fields", [])
    for pt in sorted_types:
        col_name = f"productType_{pt}"
        desc = f"{col_name} - One-hot indicator for productType == '{pt}'"
        if desc not in fields:
            fields.append(desc)
    metadata["fields"] = fields
    data["_metadata"] = metadata

    # Add one-hot columns to each course
    for course in courses:
        raw_type = course.get("productType")
        pt_value = raw_type if raw_type not in (None, "") else "UNKNOWN"
        pt_value = str(pt_value)

        for pt in sorted_types:
            col_name = f"productType_{pt}"
            course[col_name] = int(pt_value == pt)

    return data


def main():
    data = load_courses()
    data_with_one_hot = add_one_hot_features(data)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(data_with_one_hot, f, ensure_ascii=False, indent=2)

    total = len(data_with_one_hot.get("courses", []))
    print(
        f"Saved {total} courses with productType one-hot features to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()


