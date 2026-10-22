import json
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
import io
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
import xgboost as xgb

# Force UTF-8 for stdout/stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Set plotting style
sns.set(style="whitegrid")
plt.rcParams['font.sans-serif'] = ['SimHei'] 
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = "模型训练图片结果"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def run_classification_training():
    print("Loading Courses_Classification_Ready.json...")
    with open('Courses_Classification_Ready.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data['courses'])
    
    # --- Feature Selection ---
    leakage_cols = [
        'subscribers_log', 'ratings_log', 'adjusted_rating', 
        'subscribers_norm', 'ratings_norm', 'adjusted_rating_norm', # Drop normalized components
        'popularity_score_global', 'suscribers', 'numProductRatings', 
        'avgProductRating', 'reviews', 'popularity_score' # Drop continuous target
    ]
    id_cols = ['id', 'url', 'name', 'skills', 'instructors', 'partners'] 
    target_col = 'popularity_class'
    
    cols_to_drop = leakage_cols + id_cols
    X = df.drop(columns=[c for c in cols_to_drop if c in df.columns] + [target_col])
    y = df[target_col]
    X = X.select_dtypes(include=[np.number])
    
    print(f"Features used ({len(X.columns)}): {list(X.columns)}")
    print(f"Target Class Distribution:\n{y.value_counts().sort_index()}")
    
    # --- 8-1-1 Stratified Split ---
    print("\n--- Splitting Data (8-1-1 Stratified) ---")
    
    # 1. Split Test (10%)
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.1, stratify=y, random_state=42
    )
    
    # 2. Split Validation (10% of total -> 1/9 of remaining)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=1/9, stratify=y_temp, random_state=42
    )
    
    print(f"Train Set: {X_train.shape[0]} samples")
    print(f"Val Set:   {X_val.shape[0]} samples")
    print(f"Test Set:  {X_test.shape[0]} samples")
    
    # --- Model Definition ---
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1),
        "XGBoost": xgb.XGBClassifier(n_estimators=200, learning_rate=0.05, max_depth=6, random_state=42, n_jobs=-1)
    }
    
    results = {}
    
    # --- Training & CV ---
    print("\n--- Training & Cross-Validation (5-Fold) ---")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    for name, model in models.items():
        print(f"Evaluating {name}...")
        cv_scores = cross_val_score(model, X_train, y_train, cv=skf, scoring='accuracy')
        mean_cv = cv_scores.mean()
        results[name] = {"cv_score": mean_cv, "model": model}
        print(f"  Mean CV Accuracy: {mean_cv:.4f}")
        
        # Train on full train set
        model.fit(X_train, y_train)
        
        # Evaluate on Validation Set
        val_pred = model.predict(X_val)
        val_acc = accuracy_score(y_val, val_pred)
        results[name]["val_score"] = val_acc
        print(f"  Validation Accuracy: {val_acc:.4f}")

    # --- Select Best Model ---
    best_model_name = max(results, key=lambda k: results[k]["val_score"])
    best_model = results[best_model_name]["model"]
    print(f"\n🏆 Best Model: {best_model_name} (Val Acc: {results[best_model_name]['val_score']:.4f})")
    
    # --- Final Evaluation on Test Set ---
    print("\n--- Final Evaluation on Test Set ---")
    y_test_pred = best_model.predict(X_test)
    
    test_acc = accuracy_score(y_test, y_test_pred)
    test_f1 = f1_score(y_test, y_test_pred, average='macro')
    
    print(f"Test Accuracy: {test_acc:.4f}")
    print(f"Test F1 (Macro): {test_f1:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_test_pred))
    
    # --- Confusion Matrix Plot ---
    plt.figure(figsize=(8, 6))
    cm = confusion_matrix(y_test, y_test_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
    plt.title(f'Confusion Matrix ({best_model_name})')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'confusion_matrix.png'))
    print(f"Saved confusion matrix to {os.path.join(OUTPUT_DIR, 'confusion_matrix.png')}")
    
    # --- Save Best Model ---
    joblib.dump(best_model, 'best_classification_model.pkl')
    print("Saved best model to best_classification_model.pkl")

    # --- Generate Detailed Report for ALL Models ---
    report_file = "model_evaluation_report.txt"
    print(f"\nGenerating detailed report to {report_file}...")
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("==================================================\n")
        f.write("       MODEL CLASSIFICATION PERFORMANCE REPORT\n")
        f.write("==================================================\n\n")
        
        for name, model in models.items():
            # Evaluate on Test Set
            y_pred = model.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='macro')
            
            f.write(f"--- Model: {name} ---\n")
            f.write(f"Test Accuracy:   {acc:.4f}\n")
            f.write(f"Test F1 (Macro): {f1:.4f}\n")
            f.write("\nDetailed Classification Report:\n")
            f.write(classification_report(y_test, y_pred))
            f.write("\n" + "="*50 + "\n\n")
            
    print(f"Detailed report saved to {report_file}")

if __name__ == "__main__":
    run_classification_training()
