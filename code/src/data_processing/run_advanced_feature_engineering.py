import json
import pandas as pd
import numpy as np
import re

# Load data
print("Loading Courses_Engineered_Features.json...")
with open('Courses_Engineered_Features.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

df = pd.DataFrame(data['courses'])
print(f"Loaded {len(df)} records with {len(df.columns)} features")

# ==========================================
# NEW FEATURE SET 1: Course Name Analysis
# ==========================================
print("\n1. Analyzing course names...")

# Name length
df['name_length'] = df['name'].apply(lambda x: len(str(x)) if pd.notna(x) else 0)
df['name_word_count'] = df['name'].apply(lambda x: len(str(x).split()) if pd.notna(x) else 0)

# Hot keywords in name
HOT_KEYWORDS = {
    'python', 'data', 'machine learning', 'ai', 'artificial intelligence',
    'deep learning', 'sql', 'business', 'marketing', 'finance',
    'leadership', 'management', 'cloud', 'aws', 'google', 'microsoft',
    'java', 'javascript', 'web', 'mobile', 'blockchain', 'cybersecurity'
}

def count_hot_keywords(name):
    if pd.isna(name):
        return 0
    name_lower = str(name).lower()
    return sum(1 for keyword in HOT_KEYWORDS if keyword in name_lower)

df['name_hot_keywords'] = df['name'].apply(count_hot_keywords)
df['has_hot_keyword_in_name'] = (df['name_hot_keywords'] > 0).astype(int)

# Specific popular terms
df['name_has_python'] = df['name'].apply(lambda x: 1 if 'python' in str(x).lower() else 0)
df['name_has_data'] = df['name'].apply(lambda x: 1 if 'data' in str(x).lower() else 0)
df['name_has_business'] = df['name'].apply(lambda x: 1 if 'business' in str(x).lower() else 0)

print(f"  Created {6} name-based features")

# ==========================================
# NEW FEATURE SET 2: Top Universities One-Hot
# ==========================================
print("\n2. Creating top university indicators...")

TOP_UNIVERSITIES_DETAILED = [
    'Stanford University', 'University of Michigan', 'University of Pennsylvania',
    'Yale University', 'Duke University', 'Johns Hopkins University',
    'University of Illinois', 'Northwestern University', 'University of California',
    'Imperial College London', 'University of London'
]

for uni in TOP_UNIVERSITIES_DETAILED:
    col_name = f"partner_{uni.replace(' ', '_').replace(',', '')[:20]}"
    df[col_name] = df['partners'].apply(
        lambda x: 1 if isinstance(x, list) and any(uni in p for p in x) else 0
    )

print(f"  Created {len(TOP_UNIVERSITIES_DETAILED)} university indicator features")

# ==========================================
# NEW FEATURE SET 3: Skill Domain Classification
# ==========================================
print("\n3. Classifying skill domains...")

SKILL_DOMAINS = {
    'programming': {'Python', 'Java', 'JavaScript', 'C++', 'R', 'SQL', 'HTML', 'CSS', 'PHP', 'Ruby'},
    'data_science': {'Machine Learning', 'Deep Learning', 'Data Analysis', 'Data Science', 
                     'Artificial Intelligence', 'Big Data', 'Statistics', 'Data Visualization'},
    'cloud': {'Cloud Computing', 'AWS', 'Azure', 'Google Cloud Platform', 'Docker', 'Kubernetes'},
    'business': {'Project Management', 'Leadership', 'Marketing', 'Finance', 'Accounting', 
                 'Strategy', 'Entrepreneurship'},
    'soft_skills': {'Communication', 'Critical Thinking', 'Problem Solving', 'Teamwork'}
}

def classify_skills(skills_list):
    if not isinstance(skills_list, list):
        return {domain: 0 for domain in SKILL_DOMAINS}
    
    counts = {domain: 0 for domain in SKILL_DOMAINS}
    for skill in skills_list:
        for domain, keywords in SKILL_DOMAINS.items():
            if skill in keywords or any(kw.lower() in skill.lower() for kw in keywords):
                counts[domain] += 1
    return counts

skill_domain_counts = df['skills'].apply(classify_skills)

for domain in SKILL_DOMAINS:
    df[f'skills_{domain}_count'] = skill_domain_counts.apply(lambda x: x[domain])
    df[f'has_{domain}_skill'] = (df[f'skills_{domain}_count'] > 0).astype(int)

print(f"  Created {len(SKILL_DOMAINS) * 2} skill domain features")

# ==========================================
# NEW FEATURE SET 4: Advanced Interactions
# ==========================================
print("\n4. Creating advanced interaction features...")

# Difficulty × Free interaction
df['beginner_free'] = df['difficulty_BEGINNER'] * df['isCourseFree_int']
df['advanced_paid'] = df['difficulty_ADVANCED'] * (1 - df['isCourseFree_int'])

# Top university × Advanced difficulty
df['top_uni_advanced'] = df['has_top_university'] * df['difficulty_ADVANCED']

# Tech company × Programming skills
df['tech_company_programming'] = df['has_tech_company'] * df['has_programming_skill']

# Skill diversity (normalized)
df['skill_diversity'] = df['skills_count'] / (df['skills_count'].max() + 1)

# Partner-skill ratio
df['partner_skill_ratio'] = df['partner_count'] / (df['skills_count'] + 1)

# Language richness × Subject
df['language_richness'] = df['language_count'] / (df['language_count'].max() + 1)

print(f"  Created 7 interaction features")

# ==========================================
# NEW FEATURE SET 5: Aggregation Enhancements
# ==========================================
print("\n5. Creating enhanced aggregation features...")

# Difficulty × Subject aggregations
for diff_level in [1.0, 2.0, 3.0]:  # Beginner, Intermediate, Advanced
    mask = df['difficulty_level_num'] == diff_level
    if mask.sum() > 0:
        avg_pop = df[mask]['popularity_score_global'].mean()
        df[f'diff_{int(diff_level)}_avg_pop'] = avg_pop

# Free vs Paid by subject
for subject in df['subject'].unique():
    if pd.notna(subject):
        mask_free = (df['subject'] == subject) & (df['isCourseFree'] == True)
        mask_paid = (df['subject'] == subject) & (df['isCourseFree'] == False)
        
        if mask_free.sum() > 0:
            df.loc[df['subject'] == subject, 'subject_free_avg_pop'] = \
                df[mask_free]['popularity_score_global'].mean()
        if mask_paid.sum() > 0:
            df.loc[df['subject'] == subject, 'subject_paid_avg_pop'] = \
                df[mask_paid]['popularity_score_global'].mean()

df['subject_free_avg_pop'] = df['subject_free_avg_pop'].fillna(df['popularity_score_global'].mean())
df['subject_paid_avg_pop'] = df['subject_paid_avg_pop'].fillna(df['popularity_score_global'].mean())

print(f"  Created aggregation features")

# ==========================================
# Summary
# ==========================================
new_feature_count = len(df.columns) - len(data['courses'][0])
print(f"\n{'='*70}")
print(f"FEATURE ENGINEERING COMPLETE")
print(f"{'='*70}")
print(f"Original features: {len(data['courses'][0])}")
print(f"New features added: {new_feature_count}")
print(f"Total features: {len(df.columns)}")

# Save enhanced dataset
output_data = {
    "courses": df.to_dict(orient='records'),
    "_metadata": {
        "source": "Courses_Engineered_Features.json",
        "total_records": len(df),
        "features_count": len(df.columns),
        "new_features_added": new_feature_count,
        "feature_categories": [
            "Name Analysis (6 features)",
            "Top University Indicators (11 features)",
            "Skill Domain Classification (10 features)",
            "Advanced Interactions (7 features)",
            "Enhanced Aggregations"
        ]
    }
}

with open('Courses_Advanced_Features.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2)

print(f"\nSaved to: Courses_Advanced_Features.json")
print("Ready for model training with enhanced features!")
