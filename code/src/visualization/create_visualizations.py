"""
Create visualizations for the report
Generates essential charts for data analysis report
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
from collections import Counter
import numpy as np

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

def load_data():
    """Load enhanced course data"""
    path = Path("data/AllCourses_Enhanced.json")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data["courses"])


def plot_product_type_distribution(df):
    """Plot distribution of product types"""
    fig, ax = plt.subplots(figsize=(10, 6))
    product_counts = df['productType'].value_counts()
    product_counts.plot(kind='bar', ax=ax, color='steelblue', edgecolor='black')
    ax.set_xlabel('Product Type', fontsize=12)
    ax.set_ylabel('Number of Courses', fontsize=12)
    ax.set_title('Distribution of Product Types', fontsize=14, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig('visualizations/product_type_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Created: product_type_distribution.png")


def plot_subject_distribution(df):
    """Plot distribution of subjects"""
    fig, ax = plt.subplots(figsize=(10, 8))
    subjects = df['subject'].dropna().value_counts().sort_values(ascending=True)
    subjects.plot(kind='barh', ax=ax, color='coral', edgecolor='black')
    ax.set_xlabel('Number of Courses', fontsize=12)
    ax.set_ylabel('Subject', fontsize=12)
    ax.set_title('Distribution of Courses by Subject', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('visualizations/subject_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Created: subject_distribution.png")


def plot_rating_distribution(df):
    """Plot distribution of ratings"""
    fig, ax = plt.subplots(figsize=(10, 6))
    ratings = df['avgProductRating'].dropna()
    ax.hist(ratings, bins=20, color='skyblue', edgecolor='black', alpha=0.7)
    ax.set_xlabel('Average Rating', fontsize=12)
    ax.set_ylabel('Number of Courses', fontsize=12)
    ax.set_title('Distribution of Course Ratings', fontsize=14, fontweight='bold')
    ax.axvline(ratings.mean(), color='red', linestyle='--', label=f'Mean: {ratings.mean():.2f}')
    ax.axvline(ratings.median(), color='green', linestyle='--', label=f'Median: {ratings.median():.2f}')
    ax.legend()
    plt.tight_layout()
    plt.savefig('visualizations/rating_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Created: rating_distribution.png")


def plot_rating_by_product_type(df):
    """Plot rating distribution by product type"""
    fig, ax = plt.subplots(figsize=(12, 6))
    df_with_ratings = df[df['avgProductRating'].notna()]
    sns.boxplot(data=df_with_ratings, x='productType', y='avgProductRating', ax=ax)
    ax.set_xlabel('Product Type', fontsize=12)
    ax.set_ylabel('Average Rating', fontsize=12)
    ax.set_title('Rating Distribution by Product Type', fontsize=14, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig('visualizations/rating_by_product_type.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Created: rating_by_product_type.png")


def plot_rating_by_subject(df):
    """Plot rating distribution by subject"""
    fig, ax = plt.subplots(figsize=(12, 8))
    df_with_ratings = df[(df['avgProductRating'].notna()) & (df['subject'].notna())]
    sns.boxplot(data=df_with_ratings, x='avgProductRating', y='subject', ax=ax, orient='h')
    ax.set_xlabel('Average Rating', fontsize=12)
    ax.set_ylabel('Subject', fontsize=12)
    ax.set_title('Rating Distribution by Subject', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('visualizations/rating_by_subject.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Created: rating_by_subject.png")


def plot_rating_count_distribution(df):
    """Plot distribution of rating counts (log scale)"""
    fig, ax = plt.subplots(figsize=(10, 6))
    rating_counts = df['numProductRatings'].dropna()
    ax.hist(rating_counts, bins=50, color='lightgreen', edgecolor='black', alpha=0.7)
    ax.set_xlabel('Number of Ratings', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_yscale('log')
    ax.set_title('Distribution of Rating Counts (Log Scale)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('visualizations/rating_count_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Created: rating_count_distribution.png")


def plot_missing_values_by_product_type(df):
    """Plot missing values by product type"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Subtitles missing
    missing_subtitles = df.groupby('productType').apply(
        lambda x: (x['subtitlesOnlyLanguages'].isna() | x['subtitlesOnlyLanguages'].apply(lambda y: y == [] if isinstance(y, list) else False)).sum() / len(x) * 100
    ).sort_values(ascending=False)
    missing_subtitles.plot(kind='bar', ax=ax1, color='salmon', edgecolor='black')
    ax1.set_xlabel('Product Type', fontsize=12)
    ax1.set_ylabel('Missing Rate (%)', fontsize=12)
    ax1.set_title('subtitlesOnlyLanguages Missing Rate by Product Type', fontsize=12, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    
    # Rating missing
    missing_rating = df.groupby('productType').apply(
        lambda x: x['avgProductRating'].isna().sum() / len(x) * 100
    ).sort_values(ascending=False)
    missing_rating.plot(kind='bar', ax=ax2, color='lightcoral', edgecolor='black')
    ax2.set_xlabel('Product Type', fontsize=12)
    ax2.set_ylabel('Missing Rate (%)', fontsize=12)
    ax2.set_title('avgProductRating Missing Rate by Product Type', fontsize=12, fontweight='bold')
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('visualizations/missing_values_by_product_type.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Created: missing_values_by_product_type.png")


def plot_free_vs_paid(df):
    """Plot comparison of free vs paid courses"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Rating comparison
    df_with_ratings = df[df['avgProductRating'].notna()]
    sns.boxplot(data=df_with_ratings, x='isCourseFree', y='avgProductRating', ax=ax1)
    ax1.set_xlabel('Is Course Free', fontsize=12)
    ax1.set_ylabel('Average Rating', fontsize=12)
    ax1.set_title('Rating: Free vs Paid Courses', fontsize=12, fontweight='bold')
    ax1.set_xticklabels(['Paid', 'Free'])
    
    # Count comparison
    free_counts = df['isCourseFree'].value_counts()
    free_counts.plot(kind='bar', ax=ax2, color=['steelblue', 'orange'], edgecolor='black')
    ax2.set_xlabel('Is Course Free', fontsize=12)
    ax2.set_ylabel('Number of Courses', fontsize=12)
    ax2.set_title('Count: Free vs Paid Courses', fontsize=12, fontweight='bold')
    ax2.set_xticklabels(['Paid', 'Free'], rotation=0)
    
    plt.tight_layout()
    plt.savefig('visualizations/free_vs_paid.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Created: free_vs_paid.png")


def plot_correlation_heatmap(df):
    """Plot correlation heatmap"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Select numerical columns
    numerical_cols = ['avgProductRating', 'numProductRatings']
    df_numerical = df[numerical_cols].copy()
    
    # Add skills count
    df_numerical['skills_count'] = df['skills'].apply(lambda x: len(x) if isinstance(x, list) else 0)
    
    # Calculate correlation
    corr_matrix = df_numerical.corr()
    
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, 
                square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
    ax.set_title('Correlation Heatmap', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('visualizations/correlation_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Created: correlation_heatmap.png")


def plot_outliers_boxplot(df):
    """Plot box plot for outliers"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Rating counts
    rating_counts = df['numProductRatings'].dropna()
    ax1.boxplot(rating_counts, vert=True)
    ax1.set_ylabel('Number of Ratings', fontsize=12)
    ax1.set_title('Outliers in Rating Counts', fontsize=12, fontweight='bold')
    ax1.set_yscale('log')
    
    # Ratings
    ratings = df['avgProductRating'].dropna()
    ax2.boxplot(ratings, vert=True)
    ax2.set_ylabel('Average Rating', fontsize=12)
    ax2.set_title('Outliers in Ratings', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('visualizations/outliers_boxplot.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Created: outliers_boxplot.png")


def main():
    """Main function to create all visualizations"""
    print("=" * 70)
    print("CREATING VISUALIZATIONS FOR REPORT")
    print("=" * 70)
    
    # Create output directory
    Path("visualizations").mkdir(exist_ok=True)
    
    # Load data
    print("\nLoading data...")
    df = load_data()
    print(f"Loaded {len(df):,} courses")
    
    # Create visualizations
    print("\nCreating visualizations...")
    plot_product_type_distribution(df)
    plot_subject_distribution(df)
    plot_rating_distribution(df)
    plot_rating_by_product_type(df)
    plot_rating_by_subject(df)
    plot_rating_count_distribution(df)
    plot_missing_values_by_product_type(df)
    plot_free_vs_paid(df)
    plot_correlation_heatmap(df)
    plot_outliers_boxplot(df)
    
    print("\n" + "=" * 70)
    print("All visualizations created successfully!")
    print("=" * 70)
    print(f"\nOutput directory: visualizations/")
    print(f"Total files created: 10")


if __name__ == "__main__":
    main()

