"""
Data Loader Module
Downloads and processes A/B testing data from publicly available sources
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Tuple, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ABTestDataLoader:
    """Handles data loading and preprocessing for A/B testing"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def generate_synthetic_dark_mode_data(
        self,
        control_size: int = 5000,
        variant_size: int = 5000,
        session_duration_control_mean: float = 450,
        session_duration_variant_mean: float = 480,
        conversion_rate_control: float = 0.08,
        conversion_rate_variant: float = 0.085,
        seed: int = 42
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Generate synthetic A/B test data for Dark Mode experiment
        
        Simulates:
        - Session Duration (primary metric)
        - Conversion (secondary metric)
        
        Returns:
            DataFrame with experiment data and metadata dict
        """
        np.random.seed(seed)
        
        # Control group (Light Mode)
        control_data = {
            'user_id': np.arange(control_size),
            'variant': 'control',
            'session_duration': np.random.normal(
                session_duration_control_mean, 
                150, 
                control_size
            ),
            'converted': np.random.binomial(1, conversion_rate_control, control_size),
            'timestamp': pd.date_range('2024-01-01', periods=control_size, freq='1min')
        }
        
        # Variant group (Dark Mode)
        variant_data = {
            'user_id': np.arange(control_size, control_size + variant_size),
            'variant': 'variant',
            'session_duration': np.random.normal(
                session_duration_variant_mean, 
                150, 
                variant_size
            ),
            'converted': np.random.binomial(1, conversion_rate_variant, variant_size),
            'timestamp': pd.date_range('2024-01-01', periods=variant_size, freq='1min')
        }
        
        df_control = pd.DataFrame(control_data)
        df_variant = pd.DataFrame(variant_data)
        df = pd.concat([df_control, df_variant], ignore_index=True)
        
        # Ensure session_duration is positive
        df['session_duration'] = df['session_duration'].clip(lower=1)
        
        metadata = {
            'total_users': len(df),
            'control_users': control_size,
            'variant_users': variant_size,
            'primary_metric': 'session_duration',
            'secondary_metric': 'converted',
            'control_mean_session': df[df['variant'] == 'control']['session_duration'].mean(),
            'variant_mean_session': df[df['variant'] == 'variant']['session_duration'].mean(),
            'control_conversion': df[df['variant'] == 'control']['converted'].mean(),
            'variant_conversion': df[df['variant'] == 'variant']['converted'].mean(),
        }
        
        logger.info(f"Generated synthetic data: {metadata}")
        return df, metadata
    
    def load_cookie_cats_data(self) -> Tuple[pd.DataFrame, Dict]:
        """
        Load Cookie Cats A/B testing data from Kaggle
        https://www.kaggle.com/datasets/yufengsui/mobile-games-ab-testing-cookie-cats
        """
        file_path = self.data_dir / "cookie_cats.csv"
        
        if not file_path.exists():
            logger.warning(f"Cookie Cats data not found at {file_path}")
            logger.info("Using synthetic data instead...")
            return self.generate_synthetic_dark_mode_data()
        
        df = pd.read_csv(file_path)
        
        # Rename columns for consistency
        df.columns = df.columns.str.lower()
        
        metadata = {
            'source': 'Cookie Cats Kaggle',
            'total_users': len(df),
            'columns': list(df.columns)
        }
        
        return df, metadata
    
    def prepare_experiment_data(
        self,
        df: pd.DataFrame,
        primary_metric: str = 'session_duration',
        secondary_metric: str = 'converted',
        control_variant: str = 'control',
        treatment_variant: str = 'variant',
        remove_outliers: bool = True,
        outlier_method: str = 'iqr'
    ) -> Tuple[Dict, Dict]:
        """
        Prepare and clean experiment data
        
        Args:
            df: Raw experiment dataframe
            primary_metric: Column name for primary metric (e.g., session duration)
            secondary_metric: Column name for secondary metric (e.g., conversion)
            control_variant: Value in 'variant' column for control group
            treatment_variant: Value in 'variant' column for treatment group
            remove_outliers: Whether to remove outliers
            outlier_method: 'iqr' or 'zscore'
        
        Returns:
            Tuple of (control_data_dict, variant_data_dict)
        """
        
        # Split by variant
        control = df[df['variant'] == control_variant].copy()
        variant = df[df['variant'] == treatment_variant].copy()
        
        logger.info(f"Control group size: {len(control)}")
        logger.info(f"Variant group size: {len(variant)}")
        
        # Remove outliers if specified
        if remove_outliers:
            control = self._remove_outliers(
                control, 
                primary_metric, 
                method=outlier_method
            )
            variant = self._remove_outliers(
                variant, 
                primary_metric, 
                method=outlier_method
            )
            
            logger.info(f"After outlier removal:")
            logger.info(f"  Control: {len(control)} users")
            logger.info(f"  Variant: {len(variant)} users")
        
        # Prepare control data
        control_data = {
            'primary_metric': control[primary_metric].values,
            'secondary_metric': control[secondary_metric].values,
            'sample_size': len(control),
            'mean_primary': control[primary_metric].mean(),
            'std_primary': control[primary_metric].std(),
            'conversion_rate': control[secondary_metric].mean(),
        }
        
        # Prepare variant data
        variant_data = {
            'primary_metric': variant[primary_metric].values,
            'secondary_metric': variant[secondary_metric].values,
            'sample_size': len(variant),
            'mean_primary': variant[primary_metric].mean(),
            'std_primary': variant[primary_metric].std(),
            'conversion_rate': variant[secondary_metric].mean(),
        }
        
        return control_data, variant_data
    
    @staticmethod
    def _remove_outliers(
        data: pd.DataFrame, 
        column: str, 
        method: str = 'iqr',
        threshold: float = 3.0
    ) -> pd.DataFrame:
        """Remove outliers using IQR or Z-score method"""
        if method == 'iqr':
            Q1 = data[column].quantile(0.25)
            Q3 = data[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return data[(data[column] >= lower_bound) & (data[column] <= upper_bound)]
        
        elif method == 'zscore':
            z_scores = np.abs((data[column] - data[column].mean()) / data[column].std())
            return data[z_scores < threshold]
        
        return data


if __name__ == "__main__":
    loader = ABTestDataLoader()
    
    # Generate synthetic data
    df, metadata = loader.generate_synthetic_dark_mode_data()
    print("\n=== Synthetic Data Generated ===")
    print(f"Shape: {df.shape}")
    print(f"\nMetadata: {metadata}")
    print(f"\nFirst few rows:\n{df.head()}")
    
    # Prepare for analysis
    control, variant = loader.prepare_experiment_data(df)
    print("\n=== Prepared Control Group ===")
    print(f"Sample Size: {control['sample_size']}")
    print(f"Mean Session Duration: {control['mean_primary']:.2f}s")
    print(f"Conversion Rate: {control['conversion_rate']:.4f}")
    
    print("\n=== Prepared Variant Group ===")
    print(f"Sample Size: {variant['sample_size']}")
    print(f"Mean Session Duration: {variant['mean_primary']:.2f}s")
    print(f"Conversion Rate: {variant['conversion_rate']:.4f}")
