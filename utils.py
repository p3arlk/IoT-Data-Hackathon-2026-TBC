"""
Utility functions for logging, validation, and helpers
"""
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import sys
import traceback

class Logger:
    """Simple logging utility"""
    
    def __init__(self, log_file=None):
        self.start_time = datetime.now()
        self.log_file = log_file
        
    def info(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
        
    def success(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"✅ [{timestamp}] {message}")
        
    def warning(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"⚠️  [{timestamp}] {message}")
        
    def error(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"❌ [{timestamp}] {message}")
        
    def section(self, title):
        print("\n" + "="*80)
        print(f"{title}")
        print("="*80)
        
    def execution_time(self):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        return f"Execution time: {duration:.2f} seconds"

def safe_read_csv(filepath, **kwargs):
    """Safely read CSV with error handling"""
    try:
        return pd.read_csv(filepath, **kwargs)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def safe_read_excel(filepath, **kwargs):
    """Safely read Excel with error handling"""
    try:
        return pd.read_excel(filepath, **kwargs)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def validate_district(df, district_col='District'):
    """Validate district names"""
    from config import HK_DISTRICTS
    
    if district_col in df.columns:
        invalid = df[~df[district_col].isin(HK_DISTRICTS)][district_col].unique()
        if len(invalid) > 0:
            print(f"Warning: Invalid district names: {invalid}")
    return df

def clean_numeric(series):
    """Convert series to numeric, coercing errors"""
    return pd.to_numeric(series, errors='coerce')

def save_output(df, filename, subdir=''):
    """Save dataframe to CSV"""
    from config import OUTPUT_DIR
    
    save_dir = OUTPUT_DIR / subdir
    save_dir.mkdir(exist_ok=True)
    
    filepath = save_dir / filename
    df.to_csv(filepath, index=False)
    return filepath