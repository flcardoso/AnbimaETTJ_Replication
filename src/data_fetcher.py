"""
Data fetcher module for Brazilian government bond data.

This module fetches publicly available bond data from Anbima and other sources.
Since Anbima requires authentication for direct API access, we'll use publicly
available market data as a fallback or simulation.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BondDataFetcher:
    """Fetches Brazilian government bond data."""
    TD_URL = (
        "https://www.tesourotransparente.gov.br/ckan/"
        "dataset/df56aa42-484a-4a59-8184-7676580c81e3/"
        "resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/"
        "download/precotaxatesourodireto.csv"
    )  # precotaxatesourodireto.csv

    def __init__(self, cache_path: str | None = "data/precotaxatesourodireto.csv"):
        """Initialize the bond data fetcher."""
        self.logger = logger
        self.cache_path = cache_path
        self._raw_df = None

    def _load_td_raw(self):
        """Download (or load cached) Tesouro Direto CSV into a DataFrame."""
        if self._raw_df is not None:
            return self._raw_df

        if self.cache_path and os.path.exists(self.cache_path):
            df = pd.read_csv(self.cache_path, sep=";", decimal=",", encoding="latin1")
        else:
            df = pd.read_csv(self.TD_URL, sep=";", decimal=",", encoding="latin1")
            if self.cache_path:
                os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
                df.to_csv(self.cache_path, sep=";", index=False)

        self._raw_df = df
        return df
        
    def fetch_market_data(self, date: datetime = None) -> Dict[str, pd.DataFrame]:
        """
        Fetch bond market data for a given date.
        
        In a real implementation, this would fetch from Anbima or other data providers.
        For this implementation, we'll use simulated/sample data structure.
        
        Args:
            date: Date to fetch data for (defaults to today)
            
        Returns:
            Dictionary with 'nominal' and 'inflation_linked' DataFrames
        """
        if date is None:
            date = datetime.now()
            
        self.logger.info(f"Fetching bond data for {date.strftime('%Y-%m-%d')}")
        
        # In a real implementation, this would make API calls or web scraping
        # For now, we'll create sample data structure
        
        # Nominal bonds (LTN/NTN-F) - sample data
        nominal_data = self._get_sample_nominal_data(date)
        
        # Inflation-linked bonds (NTN-B) - sample data
        inflation_linked_data = self._get_sample_inflation_linked_data(date)
        
        return {
            'nominal': nominal_data,
            'inflation_linked': inflation_linked_data
        }
    
    def _get_sample_nominal_data(self, date: datetime) -> pd.DataFrame:
        """
        Generate sample nominal bond data.
        
        In production, this would be replaced with actual API calls.
        """
        # Sample maturities and yields for Brazilian government bonds
        maturities = [
            date + timedelta(days=90),   # 3 months
            date + timedelta(days=180),  # 6 months
            date + timedelta(days=365),  # 1 year
            date + timedelta(days=730),  # 2 years
            date + timedelta(days=1095), # 3 years
            date + timedelta(days=1825), # 5 years
            date + timedelta(days=3650), # 10 years
        ]
        
        # Sample yields (in %, typical range for Brazil)
        base_yield = 11.5
        yields = [
            base_yield - 0.5,  # 3m
            base_yield - 0.3,  # 6m
            base_yield,        # 1y
            base_yield + 0.2,  # 2y
            base_yield + 0.4,  # 3y
            base_yield + 0.6,  # 5y
            base_yield + 0.8,  # 10y
        ]
        
        return pd.DataFrame({
            'maturity_date': maturities,
            'yield': yields,
            'price': [100.0] * len(maturities),  # Par prices for simplicity
        })
    
    def _get_sample_inflation_linked_data(self, date: datetime) -> pd.DataFrame:
        """
        Generate sample inflation-linked bond data (NTN-B).
        
        In production, this would be replaced with actual API calls.
        """
        # Sample maturities for NTN-B
        maturities = [
            date + timedelta(days=730),  # 2 years
            date + timedelta(days=1825), # 5 years
            date + timedelta(days=3650), # 10 years
            date + timedelta(days=7300), # 20 years
        ]
        
        # Sample real yields (real rate + IPCA)
        base_real_yield = 6.0
        real_yields = [
            base_real_yield - 0.3,  # 2y
            base_real_yield,        # 5y
            base_real_yield + 0.2,  # 10y
            base_real_yield + 0.3,  # 20y
        ]
        
        return pd.DataFrame({
            'maturity_date': maturities,
            'real_yield': real_yields,
            'price': [100.0] * len(maturities),
        })
