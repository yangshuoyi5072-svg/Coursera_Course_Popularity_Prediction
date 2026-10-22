import json
import numpy as np
import os

def process_data(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    courses = data.get('courses', data) if isinstance(data, dict) else data
    
    # --- 1. Imputation Preparation ---
    all_courses_counts = []
    for course in courses:
        if 'instructors' in course:
            for inst in course['instructors']:
                cc = inst.get('courses_count')
                if cc:
                    try:
                        val = int(str(cc).replace(',', ''))
                        all_courses_counts.append(val)
                    except:
                        pass
    
    avg_courses_count = int(np.mean(all_courses_counts)) if all_courses_counts else 0
    print(f"Imputing missing courses_count with mean: {avg_courses_count}")

    # --- 2. Processing Loop ---
    for course in courses:
        # A. Data Cleaning
        # Instructor Rating
        if 'instructor_rating' in course and course['instructor_rating']:
            try: course['instructor_rating'] = float(course['instructor_rating'])
            except: pass
        
        # Instructor Rating Count
        if 'instructor_rating_count' in course and course['instructor_rating_count']:
            try: course['instructor_rating_count'] = int(str(course['instructor_rating_count']).replace(',', ''))
            except: pass

        # Positive Review Rate
        if 'positive_review_rate' in course and course['positive_review_rate']:
            try:
                val = str(course['positive_review_rate']).replace('%', '')
                course['positive_review_rate'] = float(val) / 100.0
            except: pass

        # Booleans
        for field in ['is_specialization', 'is_professional_certificate', 'is_flexible_schedule']:
            if field in course:
                course[field] = 1 if course[field] else 0
        
        # Instructors Cleaning
        cleaned_instructors = []
        if 'instructors' in course:
            for inst in course['instructors']:
                # Learners count
                if 'learners_count' in inst and inst['learners_count']:
                    try: inst['learners_count'] = int(str(inst['learners_count']).replace(',', ''))
                    except: pass
                
                # Courses count (Imputation)
                if not inst.get('courses_count'):
                    inst['courses_count'] = avg_courses_count
                else:
                    try: inst['courses_count'] = int(str(inst['courses_count']).replace(',', ''))
                    except: inst['courses_count'] = avg_courses_count
                
                cleaned_instructors.append(inst)
            course['instructors'] = cleaned_instructors

        # B. Feature Engineering
        instructors = course.get('instructors', [])
        
        # 1. num_instructors
        course['num_instructors'] = len(instructors)
        
        # 2. Learners stats
        learners_counts = [i.get('learners_count', 0) for i in instructors if i.get('learners_count') is not None]
        # Treat None as 0 for aggregation? Or skip? Let's treat as 0 for safety or skip if empty.
        # If list is empty, max/avg is 0.
        if learners_counts:
            course['max_instructor_learners'] = max(learners_counts)
            course['avg_instructor_learners'] = float(np.mean(learners_counts))
        else:
            course['max_instructor_learners'] = 0
            course['avg_instructor_learners'] = 0.0
            
        # 3. Courses stats
        courses_counts = [i.get('courses_count', 0) for i in instructors]
        if courses_counts:
            course['max_instructor_courses'] = max(courses_counts)
            course['avg_instructor_courses'] = float(np.mean(courses_counts))
        else:
            course['max_instructor_courses'] = 0
            course['avg_instructor_courses'] = 0.0
            
        # 4. Top Instructor Flag
        # Check if any instructor has is_top_instructor == True
        has_top = any(i.get('is_top_instructor') for i in instructors)
        course['has_top_instructor'] = 1 if has_top else 0

    # Save
    output_data = {'courses': courses} if isinstance(data, dict) and 'courses' in data else courses
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"Saved processed data to {output_file}")

if __name__ == "__main__":
    process_data('Courses_instructors.json', 'Courses_instructors_processed.json')
