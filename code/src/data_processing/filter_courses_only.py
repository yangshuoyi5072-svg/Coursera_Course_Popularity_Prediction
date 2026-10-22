"""
Filter COURSE-only dataset from the complete dataset.

This script creates a filtered dataset containing only productType='COURSE' records,
which will be used for all subsequent analysis and modeling.

Input: AllCourses_Enhanced_with_popularity.json (18,387 records)
Output: Courses_Only_Dataset.json (14,006 COURSE records)
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime


def load_complete_dataset():
    """Load the complete dataset with all product types."""
    input_file = Path("AllCourses_Enhanced_with_popularity.json")
    
    if not input_file.exists():
        raise FileNotFoundError(
            f"{input_file} not found. Please ensure the file exists."
        )
    
    print(f"Loading data from {input_file}...")
    with input_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data


def filter_courses(data):
    """Filter only COURSE productType records."""
    print("\nFiltering COURSE records...")
    
    # Convert to DataFrame for easier filtering
    df = pd.DataFrame(data["courses"])
    
    # Original stats
    total_records = len(df)
    product_type_counts = df["productType"].value_counts()
    
    print(f"\nOriginal dataset:")
    print(f"  Total records: {total_records:,}")
    print(f"\n  Product type distribution:")
    for ptype, count in product_type_counts.items():
        print(f"    {ptype:30s}: {count:6,} ({count/total_records*100:5.2f}%)")
    
    # Filter COURSE only
    courses_df = df[df["productType"] == "COURSE"].copy()
    courses_df.reset_index(drop=True, inplace=True)
    
    # Filtered stats
    course_count = len(courses_df)
    print(f"\nFiltered dataset:")
    print(f"  COURSE records: {course_count:,}")
    print(f"  Percentage of total: {course_count/total_records*100:.2f}%")
    print(f"  Removed records: {total_records - course_count:,}")
    
    return courses_df, total_records


def analyze_filtered_data(courses_df):
    """Analyze the filtered COURSE dataset."""
    print("\n" + "="*70)
    print("FILTERED DATASET ANALYSIS")
    print("="*70)
    
    # Missing values analysis
    print("\nMissing values in key fields:")
    key_fields = ["suscribers", "avgProductRating", "numProductRatings", 
                  "productDifficultyLevel", "subject"]
    
    for field in key_fields:
        if field in courses_df.columns:
            missing_count = courses_df[field].isnull().sum()
            missing_pct = (missing_count / len(courses_df)) * 100
            print(f"  {field:25s}: {missing_count:6,} ({missing_pct:5.2f}%)")
    
    # Subject distribution
    print("\nSubject distribution (Top 10):")
    subject_counts = courses_df["subject"].value_counts().head(10)
    for subject, count in subject_counts.items():
        print(f"  {subject:40s}: {count:5,} ({count/len(courses_df)*100:5.2f}%)")
    
    # Difficulty distribution
    print("\nDifficulty distribution:")
    if "productDifficultyLevel" in courses_df.columns:
        diff_counts = courses_df["productDifficultyLevel"].value_counts()
        for diff, count in diff_counts.items():
            print(f"  {str(diff):25s}: {count:6,} ({count/len(courses_df)*100:5.2f}%)")
    
    # Duration distribution
    print("\nDuration distribution:")
    if "productDuration" in courses_df.columns:
        dur_counts = courses_df["productDuration"].value_counts()
        for dur, count in dur_counts.items():
            print(f"  {str(dur):25s}: {count:6,} ({count/len(courses_df)*100:5.2f}%)")
    
    # Free vs Paid
    print("\nPricing distribution:")
    if "isCourseFree" in courses_df.columns:
        free_count = courses_df["isCourseFree"].sum()
        paid_count = len(courses_df) - free_count
        print(f"  Free courses: {free_count:6,} ({free_count/len(courses_df)*100:5.2f}%)")
        print(f"  Paid courses: {paid_count:6,} ({paid_count/len(courses_df)*100:5.2f}%)")


def save_filtered_dataset(courses_df, original_total):
    """Save the filtered dataset to JSON."""
    output_file = Path("Courses_Only_Dataset.json")
    
    # Create metadata
    metadata = {
        "description": "Filtered dataset containing only COURSE productType",
        "total_records": len(courses_df),
        "filtered_from": "AllCourses_Enhanced_with_popularity.json",
        "filter_criteria": "productType == 'COURSE'",
        "original_total_records": original_total,
        "percentage_of_original": f"{len(courses_df)/original_total*100:.2f}%",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fields_count": len(courses_df.columns),
        "key_statistics": {
            "missing_subscribers": int(courses_df["suscribers"].isnull().sum()),
            "missing_avgProductRating": int(courses_df["avgProductRating"].isnull().sum()),
            "subjects_count": int(courses_df["subject"].nunique()),
            "free_courses": int(courses_df["isCourseFree"].sum()),
            "paid_courses": int((~courses_df["isCourseFree"]).sum())
        }
    }
    
    # Prepare output data
    output_data = {
        "_metadata": metadata,
        "courses": courses_df.to_dict("records")
    }
    
    # Save to JSON
    print(f"\nSaving filtered dataset to {output_file}...")
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Successfully saved {len(courses_df):,} COURSE records")
    print(f"✓ Output file: {output_file}")
    print(f"✓ File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")


def main():
    """Main execution function."""
    print("="*70)
    print("COURSE DATA FILTERING SCRIPT")
    print("="*70)
    
    # Load complete dataset
    data = load_complete_dataset()
    
    # Filter COURSE records
    courses_df, original_total = filter_courses(data)
    
    # Analyze filtered data
    analyze_filtered_data(courses_df)
    
    # Save filtered dataset
    save_filtered_dataset(courses_df, original_total)
    
    print("\n" + "="*70)
    print("FILTERING COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Review Courses_Only_Dataset.json")
    print("  2. Run EDA notebook: notebooks/01_EDA_Courses.ipynb")
    print("  3. Continue with feature engineering")


if __name__ == "__main__":
    main()
