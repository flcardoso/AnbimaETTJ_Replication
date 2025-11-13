"""
Main pipeline for processing bond data and generating yield curves.
"""

import os
import yaml
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
import logging

from data_fetcher import BondDataFetcher
from yield_curve_model import NelsonSiegelSvensson

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YieldCurvePipeline:
    """Main pipeline for yield curve processing."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the pipeline.
        
        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            # Default to config.yaml in the repository root
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(os.path.dirname(script_dir), 'config.yaml')
        
        self.config = self._load_config(config_path)
        self.fetcher = BondDataFetcher()
        self.logger = logger
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def run(self, date: datetime = None) -> Dict[str, pd.DataFrame]:
        """
        Run the full pipeline for a given date.
        
        Args:
            date: Date to process (defaults to today)
            
        Returns:
            Dictionary of output DataFrames
        """
        if date is None:
            date = datetime.now()
        
        self.logger.info(f"Running pipeline for {date.strftime('%Y-%m-%d')}")
        
        # Step 1: Fetch bond data
        bond_data = self.fetcher.fetch_market_data(date)
        
        # Step 2: Fit yield curves
        nominal_curve = self._fit_nominal_curve(bond_data['nominal'], date)
        inflation_curve = self._fit_inflation_curve(bond_data['inflation_linked'], date)
        
        # Step 3: Generate outputs
        tenors = self.config['model']['tenors']
        
        nominal_yields_df = self._generate_yields(nominal_curve, tenors, date, 'nominal')
        inflation_yields_df = self._generate_yields(inflation_curve, tenors, date, 'inflation_linked')
        breakeven_df = self._calculate_breakeven(nominal_yields_df, inflation_yields_df, date)
        forward_rates_df = self._calculate_forward_rates(nominal_curve, inflation_curve, tenors, date)
        
        # Step 4: Save outputs
        output_dir = self.config['output']['directory']
        os.makedirs(output_dir, exist_ok=True)
        
        outputs = {
            'nominal_yields': nominal_yields_df,
            'inflation_linked_yields': inflation_yields_df,
            'breakeven_inflation': breakeven_df,
            'forward_rates': forward_rates_df
        }
        
        self._save_outputs(outputs, output_dir)
        
        return outputs
    
    def _fit_nominal_curve(self, bond_data: pd.DataFrame, date: datetime) -> NelsonSiegelSvensson:
        """Fit yield curve to nominal bond data."""
        self.logger.info("Fitting nominal yield curve")
        
        # Calculate time to maturity in years
        maturities = (bond_data['maturity_date'] - date).dt.days / 365.25
        yields = bond_data['yield'].values
        
        model = NelsonSiegelSvensson()
        model.fit(maturities.values, yields)
        
        return model
    
    def _fit_inflation_curve(self, bond_data: pd.DataFrame, date: datetime) -> NelsonSiegelSvensson:
        """Fit yield curve to inflation-linked bond data."""
        self.logger.info("Fitting inflation-linked yield curve")
        
        # Calculate time to maturity in years
        maturities = (bond_data['maturity_date'] - date).dt.days / 365.25
        yields = bond_data['real_yield'].values
        
        model = NelsonSiegelSvensson()
        model.fit(maturities.values, yields)
        
        return model
    
    def _generate_yields(self, model: NelsonSiegelSvensson, tenors: List[float], 
                        date: datetime, curve_type: str) -> pd.DataFrame:
        """
        Generate yield curve for specified tenors.
        
        Args:
            model: Fitted NSS model
            tenors: List of tenors in years
            date: Reference date
            curve_type: Type of curve ('nominal' or 'inflation_linked')
            
        Returns:
            DataFrame with yields for each tenor
        """
        tenors_array = np.array(tenors)
        yields = model.predict(tenors_array)
        
        df = pd.DataFrame({
            'date': date.strftime('%Y-%m-%d'),
            'tenor_years': tenors,
            'yield': yields
        })
        
        return df
    
    def _calculate_breakeven(self, nominal_df: pd.DataFrame, 
                            inflation_df: pd.DataFrame, date: datetime) -> pd.DataFrame:
        """
        Calculate breakeven inflation rates.
        
        Breakeven inflation = Nominal yield - Real yield
        
        Args:
            nominal_df: Nominal yields DataFrame
            inflation_df: Inflation-linked yields DataFrame
            date: Reference date
            
        Returns:
            DataFrame with breakeven inflation rates
        """
        self.logger.info("Calculating breakeven inflation rates")
        
        # Merge on tenor
        merged = nominal_df.merge(
            inflation_df, 
            on='tenor_years', 
            suffixes=('_nominal', '_inflation')
        )
        
        df = pd.DataFrame({
            'date': date.strftime('%Y-%m-%d'),
            'tenor_years': merged['tenor_years'],
            'breakeven_inflation': merged['yield_nominal'] - merged['yield_inflation']
        })
        
        return df
    
    def _calculate_forward_rates(self, nominal_model: NelsonSiegelSvensson,
                                 inflation_model: NelsonSiegelSvensson,
                                 tenors: List[float], date: datetime) -> pd.DataFrame:
        """
        Calculate forward rates for both nominal and inflation-linked curves.
        
        Args:
            nominal_model: Fitted nominal NSS model
            inflation_model: Fitted inflation-linked NSS model
            tenors: List of tenors in years
            date: Reference date
            
        Returns:
            DataFrame with forward rates
        """
        self.logger.info("Calculating forward rates")
        
        forward_data = []
        
        for tenor in tenors:
            if tenor >= 0.25:  # Need at least 3 months
                nominal_forward = nominal_model.forward_rate(tenor, horizon=0.25)
                inflation_forward = inflation_model.forward_rate(tenor, horizon=0.25)
                
                forward_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'tenor_years': tenor,
                    'nominal_forward': nominal_forward,
                    'inflation_forward': inflation_forward
                })
        
        return pd.DataFrame(forward_data)
    
    def _save_outputs(self, outputs: Dict[str, pd.DataFrame], output_dir: str):
        """Save output DataFrames to CSV files."""
        # Make output_dir absolute relative to repository root
        if not os.path.isabs(output_dir):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(os.path.dirname(script_dir), output_dir)
        
        self.logger.info(f"Saving outputs to {output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        file_mapping = self.config['output']['files']
        
        for key, df in outputs.items():
            filename = file_mapping[key]
            filepath = os.path.join(output_dir, filename)
            
            # Append to existing file or create new one
            if os.path.exists(filepath):
                existing_df = pd.read_csv(filepath)
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                # Remove duplicates based on date and tenor
                if 'tenor_years' in combined_df.columns:
                    combined_df = combined_df.drop_duplicates(subset=['date', 'tenor_years'], keep='last')
                else:
                    combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
                combined_df.to_csv(filepath, index=False)
            else:
                df.to_csv(filepath, index=False)
            
            self.logger.info(f"Saved {key} to {filename}")


def main():
    """Main entry point."""
    logger.info("Starting Anbima ETTJ Replication pipeline")
    
    pipeline = YieldCurvePipeline()
    results = pipeline.run()
    
    logger.info("Pipeline completed successfully")
    logger.info(f"Generated outputs: {list(results.keys())}")


if __name__ == '__main__':
    main()
