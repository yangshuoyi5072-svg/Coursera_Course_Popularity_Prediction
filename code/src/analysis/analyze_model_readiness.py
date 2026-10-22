import json
import pandas as pd
import numpy as np
import os

def analyze_model_readiness(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    if isinstance(data, dict) and 'courses' in data:
        df = pd.DataFrame(data['courses'])
    else:
        df = pd.DataFrame(data)

    report_lines = []
    report_lines.append("# Model Readiness Report\n")
    report_lines.append(f"**File**: `{file_path}`\n")
    report_lines.append(f"**Total Samples**: {len(df)}\n")
    report_lines.append(f"**Total Features**: {len(df.columns)}\n")

    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    
    report_lines.append("## 1. Missing Values\n")
    if missing.empty:
        report_lines.append("No missing values found. Dataset is clean.\n")
    else:
        report_lines.append("| Feature | Missing Count | Percentage |\n")
        report_lines.append("|---|---|---|\n")
        for feat, count in missing.items():
            pct = (count / len(df)) * 100
            report_lines.append(f"| {feat} | {count} | {pct:.2f}% |\n")
        report_lines.append("\n> ⚠️ **Action Required**: Impute or drop these features before training.\n")

    report_lines.append("\n## 2. Data Types\n")
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    num_df = df.select_dtypes(include=numerics)
    cat_df = df.select_dtypes(exclude=numerics)
    
    report_lines.append(f"- **Numeric Features**: {len(num_df.columns)}\n")
    report_lines.append(f"- **Categorical/Object Features**: {len(cat_df.columns)}\n")
    
    if not cat_df.empty:
        report_lines.append("\n**Categorical Features (Need Encoding):**\n")
        report_lines.append("| Feature | Unique Values | Example |\n")
        report_lines.append("|---|---|---|\n")
        for col in cat_df.columns:
            unique_count = df[col].nunique()
            example = str(df[col].iloc[0])[:50]
            report_lines.append(f"| {col} | {unique_count} | {example} |\n")
    
    report_lines.append("\n## 3. Zero Variance Features\n")
    constant_cols = [col for col in df.columns if df[col].nunique() <= 1]
    
    if constant_cols:
        report_lines.append("**The following features have zero variance (constant values) and should be dropped:**\n")
        for col in constant_cols:
            report_lines.append(f"- `{col}`\n")
    else:
        report_lines.append(" No constant features found.\n")

    target_col = 'popularity_score'
    if target_col in df.columns:
        report_lines.append(f"\n## 4. Target Variable: `{target_col}`\n")
        desc = df[target_col].describe()
        report_lines.append(f"- **Mean**: {desc['mean']:.4f}\n")
        report_lines.append(f"- **Std**: {desc['std']:.4f}\n")
        report_lines.append(f"- **Min**: {desc['min']:.4f}\n")
        report_lines.append(f"- **Max**: {desc['max']:.4f}\n")
        
        skew = df[target_col].skew()
        report_lines.append(f"- **Skewness**: {skew:.4f}\n")
        if abs(skew) > 1:
            report_lines.append(">  Target is skewed. Consider log-transformation if not already done.\n")
    else:
        report_lines.append(f"\n## 4. Target Variable\n⚠️ Target `{target_col}` not found!\n")

    if target_col in df.columns and not num_df.empty:
        report_lines.append("\n## 5. Top Correlations with Target\n")
        corr_matrix = num_df.corr()
        if target_col in corr_matrix.columns:
            target_corr = corr_matrix[target_col].sort_values(ascending=False)
            top_corr = target_corr[1:11] # Top 10 positive (excluding self)
            bot_corr = target_corr[-10:] # Top 10 negative
            
            report_lines.append("| Feature | Correlation |\n")
            report_lines.append("|---|---|\n")
            for feat, val in top_corr.items():
                report_lines.append(f"| {feat} | {val:.4f} |\n")
            for feat, val in bot_corr.items():
                report_lines.append(f"| {feat} | {val:.4f} |\n")

    with open('MODEL_READINESS_REPORT.md', 'w', encoding='utf-8') as f:
        f.writelines(report_lines)

if __name__ == "__main__":
    analyze_model_readiness('Courses_Integrated_Features.json')
