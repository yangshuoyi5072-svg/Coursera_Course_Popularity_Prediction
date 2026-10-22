import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

def prepare_model_data():
    print("Loading Courses_Integrated_Features.json...")
    with open('Courses_Integrated_Features.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data['courses'])
    print(f"Initial Shape: {df.shape}")

    # --- Step 1: Handle High Missing Values (instructor_rating) ---
    print("\n--- Step 1: Handling Missing Instructor Ratings ---")
    df['instructor_rating_missing'] = df['instructor_rating'].isnull().astype(int)
    df['instructor_rating'] = df['instructor_rating'].fillna(-1)
    print("Created 'instructor_rating_missing' flag and imputed 'instructor_rating' with -1.")

    # --- Step 2: Remove Zero Variance Features ---
    print("\n--- Step 2: Removing Zero Variance Features ---")
    cols_to_drop = ['is_specialization', 'is_professional_certificate', 'fullyTranslatedLanguages_count']
    existing_cols_to_drop = [c for c in cols_to_drop if c in df.columns]
    if existing_cols_to_drop:
        df.drop(columns=existing_cols_to_drop, inplace=True)
        print(f"Dropped columns: {existing_cols_to_drop}")
    else:
        print("No zero variance columns found to drop.")

    # --- Step 3: Target Reconstruction Strategy ---
    print("\n--- Step 3: Target Reconstruction (Subscribers) ---")
    
    # Features for prediction
    # Note: 'numProductRatings' might not be in df, using 'ratings_log' and 'adjusted_rating'
    features = ['ratings_log', 'adjusted_rating']
    target = 'subscribers_log'
    
    # Split into Train (known subscribers) and Predict (missing/zero subscribers)
    # Assuming 0.0 log means 0 subscribers (or missing in original logic)
    train_mask = df[target] > 0
    predict_mask = df[target] == 0
    
    train_df = df[train_mask]
    predict_df = df[predict_mask]
    
    print(f"Train Set (Known Subscribers): {len(train_df)}")
    print(f"Prediction Set (Missing/Zero Subscribers): {len(predict_df)}")
    
    if len(train_df) > 0 and len(predict_df) > 0:
        X_train = train_df[features]
        y_train = train_df[target]
        X_predict = predict_df[features]
        
        # Train Random Forest
        rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        
        # Evaluate on Train (OOB or just Training Score for sanity)
        train_score = rf.score(X_train, y_train)
        print(f"Model R^2 Score (Training): {train_score:.4f}")
        
        # Predict
        predicted_subscribers = rf.predict(X_predict)
        
        # Fill missing values
        df.loc[predict_mask, target] = predicted_subscribers
        print("Imputed missing 'subscribers_log' values.")
        
        # Recalculate Popularity Score with Standardization
        # 1. Re-standardize subscribers_log (now that we have full data)
        min_sub = df['subscribers_log'].min()
        max_sub = df['subscribers_log'].max()
        df['subscribers_norm'] = (df['subscribers_log'] - min_sub) / (max_sub - min_sub)
        
        # 2. Ensure other norms are present (or re-calc if needed, but they should be there)
        # Let's re-calc to be 100% safe and consistent
        min_rat = df['ratings_log'].min()
        max_rat = df['ratings_log'].max()
        df['ratings_norm'] = (df['ratings_log'] - min_rat) / (max_rat - min_rat)
        
        min_adj = df['adjusted_rating'].min()
        max_adj = df['adjusted_rating'].max()
        df['adjusted_rating_norm'] = (df['adjusted_rating'] - min_adj) / (max_adj - min_adj)

        # 3. Calculate Score
        # Formula: 0.5 * subs_norm + 0.3 * ratings_norm + 0.2 * adj_norm
        df['popularity_score'] = (0.5 * df['subscribers_norm']) + \
                                 (0.3 * df['ratings_norm']) + \
                                 (0.2 * df['adjusted_rating_norm'])
        print("Recalculated 'popularity_score' using standardized components.")
        
    else:
        print("Skipping reconstruction: Not enough data for split.")

    # --- Step 4: Final Cleanup ---
    print("\n--- Step 4: Final Cleanup ---")
    if 'popularity_score_global' in df.columns:
        df.drop(columns=['popularity_score_global'], inplace=True)
        print("Dropped 'popularity_score_global'.")
        
    # Save
    output_file = 'Courses_Final_Model_Ready.json'
    # Convert back to dict structure if needed, or just list of records
    output_data = {'courses': df.to_dict(orient='records')}
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"\nSaved final dataset to {output_file}")
    print("\nFinal DataFrame Info:")
    df.info()

if __name__ == "__main__":
    prepare_model_data()
