# 1. Partner Features

print("Engineering Partner Features...")


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

def process_partners(partners):
    if not isinstance(partners, list):
        return 0, 0, 0, 'none'
    
    count = len(partners)
    has_top_uni = 1 if any(p in TOP_UNIVERSITIES or any(u in p for u in TOP_UNIVERSITIES) for p in partners) else 0
    has_tech = 1 if any(p in TOP_COMPANIES for p in partners) else 0
    

    is_uni = any('University' in p or 'College' in p or 'Institute' in p for p in partners)
    is_comp = any(p in TOP_COMPANIES for p in partners)
    
    if is_uni and is_comp:
        p_type = 'mixed'
    elif is_uni:
        p_type = 'university'
    elif is_comp:
        p_type = 'company'
    else:
        p_type = 'other'
        
    return count, has_top_uni, has_tech, p_type


partner_features = df['partners'].apply(process_partners)
df['partner_count'] = [x[0] for x in partner_features]
df['has_top_university'] = [x[1] for x in partner_features]
df['has_tech_company'] = [x[2] for x in partner_features]
df['partner_type'] = [x[3] for x in partner_features]


print("Engineering Skill Features...")

HOT_SKILLS = {
    'Python', 'Java', 'SQL', 'C++', 'JavaScript', 'R', 'HTML', 'CSS',
    'Machine Learning', 'Deep Learning', 'Artificial Intelligence', 'Data Analysis', 
    'Data Science', 'Big Data', 'Cloud Computing', 'Blockchain',
    'Project Management', 'Leadership', 'Communication', 'Marketing', 'Finance'
}

def process_skills(skills):
    if not isinstance(skills, list):
        return 0, 0, 0
    
    count = len(skills)
    has_hot = 1 if any(s in HOT_SKILLS for s in skills) else 0
    hot_count = sum(1 for s in skills if s in HOT_SKILLS)
    
    return count, has_hot, hot_count

skill_features = df['skills'].apply(process_skills)
df['skills_count'] = [x[0] for x in skill_features]
df['has_hot_skill'] = [x[1] for x in skill_features]
df['hot_skills_count'] = [x[2] for x in skill_features]


print("Engineering Language Features...")

def process_languages(langs):
    if not isinstance(langs, list):
        return 0
    return len(langs)

df['language_count'] = df['fullyTranslatedLanguages'].apply(process_languages)


print("Engineering Interaction Features...")


df['rating_reliability'] = df['numProductRatings'] / (df['numProductRatings'] + 100)
df['quality_score'] = df['adjusted_rating'] * df['rating_reliability']


df['rating_count_interaction'] = df['adjusted_rating'] * df['ratings_log']


df['difficulty_duration_product'] = df['difficulty_level_num'] * df['duration_level_num']


df['free_subject'] = df['isCourseFree'].astype(str) + "_" + df['subject']


print("Engineering Aggregation Features...")


subject_stats = df.groupby('subject').agg({
    'popularity_score_global': ['mean', 'median'],
    'adjusted_rating': 'mean',
    'numProductRatings': 'mean',
    'id': 'count'
}).reset_index()
subject_stats.columns = ['subject', 'subject_avg_popularity', 'subject_median_popularity', 
                         'subject_avg_rating', 'subject_avg_num_ratings', 'subject_course_count']

df = df.merge(subject_stats, on='subject', how='left')


diff_stats = df.groupby('difficulty_level_num').agg({
    'popularity_score_global': 'mean',
    'adjusted_rating': 'mean'
}).reset_index()
diff_stats.columns = ['difficulty_level_num', 'difficulty_avg_popularity', 'difficulty_avg_rating']

df = df.merge(diff_stats, on='difficulty_level_num', how='left')


print("Engineering Relative Features...")

df['popularity_vs_subject_avg'] = df['popularity_score_global'] - df['subject_avg_popularity']
df['rating_vs_subject_avg'] = df['adjusted_rating'] - df['subject_avg_rating']
df['popularity_vs_difficulty_avg'] = df['popularity_score_global'] - df['difficulty_avg_popularity']


print("\nSaving Courses_Engineered_Features.json...")


output_data = {
    "courses": df.to_dict(orient='records'),
    "_metadata": {
        "source": "Courses_Only_Dataset.json",
        "total_records": len(df),
        "features_count": len(df.columns),
        "engineered_features": [
            "partner_count", "has_top_university", "has_tech_company", "partner_type",
            "skills_count", "has_hot_skill", "hot_skills_count",
            "language_count",
            "quality_score", "rating_count_interaction", "rating_reliability",
            "subject_avg_popularity", "popularity_vs_subject_avg"
        ]
    }
}

with open('data/Courses_Engineered_Features.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2)

print(f"✓ Saved {len(df)} records with {len(df.columns)} features")
print("Feature Engineering Complete!")
