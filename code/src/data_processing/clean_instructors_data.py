import json
import numpy as np
import os

def clean_data(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict wrapper
    courses = data.get('courses', data) if isinstance(data, dict) else data
    
    # First pass: collect values for imputation
    all_courses_counts = []
    
    for course in courses:
        if 'instructors' in course:
            for inst in course['instructors']:
                cc = inst.get('courses_count')
                if cc:
                    try:
                        # Handle cases where it might already be int
                        val = int(str(cc).replace(',', ''))
                        all_courses_counts.append(val)
                    except:
                        pass

    avg_courses_count = int(np.mean(all_courses_counts)) if all_courses_counts else 0
    print(f"Imputing missing courses_count with mean: {avg_courses_count}")

    # Second pass: clean and update
    for course in courses:
        # 1. Instructor Rating
        if 'instructor_rating' in course and course['instructor_rating']:
            try:
                course['instructor_rating'] = float(course['instructor_rating'])
            except:
                pass # Keep original or None? User implies conversion, so maybe leave as is if fail
        
        # 2. Instructor Rating Count
        if 'instructor_rating_count' in course and course['instructor_rating_count']:
            try:
                course['instructor_rating_count'] = int(str(course['instructor_rating_count']).replace(',', ''))
            except:
                pass

        # 3. Positive Review Rate
        if 'positive_review_rate' in course and course['positive_review_rate']:
            try:
                val = str(course['positive_review_rate']).replace('%', '')
                course['positive_review_rate'] = float(val) / 100.0
            except:
                pass

        # 4. Booleans
        for field in ['is_specialization', 'is_professional_certificate', 'is_flexible_schedule']:
            if field in course:
                # Convert to 1/0
                course[field] = 1 if course[field] else 0
        
        # 5. Instructors
        if 'instructors' in course:
            for inst in course['instructors']:
                # Learners count
                if 'learners_count' in inst and inst['learners_count']:
                    try:
                        inst['learners_count'] = int(str(inst['learners_count']).replace(',', ''))
                    except:
                        pass
                
                # Courses count (Imputation)
                if not inst.get('courses_count'):
                    inst['courses_count'] = avg_courses_count
                else:
                    try:
                        inst['courses_count'] = int(str(inst['courses_count']).replace(',', ''))
                    except:
                        inst['courses_count'] = avg_courses_count
                
                # is_top_instructor (Ensure boolean or 1/0? User didn't specify, but let's keep consistent if needed. 
                # User only specified the 3 fields above for boolean conversion. I'll leave this one alone unless asked.)

    # Save
    # Preserve original structure if it was a dict
    output_data = {'courses': courses} if isinstance(data, dict) and 'courses' in data else courses
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"Saved cleaned data to {output_file}")

if __name__ == "__main__":
    clean_data('Courses_instructors.json', 'Courses_instructors_cleaned.json')
