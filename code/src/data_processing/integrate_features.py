import json
import math
import numpy as np
import ast
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Set

# ==========================================
# Constants & Lists
# ==========================================

HOT_KEYWORDS = {
    'python', 'data', 'machine learning', 'ai', 'artificial intelligence',
    'deep learning', 'sql', 'business', 'marketing', 'finance',
    'leadership', 'management', 'cloud', 'aws', 'google', 'microsoft',
    'java', 'javascript', 'web', 'mobile', 'blockchain', 'cybersecurity'
}

TOP_UNIVERSITIES = {
    'Massachusetts Institute of Technology', 'Stanford University', 'Harvard University', 
    'California Institute of Technology', 'University of Oxford', 'University of Cambridge', 
    'ETH Zurich', 'Imperial College London', 'University of Chicago', 'UCL', 
    'National University of Singapore', 'Princeton University', 'Nanyang Technological University', 
    'EPFL', 'Tsinghua University', 'University of Pennsylvania', 'Yale University', 
    'Cornell University', 'Columbia University', 'University of Edinburgh', 'University of Michigan', 
    'University of Hong Kong', 'Peking University', 'University of Tokyo', 'Johns Hopkins University', 
    'Duke University', 'University of California, Berkeley', 'University of Manchester', 
    'University of California, Los Angeles', 'New York University', 'University of California, San Diego',
    'University of Toronto', 'McGill University', 'University of Melbourne', 'UNSW Sydney'
}

TOP_COMPANIES = {
    'Google', 'Google Cloud', 'IBM', 'Amazon Web Services', 'Meta', 'Facebook', 
    'Microsoft', 'Apple', 'Intel', 'Cisco', 'Oracle', 'Salesforce', 'SAP', 
    'PwC', 'Goldman Sachs', 'Morgan Stanley', 'DeepLearning.AI'
}

SKILL_DOMAINS = {
    'programming': {'Python', 'Java', 'JavaScript', 'C++', 'R', 'SQL', 'HTML', 'CSS', 'PHP', 'Ruby'},
    'data_science': {'Machine Learning', 'Deep Learning', 'Data Analysis', 'Data Science', 
                     'Artificial Intelligence', 'Big Data', 'Statistics', 'Data Visualization'},
    'cloud': {'Cloud Computing', 'AWS', 'Azure', 'Google Cloud Platform', 'Docker', 'Kubernetes'},
    'business': {'Project Management', 'Leadership', 'Marketing', 'Finance', 'Accounting', 
                 'Strategy', 'Entrepreneurship'},
    'soft_skills': {'Communication', 'Critical Thinking', 'Problem Solving', 'Teamwork'}
}

HOT_SKILLS = {
    'Python', 'Java', 'SQL', 'C++', 'JavaScript', 'R', 'HTML', 'CSS',
    'Machine Learning', 'Deep Learning', 'Artificial Intelligence', 'Data Analysis', 
    'Data Science', 'Big Data', 'Cloud Computing', 'Blockchain',
    'Project Management', 'Leadership', 'Communication', 'Marketing', 'Finance'
}

SUBJECTS = [
    'ARTS_AND_HUMANITIES', 'BUSINESS', 'COMPUTER_SCIENCE', 'DATA_SCIENCE', 
    'HEALTH', 'INFORMATION_TECHNOLOGY', 'LANGUAGE_LEARNING', 'MATH_AND_LOGIC', 
    'PERSONAL_DEVELOPMENT', 'PHYSICAL_SCIENCE_AND_ENGINEERING', 'SOCIAL_SCIENCES'
]

M_SMOOTH = 50.0

# ==========================================
# Helper Functions
# ==========================================

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

def get_difficulty_numeric(level: str) -> float:
    if not level: return 0.0
    level = level.upper()
    if level == 'BEGINNER': return 1.0
    if level == 'INTERMEDIATE': return 2.0
    if level == 'ADVANCED': return 3.0
    if level == 'MIXED': return 2.0
    return 0.0

def get_duration_numeric(duration: str) -> float:
    if not duration: return 0.0
    duration = duration.upper()
    if 'LESS_THAN_TWO_HOURS' in duration: return 0.5
    if 'ONE_TO_FOUR_WEEKS' in duration: return 1.0
    if 'ONE_TO_THREE_MONTHS' in duration: return 2.0
    if 'THREE_TO_SIX_MONTHS' in duration: return 3.0
    if 'ONE_TO_FOUR_YEARS' in duration: return 4.0
    return 0.0

