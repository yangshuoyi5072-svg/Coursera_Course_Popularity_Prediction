# Code & Technical Pipeline Guide

This directory contains the complete source code, datasets, and pretrained models for the Coursera course popularity analysis.

For high-level project insights, methodology, and links to the full research report, please refer to the [Root README](../README.md).

---

## Directory Structure

```text
code/
├── requirements.txt                     # Python dependencies
├── best_classification_model.pkl        # Serialized optimal classification model
├── data/                                # Curated datasets (JSON format)
│   ├── README.md                        # Dataset summary & metadata
│   ├── AllCourses_Enhanced.json         # Raw scraped product records (18,387)
│   ├── Courses_Only_Dataset.json        # Course-only subset (14,006)
│   ├── Courses_Engineered_Features.json # Feature-engineered dataset (80 features)
│   └── Courses_Final_Model_Ready.json   # Model-ready dataset (52 features)
└── src/
    ├── data_collection/                 # Web scrapers (GraphQL API, Selenium, Playwright)
    │   ├── coursera_graphql_scraper.py
    │   ├── coursera_full_scraper.py
    │   ├── coursera_batch_scraper.py
    │   ├── incremental_scraper.py
    │   ├── scrape_subjects.py
    │   └── coursera_playwright_scraper.py
    ├── data_processing/                 # Cleaning, imputation & feature engineering
    │   ├── filter_courses_only.py
    │   ├── clean_instructors_data.py
    │   ├── process_instructors_features.py
    │   ├── add_difficulty_features.py
    │   ├── add_duration_features.py
    │   ├── add_subject_one_hot.py
    │   ├── add_product_type_one_hot.py
    │   ├── add_popularity_targets.py
    │   ├── merge_courses_with_subscribers.py
    │   ├── merge_image_urls.py
    │   ├── integrate_features.py
    │   ├── run_feature_engineering.py
    │   ├── run_advanced_feature_engineering.py
    │   ├── prepare_model_data.py
    │   └── prepare_classification_data.py
    ├── modeling/                        # Machine learning training & evaluation
    │   └── run_classification_training.py
    ├── visualization/                   # Plotting and figure generation
    │   └── create_visualizations.py
    └── analysis/                        # Dataset profiling & sanity checks
        ├── analyze_data_for_report.py
        └── analyze_model_readiness.py
```

---

## Installation & Setup

All commands below should be executed from within the `code/` directory:

```bash
cd code
pip install -r requirements.txt
```

*(Optional) If you plan to re-run the scrapers requiring browser automation:*
```bash
playwright install
# Chrome driver is handled automatically via webdriver-manager
```

---

## Execution Guide

### 1. Model Training & Evaluation
To train baseline and ensemble models (Logistic Regression, Random Forest, XGBoost) using 5-fold cross-validation and evaluate on a held-out test set:

```bash
python src/modeling/run_classification_training.py
```
* **Input**: `Courses_Classification_Ready.json` (or `data/Courses_Final_Model_Ready.json`)
* **Outputs**:
  - `best_classification_model.pkl`: Serialized top-performing classifier.
  - `model_evaluation_report.txt`: Precision, recall, and F1 scores across classes.
  - `模型训练图片结果/confusion_matrix.png`: Test set confusion matrix visualization.

### 2. Exploratory Data Visualization
To regenerate summary statistics and distribution charts:

```bash
python src/visualization/create_visualizations.py
```
* **Input**: `data/AllCourses_Enhanced.json`
* **Output**: Generated PNG figures in `visualizations/`.

### 3. Feature Engineering Pipeline (Optional)
If you wish to recompute the engineered features from the filtered dataset:

```bash
python src/data_processing/run_feature_engineering.py
```
* **Input**: `data/Courses_Only_Dataset.json`
* **Output**: `data/Courses_Engineered_Features.json`

For advanced linguistic and keyword features:
```bash
python src/data_processing/run_advanced_feature_engineering.py
```

### 4. Data Collection (Optional)
The scrapers used to harvest the raw dataset are provided for reproducibility:
* **GraphQL Batch Harvest**: `python src/data_collection/coursera_batch_scraper.py`
* **Incremental Selenium Scraper**: `python src/data_collection/incremental_scraper.py`
* **Playwright Scraper**: `python src/data_collection/coursera_playwright_scraper.py`
