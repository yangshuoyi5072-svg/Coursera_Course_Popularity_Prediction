"""
Data Analysis Script for Report
Analyzes data sources, quality, and statistics for the report
"""

import json
from pathlib import Path
from collections import Counter
import statistics


def load_enhanced_data():
    """Load enhanced course data"""
    path = Path("data/AllCourses_Enhanced.json")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def analyze_data_sources():
    """Analyze data sources and their volumes"""
    print("=" * 70)
    print("1. DATA SOURCES AND VOLUMES")
    print("=" * 70)
    
    enhanced_data = load_enhanced_data()
    courses = enhanced_data["courses"]
    metadata = enhanced_data["_metadata"]
    
    print(f"\nPrimary Dataset: AllCourses_Enhanced.json")
    print(f"  Total entries: {len(courses):,}")
    print(f"  Created at: {metadata.get('created_at')}")
    print(f"  Source files:")
    for source in metadata.get("source_files", []):
        print(f"    - {source}")
    
    sources_info = {
        "AllCourses_ID_URL_productType.json": "Base index with ID, URL, productType",
        "coursera_all_products_batch.json": "Full product data from GraphQL API",
        "url_to_subject_mapping.json": "Subject categorization from topic filtering"
    }
    
    print(f"\nData Source Details:")
    for source_file, description in sources_info.items():
        path = Path(source_file)
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                if "products" in data:
                    count = len(data["products"])
                elif "courses" in data:
                    count = len(data["courses"])
                elif "mappings" in data:
                    count = len(data["mappings"])
                else:
                    count = "N/A"
            elif isinstance(data, list):
                count = len(data)
            else:
                count = "N/A"
            print(f"  {source_file}:")
            print(f"    Description: {description}")
            print(f"    Records: {count:,}" if isinstance(count, int) else f"    Records: {count}")
        else:
            print(f"  {source_file}: Not found")
    
    return courses


def analyze_data_dimensions(courses):
    """Analyze data dimensionality"""
    print("\n" + "=" * 70)
    print("2. DATA DIMENSIONALITY")
    print("=" * 70)
    
    if not courses:
        return
    
    sample = courses[0]
    fields = list(sample.keys())
    
    print(f"\nNumber of features/attributes: {len(fields)}")
    print(f"\nFeature list:")
    for i, field in enumerate(fields, 1):
        value = sample.get(field)
        value_type = type(value).__name__
        if isinstance(value, list):
            value_type = f"list[{type(value[0]).__name__ if value else 'unknown'}]"
        print(f"  {i:2d}. {field:30s} ({value_type})")
    
    product_types = Counter(course.get("productType") for course in courses)
    print(f"\nProduct types distribution:")
    for ptype, count in product_types.most_common():
        print(f"  {ptype:30s}: {count:6,} ({count/len(courses)*100:.2f}%)")


def analyze_missing_values(courses):
    """Analyze missing values"""
    print("\n" + "=" * 70)
    print("3. MISSING VALUES ANALYSIS")
    print("=" * 70)
    
    if not courses:
        return
    
    fields = list(courses[0].keys())
    missing_stats = {}
    
    for field in fields:
        missing_count = sum(1 for course in courses if course.get(field) is None or course.get(field) == [])
        missing_stats[field] = {
            "missing": missing_count,
            "present": len(courses) - missing_count,
            "percentage": (missing_count / len(courses)) * 100
        }
    
    print(f"\nMissing values by field:")
    print(f"{'Field':<35} {'Missing':>10} {'Present':>10} {'% Missing':>12}")
    print("-" * 70)
    
    for field, stats in sorted(missing_stats.items(), key=lambda x: x[1]["percentage"], reverse=True):
        if stats["missing"] > 0:
            print(f"{field:<35} {stats['missing']:>10,} {stats['present']:>10,} {stats['percentage']:>11.2f}%")
    
    print(f"\nKey fields missing value summary:")
    key_fields = ["subject", "name", "avgProductRating", "partners", "skills"]
    for field in key_fields:
        if field in missing_stats:
            stats = missing_stats[field]
            print(f"  {field:30s}: {stats['missing']:6,} missing ({stats['percentage']:.2f}%)")


def analyze_outliers_and_noise(courses):
    """Analyze outliers and potential noise"""
    print("\n" + "=" * 70)
    print("4. OUTLIERS AND NOISE ANALYSIS")
    print("=" * 70)
    
    if not courses:
        return
    
    ratings = [c.get("avgProductRating") for c in courses if c.get("avgProductRating") is not None]
    if ratings:
        print(f"\nRating statistics:")
        print(f"  Valid ratings: {len(ratings):,}")
        print(f"  Min: {min(ratings):.2f}")
        print(f"  Max: {max(ratings):.2f}")
        print(f"  Mean: {statistics.mean(ratings):.2f}")
        print(f"  Median: {statistics.median(ratings):.2f}")
        if len(ratings) > 1:
            print(f"  Std Dev: {statistics.stdev(ratings):.2f}")
    
    rating_counts = [c.get("numProductRatings", 0) for c in courses]
    if rating_counts:
        print(f"\nNumber of ratings statistics:")
        print(f"  Min: {min(rating_counts):,}")
        print(f"  Max: {max(rating_counts):,}")
        print(f"  Mean: {statistics.mean(rating_counts):.1f}")
        print(f"  Median: {statistics.median(rating_counts):.1f}")
        
        q3 = statistics.quantiles(rating_counts, n=4)[2]
        outliers = [c for c in rating_counts if c > q3 * 3]
        if outliers:
            print(f"  Potential outliers (>3x Q3): {len(outliers)} courses")
    
    skills_counts = [len(c.get("skills", [])) for c in courses]
    if skills_counts:
        print(f"\nSkills per course statistics:")
        print(f"  Min: {min(skills_counts)}")
        print(f"  Max: {max(skills_counts)}")
        print(f"  Mean: {statistics.mean(skills_counts):.1f}")
        print(f"  Median: {statistics.median(skills_counts):.1f}")
    
    url_issues = []
    for course in courses:
        url = course.get("url", "")
        if not url.startswith("https://www.coursera.org"):
            url_issues.append(url)
    
    if url_issues:
        print(f"\nURL format issues: {len(url_issues)} URLs don't match expected format")
    else:
        print(f"\nURL format: All URLs are properly formatted")