def count_domain_skills(skills: List[str], domain: str) -> int:
    if not skills: return 0
    keywords = SKILL_DOMAINS.get(domain, set())
    count = 0
    for skill in skills:
        if skill in keywords or any(kw.lower() in skill.lower() for kw in keywords):
            count += 1
    return count

# ==========================================
# Main Logic
# ==========================================

def main():
    print("Loading data...")
    try:
        with open('Courses_With_Images.json', 'r', encoding='utf-8') as f:
            base_data = json.load(f)
        
        with open('Courses_instructors_processed.json', 'r', encoding='utf-8') as f:
            instructor_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return

    base_courses = base_data.get('courses', [])
    instructor_courses = instructor_data.get('courses', [])
    
    # Create a map for instructor data by URL
    instructor_map = {c['url']: c for c in instructor_courses if 'url' in c}
    
    # Calculate global mean for popularity score
    global_mean_rating = compute_global_mean_rating(base_courses)
    print(f"Global mean rating: {global_mean_rating:.4f}")

    # Calculate average courses count for imputation
    all_courses_counts = []
    for c in instructor_courses:
        if 'instructors' in c:
            for inst in c['instructors']:
                cc = inst.get('courses_count')
                if cc:
                    try:
                        val = int(str(cc).replace(',', ''))
                        all_courses_counts.append(val)
                    except:
                        pass
    avg_courses_count = int(np.mean(all_courses_counts)) if all_courses_counts else 0
    print(f"Avg instructor courses count (for imputation): {avg_courses_count}")

    integrated_courses = []
    
    print("Processing courses...")
    for course in base_courses:
        url = course.get('url')
        inst_data = instructor_map.get(url, {})
        
        new_course = {
            'id': course.get('id'),
            'url': url,
            'name': course.get('name')
        }
        
        # --- A. Instructor Power ---
        instructors = inst_data.get('instructors', [])
        cleaned_instructors = []
        
        # Clean instructor data locally for calculation
        for inst in instructors:
            # Learners
            l_count = inst.get('learners_count')
            if l_count:
                try: l_count = int(str(l_count).replace(',', ''))
                except: l_count = 0
            else:
                l_count = 0
            
            # Courses
            c_count = inst.get('courses_count')
            if c_count:
                try: c_count = int(str(c_count).replace(',', ''))
                except: c_count = avg_courses_count
            else:
                c_count = avg_courses_count
                
            cleaned_instructors.append({
                'learners_count': l_count,
                'courses_count': c_count,
                'is_top_instructor': inst.get('is_top_instructor', False)
            })
            
        new_course['num_instructors'] = len(cleaned_instructors)
        
        learners_counts = [i['learners_count'] for i in cleaned_instructors]
        courses_counts = [i['courses_count'] for i in cleaned_instructors]
        
        new_course['max_instructor_learners'] = max(learners_counts) if learners_counts else 0
        new_course['avg_instructor_learners'] = float(np.mean(learners_counts)) if learners_counts else 0.0
        new_course['max_instructor_courses'] = max(courses_counts) if courses_counts else 0
        
        new_course['has_top_instructor'] = 1 if any(i.get('is_top_instructor') for i in cleaned_instructors) else 0
        
        # Instructor Rating
        i_rating = inst_data.get('instructor_rating')
        if i_rating:
            try: new_course['instructor_rating'] = float(i_rating)
            except: new_course['instructor_rating'] = None
        else:
             new_course['instructor_rating'] = None

        # --- B. Course Meta ---
        p_type = course.get('productType')
        new_course['is_specialization'] = 1 if p_type == 'SPECIALIZATION' else 0
        new_course['is_professional_certificate'] = 1 if p_type == 'PROFESSIONAL_CERTIFICATE' else 0
        
        # is_flexible_schedule (from instructor data usually, but check base)
        # It seems to be in instructor data based on process_instructors_features.py
        is_flex = inst_data.get('is_flexible_schedule', False)
        new_course['is_flexible_schedule'] = 1 if is_flex else 0
        
        is_free = course.get('isCourseFree', False)
        new_course['isCourseFree_int'] = 1 if is_free else 0
        
        name = str(course.get('name', ''))
        new_course['name_length'] = len(name)
        new_course['name_word_count'] = len(name.split())
        
        name_lower = name.lower()
        hot_kw_count = sum(1 for kw in HOT_KEYWORDS if kw in name_lower)
        new_course['name_hot_keywords'] = hot_kw_count
        new_course['has_hot_keyword_in_name'] = 1 if hot_kw_count > 0 else 0
        
        # --- C. Content ---
        diff_level = course.get('productDifficultyLevel')
        diff_num = get_difficulty_numeric(diff_level)
        new_course['difficulty_level_num'] = diff_num
        
        dur_level = course.get('productDuration')
        dur_num = get_duration_numeric(dur_level)
        new_course['duration_level_num'] = dur_num
        
        # Subjects (One-Hot Encoding)
        # Use 'subject' field directly as domainTypes seems missing/inconsistent
        raw_subject = course.get('subject')
        current_subjects = set()
        
        if raw_subject:
            # Normalize: 'Information Technology' -> 'INFORMATION_TECHNOLOGY'
            norm_subj = raw_subject.upper().replace(' ', '_')
            current_subjects.add(norm_subj)
        
        for subj in SUBJECTS:
            new_course[f'subject_{subj}'] = 1 if subj in current_subjects else 0
            
        # If no known subject found, mark as UNKNOWN
        new_course['subject_UNKNOWN'] = 1 if not any(new_course[f'subject_{s}'] for s in SUBJECTS) else 0
        
        # Languages
        fully_translated = course.get('fullyTranslatedLanguages', [])
        if not isinstance(fully_translated, list): fully_translated = []
        new_course['fullyTranslatedLanguages_count'] = len(fully_translated)
        
        subtitles_only = course.get('subtitlesOnlyLanguages', [])
        n_subtitles = 0
        if isinstance(subtitles_only, list):
            n_subtitles = len(subtitles_only)
        elif isinstance(subtitles_only, str):
            try:
                # Try to parse string representation of list
                parsed = ast.literal_eval(subtitles_only)
                if isinstance(parsed, list):
                    n_subtitles = len(parsed)
            except:
                n_subtitles = 0
        
        new_course['subtitlesOnlyLanguages_count'] = n_subtitles
        
        # Calculate Raw Score for Language Richness
        # Base Score = 1.0, Weight = 0.2
        raw_score = 1.0 + (0.2 * n_subtitles)
        new_course['language_richness_raw'] = raw_score
        
        skills = course.get('skills', [])
        if not isinstance(skills, list): skills = []
        
        new_course['skills_count'] = len(skills)
        # Skill diversity: normalized by an arbitrary max (e.g., 20) or just raw count? 
        # Plan said: skills_count / max_skills (normalized). Let's use 20 as a reasonable max for normalization or just count.
        # Actually, let's stick to the plan but we don't know the global max yet. 
        # Let's just use raw count for now and maybe normalize later if needed, OR use a safe max like 50.
        new_course['skill_diversity'] = len(skills) / 50.0 
        
        hot_skill_count = sum(1 for s in skills if s in HOT_SKILLS)
        new_course['hot_skills_count'] = hot_skill_count
        new_course['has_hot_skill'] = 1 if hot_skill_count > 0 else 0
        
        new_course['skills_programming_count'] = count_domain_skills(skills, 'programming')
        new_course['skills_data_science_count'] = count_domain_skills(skills, 'data_science')
        
        # --- D. Endorsement ---
        partners = course.get('partners', [])
        if not isinstance(partners, list): partners = []
        
        new_course['partner_count'] = len(partners)
        
        has_top_uni = 1 if any(p in TOP_UNIVERSITIES or any(u in p for u in TOP_UNIVERSITIES) for p in partners) else 0
        new_course['has_top_university'] = has_top_uni
        
        has_tech = 1 if any(p in TOP_COMPANIES for p in partners) else 0
        new_course['has_tech_company'] = has_tech
        
        new_course['partner_Google_Cloud'] = 1 if any('Google Cloud' in p for p in partners) else 0
        
        # --- E. Interaction ---
        new_course['tech_company_programming'] = has_tech * (1 if new_course['skills_programming_count'] > 0 else 0)
        new_course['beginner_free'] = (1 if diff_num == 1.0 else 0) * (1 if is_free else 0)
        new_course['difficulty_duration_product'] = diff_num * dur_num
        
        # --- F. Target (Popularity) ---
        # Subscribers
        subs_raw = clean_subscribers(course.get("suscribers"))
        has_subs = 1 if subs_raw is not None else 0
        subs_log = math.log1p(subs_raw) if subs_raw is not None else 0.0

        # Ratings
        num_ratings = course.get("numProductRatings")
        if isinstance(num_ratings, (int, float)) and num_ratings >= 0:
            v = float(num_ratings)
        else:
            v = 0.0
        # has_ratings = 1 if v > 0 else 0 # Not requested in output but needed for calc
        ratings_log = math.log1p(v)

        # Adjusted rating
        raw_rating = course.get("avgProductRating")
        if isinstance(raw_rating, (int, float)) and v > 0:
            R = float(raw_rating)
            adjusted = (v / (v + M_SMOOTH)) * R + (M_SMOOTH / (v + M_SMOOTH)) * global_mean_rating
        else:
            adjusted = global_mean_rating

        # Expose intermediate features for Target Reconstruction
        new_course['subscribers_log'] = float(subs_log)
        new_course['ratings_log'] = float(ratings_log)
        new_course['adjusted_rating'] = float(adjusted)
        
        integrated_courses.append(new_course)

    # --- Post-Processing: Standardization & Popularity Score Calculation ---
    print("Standardizing Target Components & Calculating Popularity Score...")
    
    # Extract lists for vectorization
    subs_logs = np.array([c['subscribers_log'] for c in integrated_courses])
    ratings_logs = np.array([c['ratings_log'] for c in integrated_courses])
    adj_ratings = np.array([c['adjusted_rating'] for c in integrated_courses])
    
    # Min-Max Normalization Function
    def min_max_scale(arr):
        min_val = np.min(arr)
        max_val = np.max(arr)
        if max_val - min_val == 0:
            return np.zeros_like(arr)
        return (arr - min_val) / (max_val - min_val)
    
    # Apply Normalization (0 to 1 range)
    norm_subs = min_max_scale(subs_logs)
    norm_ratings = min_max_scale(ratings_logs)
    norm_adj = min_max_scale(adj_ratings)
    
    # Calculate Score with Standardized Components
    # Weights: 0.5 (Subs) + 0.3 (Reviews) + 0.2 (Rating)
    pop_scores = 0.5 * norm_subs + 0.3 * norm_ratings + 0.2 * norm_adj
    
    # Update courses with new values
    for i, c in enumerate(integrated_courses):
        c['subscribers_norm'] = float(norm_subs[i])
        c['ratings_norm'] = float(norm_ratings[i])
        c['adjusted_rating_norm'] = float(norm_adj[i])
        
        # Only update score if it had valid subscribers (otherwise 0)
        # Note: We rely on the imputation step later to fill zeros, 
        # but for now we calculate the score based on what we have.
        # If original subs was missing (0), norm_subs will reflect that low value.
        # The previous logic set popularity to 0 if has_subs was 0. Let's preserve that logic flag.
        
        # Check if original had subscribers (we can infer from subs_log > 0 or use a flag if we kept it)
        # But wait, subs_log is 0 if missing. 
        # Let's just assign the calculated score. The imputation script handles the rest.
        c['popularity_score'] = float(pop_scores[i])

    # --- Post-Processing for Language Richness Normalization ---
    print("Calculating Language Richness...")
    max_raw_score = max(c['language_richness_raw'] for c in integrated_courses)
    max_log_score = np.log(max_raw_score) if max_raw_score > 1.0 else 1.0
    
    print(f"Max Raw Score: {max_raw_score:.4f}")
    print(f"Max Log Score: {max_log_score:.4f}")
    
    for c in integrated_courses:
        raw = c.pop('language_richness_raw') # Remove raw score from final output
        log_score = np.log(raw)
        c['language_richness'] = log_score / max_log_score

    # --- Verification & Reporting ---
    print("\n" + "="*50)
    print("VERIFICATION: Language Richness")
    print("="*50)
    
    df_verify = pd.DataFrame(integrated_courses)
    if 'language_richness' in df_verify.columns:
        print("\nDescriptive Statistics:")
        print(df_verify['language_richness'].describe())
        
        print("\nSample Check (5 random rows):")
        sample_cols = ['name', 'subtitlesOnlyLanguages_count', 'language_richness']
        print(df_verify[sample_cols].sample(5).to_string())
    else:
        print("Error: language_richness column not found.")

    # Save
    output_file = Path('Courses_Integrated_Features.json')
    output_data = {'courses': integrated_courses}
    
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"Saved {len(integrated_courses)} courses to {output_file}")

if __name__ == "__main__":
    main()
