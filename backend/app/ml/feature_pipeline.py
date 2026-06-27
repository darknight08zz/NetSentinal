import pandas as pd
import numpy as np
import os
import json
import glob
from sklearn.model_selection import train_test_split

def load_cicids2017(raw_dir: str) -> tuple[pd.DataFrame, dict]:
    """
    Reads all CSVs in data/raw/cicids2017/, concatenates them, standardizes 
    column names, and cleans the data (handling NaN/Inf, duplicates).
    Returns the cleaned dataframe and missing value stats for EDA.
    """
    all_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    if not all_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")

    df_list = []
    for file in all_files:
        print(f"Loading {file}...")
        df_part = pd.read_csv(file)
        df_list.append(df_part)

    df = pd.concat(df_list, ignore_index=True)
    
    # Standardize column names
    df.columns = df.columns.str.strip()
    
    # Track missing values before cleaning
    # Replace infinite values with NaN so we can count them as missing/invalid
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    missing_counts = df.isna().sum().to_dict()
    missing_summary = {k: int(v) for k, v in missing_counts.items() if v > 0}
    
    print("Dropping NaN and infinite values...")
    df.dropna(inplace=True)
    
    print("Dropping exact duplicate rows...")
    df.drop_duplicates(inplace=True)

    # Convert object columns to numeric where possible, ignoring the label column
    label_col = 'Attack Type' if 'Attack Type' in df.columns else 'Label'
    numeric_cols = [c for c in df.columns if c != label_col]
    
    # Ensure they are numeric
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows that became NaN due to coercion
    df.dropna(inplace=True)

    print(f"Cleaned dataset shape: {df.shape}")
    return df, missing_summary

def load_nsl_kdd(raw_dir: str) -> pd.DataFrame:
    """
    Optional loader for NSL-KDD dataset. 
    """
    # Columns for NSL-KDD
    col_names = [
        "duration","protocol_type","service","flag","src_bytes",
        "dst_bytes","land","wrong_fragment","urgent","hot","num_failed_logins",
        "logged_in","num_compromised","root_shell","su_attempted","num_root",
        "num_file_creations","num_shells","num_access_files","num_outbound_cmds",
        "is_host_login","is_guest_login","count","srv_count","serror_rate",
        "srv_serror_rate","rerror_rate","srv_rerror_rate","same_srv_rate",
        "diff_srv_rate","srv_diff_host_rate","dst_host_count","dst_host_srv_count",
        "dst_host_same_srv_rate","dst_host_diff_srv_rate","dst_host_same_src_port_rate",
        "dst_host_srv_diff_host_rate","dst_host_serror_rate","dst_host_srv_serror_rate",
        "dst_host_rerror_rate","dst_host_srv_rerror_rate","label","difficulty"
    ]
    file_path = os.path.join(raw_dir, "KDDTrain+.txt")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"NSL-KDD file not found at {file_path}")
    
    df = pd.read_csv(file_path, header=None, names=col_names)
    return df

def get_benign_only(df: pd.DataFrame, label_col: str = 'Attack Type', benign_label: str = 'Normal Traffic') -> pd.DataFrame:
    """
    Filters the dataset to only include benign traffic.
    """
    return df[df[label_col] == benign_label].copy()

def generate_eda_summary(df: pd.DataFrame, missing_summary: dict, output_path: str):
    """
    Generates a short EDA summary and saves it as JSON.
    """
    label_col = 'Attack Type' if 'Attack Type' in df.columns else 'Label'
    benign_label = 'Normal Traffic' if label_col == 'Attack Type' else 'BENIGN'

    class_counts = df[label_col].value_counts().to_dict()
    total_samples = len(df)
    benign_samples = class_counts.get(benign_label, 0)
    attack_samples = total_samples - benign_samples
    
    imbalance_ratio = attack_samples / total_samples if total_samples > 0 else 0

    numeric_cols = [c for c in df.columns if c != label_col]
    
    # Compute min and max for features safely
    stats = df[numeric_cols].agg(['min', 'max']).to_dict()
    
    eda_data = {
        "class_distribution": {k: int(v) for k, v in class_counts.items()},
        "imbalance_ratio_percentage": round(imbalance_ratio * 100, 2),
        "missing_values_before_cleaning": missing_summary,
        "feature_ranges": stats
    }
    
    with open(output_path, 'w') as f:
        json.dump(eda_data, f, indent=4)
    print(f"EDA summary saved to {output_path}")
    print(f"Imbalance Ratio (Attacks): {eda_data['imbalance_ratio_percentage']}%")

if __name__ == "__main__":
    import pyarrow as pa
    import pyarrow.parquet as pq

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    PROJECT_ROOT = os.path.dirname(BASE_DIR)
    RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "cicids2017")
    PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # 1. Load and Clean
    df, missing_summary = load_cicids2017(RAW_DIR)
    
    # 2. EDA Summary
    eda_path = os.path.join(PROCESSED_DIR, "eda_summary.json")
    generate_eda_summary(df, missing_summary, eda_path)
    
    # 3. Train-Test Split (80/20 random split since no timestamp available)
    print("Splitting dataset into train (80%) and test (20%)...")
    train_df, test_df = train_test_split(df, test_size=0.20, random_state=42)
    
    # 4. Save to Parquet
    train_out = os.path.join(PROCESSED_DIR, "train.parquet")
    test_out = os.path.join(PROCESSED_DIR, "test.parquet")
    
    print(f"Saving train data to {train_out}...")
    train_df.to_parquet(train_out, engine='pyarrow', index=False)
    
    print(f"Saving test data to {test_out}...")
    test_df.to_parquet(test_out, engine='pyarrow', index=False)
    
    print("Feature Pipeline Phase 1 Complete!")
