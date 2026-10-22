import json
import pandas as pd
import numpy as np

def prepare_classification_data():
    print("Loading Courses_Final_Model_Ready.json...")
    with open('Courses_Final_Model_Ready.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data['courses'])
    
    print(f"Initial Shape: {df.shape}")
    
    # --- 1. Create Target Class (Quantile Binning) ---
    # We want 3 balanced classes: 0 (Low), 1 (Medium), 2 (High)
    print("\n--- Creating Popularity Classes (3 Quantiles) ---")
    
    df['popularity_class'], bins = pd.qcut(
        df['popularity_score'], 
        q=3, 
        labels=[0, 1, 2], 
        retbins=True
    )
    
    # Convert to int for safety
    df['popularity_class'] = df['popularity_class'].astype(int)
    
    print("Class Distribution:")
    print(df['popularity_class'].value_counts().sort_index())
    
    print("\nScore Ranges for each Class:")
    for i in range(3):
        print(f"Class {i}: {bins[i]:.4f} - {bins[i+1]:.4f}")
        
    # --- 2. Save New Dataset ---
    output_file = 'Courses_Classification_Ready.json'
    
    # Convert back to list of dicts
    courses_list = df.to_dict(orient='records')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({'courses': courses_list}, f, indent=2, ensure_ascii=False)
        
    print(f"\nSaved {len(courses_list)} courses to {output_file}")

if __name__ == "__main__":
    prepare_classification_data()
