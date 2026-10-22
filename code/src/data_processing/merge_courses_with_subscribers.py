"""
Merge subscriber metrics into the enhanced course index.

Inputs:
- AllCourses_Enhanced.json: enriched course metadata
- suscribers_and_series.json: subscriber + series counts per URL

Output:
- AllCourses_Enhanced_with_subscribers.json
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple


ALL_COURSES_FILE = Path("AllCourses_Enhanced.json")
SUBSCRIBERS_FILE = Path("suscribers_and_series.json")
OUTPUT_FILE = Path("AllCourses_Enhanced_with_subscribers.json")


def normalize_url(url: str) -> str:
    """Normalize URLs so lookups succeed."""
    if not url:
        return ""
    cleaned = url.strip()
    # Remove trailing slashes to avoid mismatches
    while cleaned.endswith("/"):
        cleaned = cleaned[:-1]
    return cleaned


def load_all_courses() -> Tuple[Dict[str, Dict], Dict]:
    """Load enhanced courses and build URL map."""
    if not ALL_COURSES_FILE.exists():
        raise FileNotFoundError(f"{ALL_COURSES_FILE} not found")

    with ALL_COURSES_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    courses = data.get("courses", [])
    url_map: Dict[str, Dict] = {}
    for course in courses:
        url = normalize_url(course.get("url", ""))
        if url:
            url_map[url] = course

    return url_map, data


def load_subscribers() -> List[Dict]:
    """Load subscriber dataset."""
    if not SUBSCRIBERS_FILE.exists():
        raise FileNotFoundError(f"{SUBSCRIBERS_FILE} not found")

    with SUBSCRIBERS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("suscribers_and_series.json should contain a list")

    return data


def merge_datasets() -> Dict:
    """Merge subscriber information into the enhanced courses."""
    url_map, all_courses_data = load_all_courses()
    subscribers = load_subscribers()

    matched = 0
    unmatched_records: List[Dict] = []

    for entry in subscribers:
        url = normalize_url(entry.get("url", ""))
        if not url:
            unmatched_records.append(entry)
            continue

        course = url_map.get(url)
        if course:
            course["suscribers"] = entry.get("suscribers")
            course["nb_series"] = entry.get("nb_series")
            matched += 1
        else:
            unmatched_records.append(entry)

    metadata = all_courses_data.get("_metadata", {}).copy()
    metadata["merged_with_subscribers_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    metadata["source_files"] = sorted(
        set(metadata.get("source_files", []))
        | {"AllCourses_Enhanced.json", "suscribers_and_series.json"}
    )
    metadata["subscriber_records_total"] = len(subscribers)
    metadata["subscriber_records_matched"] = matched
    metadata["subscriber_records_unmatched"] = len(unmatched_records)
    new_fields = [
        "suscribers - Subscriber count string from suscribers_and_series.json",
        "nb_series - Series count string from suscribers_and_series.json",
    ]
    fields = metadata.setdefault("fields", [])
    for field in new_fields:
        if field not in fields:
            fields.append(field)

    return {
        "_metadata": metadata,
        "courses": list(url_map.values()),
        "unmatched_subscriber_records": unmatched_records,
    }


def save_output(data: Dict) -> None:
    """Persist merged JSON."""
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(
        f"Saved merged dataset with {len(data.get('courses', []))} courses "
        f"to {OUTPUT_FILE}"
    )


def main():
    merged = merge_datasets()
    save_output(merged)


if __name__ == "__main__":
    main()