def analyze_data_merging():
    """Explain how data sources were merged"""
    print("\n" + "=" * 70)
    print("5. DATA MERGING PROCESS")
    print("=" * 70)
    
    print("""
Data merging was performed in multiple stages:

1. Base Index Creation (build_course_index.py):
   - Source: coursera_all_products_batch.json
   - Process: Deduplicated by URL, sorted, assigned integer IDs
   - Output: AllCourses_ID_URL_productType.json
   - Result: 18,387 unique products with ID, URL, productType

2. Subject Mapping (scrape_subjects.py):
   - Source: GraphQL API with topic filters
   - Process: Scraped products filtered by 11 subject categories
   - Output: url_to_subject_mapping.json
   - Result: 18,478 URL-to-subject mappings

3. Enhanced Index Creation (enhance_course_index.py):
   - Sources: 
     * AllCourses_ID_URL_productType.json (base index)
     * coursera_all_products_batch.json (full product data)
     * url_to_subject_mapping.json (subject mappings)
   - Process:
     a. Load base index (ID, URL, productType)
     b. Match URLs with full product data to add features
     c. Match URLs with subject mappings to add subject
   - Merging strategy: URL-based matching
   - Output: AllCourses_Enhanced.json
   - Result: 18,387 products with all features
""")


def analyze_biases():
    """Identify potential biases in the data"""
    print("\n" + "=" * 70)
    print("6. POTENTIAL BIASES IN THE DATA")
    print("=" * 70)
    
    courses = load_enhanced_data()["courses"]
    
    english_only = sum(1 for c in courses if "English" in c.get("fullyTranslatedLanguages", []))
    print(f"\nLanguage bias:")
    print(f"  Courses with English translation: {english_only:,} ({english_only/len(courses)*100:.2f}%)")
    
    subjects = Counter(c.get("subject") for c in courses if c.get("subject"))
    print(f"\nSubject distribution bias:")
    print(f"  Most represented: {subjects.most_common(1)[0] if subjects else 'N/A'}")
    print(f"  Least represented: {subjects.most_common()[-1] if subjects else 'N/A'}")
    
    high_rated = sum(1 for c in courses if c.get("numProductRatings", 0) > 1000)
    low_rated = sum(1 for c in courses if c.get("numProductRatings", 0) < 10)
    print(f"\nRating bias:")
    print(f"  Courses with >1000 ratings: {high_rated:,} ({high_rated/len(courses)*100:.2f}%)")
    print(f"  Courses with <10 ratings: {low_rated:,} ({low_rated/len(courses)*100:.2f}%)")
    
    free_courses = sum(1 for c in courses if c.get("isCourseFree") == True)
    print(f"\nPricing bias:")
    print(f"  Free courses: {free_courses:,} ({free_courses/len(courses)*100:.2f}%)")
    print(f"  Paid courses: {len(courses)-free_courses:,} ({(len(courses)-free_courses)/len(courses)*100:.2f}%)")
    
    print(f"\nPotential biases identified:")
    print(f"  1. Language: Heavy English language focus")
    print(f"  2. Subject: Uneven distribution across subjects")
    print(f"  3. Popularity: Some courses have significantly more ratings")
    print(f"  4. Pricing: Mix of free and paid courses may affect accessibility")


def generate_summary_report():
    """Generate summary report"""
    print("\n" + "=" * 70)
    print("SUMMARY REPORT")
    print("=" * 70)
    
    courses = load_enhanced_data()["courses"]
    
    print(f"""
Data Volume:
  - Total products: {len(courses):,}
  - Features per product: {len(courses[0].keys()) if courses else 0}
  - Data sources: 3 (base index, full product data, subject mapping)

Data Quality:
  - Missing subject: {sum(1 for c in courses if c.get('subject') is None):,} ({sum(1 for c in courses if c.get('subject') is None)/len(courses)*100:.2f}%)
  - Missing name: {sum(1 for c in courses if c.get('name') is None):,}
  - Missing ratings: {sum(1 for c in courses if c.get('avgProductRating') is None):,}

Data Completeness: Excellent (99.91% subject coverage)
""")


def main():
    """Main analysis function"""
    print("\n" + "=" * 70)
    print("DATA ANALYSIS FOR REPORT")
    print("=" * 70)
    
    courses = analyze_data_sources()
    analyze_data_dimensions(courses)
    analyze_missing_values(courses)
    analyze_outliers_and_noise(courses)
    analyze_data_merging()
    analyze_biases()
    generate_summary_report()
    
    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

