"""
Main pipeline for fetching ANBIMA ETTJ zero-coupon curves and storing them as CSV.

This pipeline:
1. Fetches ANBIMA's official ETTJ curves (nominal, IPCA, breakeven) for the previous week
2. Stores data in expanding CSV files (only for valid dates with actual data)
"""

import os
import pandas as pd
from datetime import date, timedelta
import logging

from data_fetcher import AnbimaETTJFetcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ETTJPipeline:
    """Main pipeline for ANBIMA ETTJ data fetching and storage."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the pipeline.
        
        Args:
            output_dir: Directory to save CSV files (default: 'output')
        """
        self.output_dir = output_dir
        self.fetcher = AnbimaETTJFetcher()
        self.logger = logger
        
        # Make output_dir absolute relative to repository root
        if not os.path.isabs(self.output_dir):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.output_dir = os.path.join(os.path.dirname(script_dir), self.output_dir)
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
    def get_previous_week_dates(self) -> tuple[date, date]:
        """
        Calculate the date range for the previous week (Monday-Friday).
        
        Returns:
            Tuple of (start_date, end_date) for the previous week
        """
        today = date.today()
        
        # Find the most recent Monday
        days_since_monday = today.weekday()  # Monday = 0, Sunday = 6
        if days_since_monday == 0:
            # If today is Monday, go back to last Monday
            last_monday = today - timedelta(days=7)
        else:
            # Go back to the most recent Monday
            last_monday = today - timedelta(days=days_since_monday)
        
        # Previous week is the week before last Monday
        previous_week_start = last_monday - timedelta(days=7)
        previous_week_end = previous_week_start + timedelta(days=4)  # Friday
        
        return previous_week_start, previous_week_end
    
    def run(self, start_date: date = None, end_date: date = None):
        """
        Run the pipeline to fetch and store ETTJ data.
        
        Args:
            start_date: Start date for data fetching (defaults to previous week Monday)
            end_date: End date for data fetching (defaults to previous week Friday)
        """
        # Use previous week dates if not specified
        if start_date is None or end_date is None:
            start_date, end_date = self.get_previous_week_dates()
        
        self.logger.info(f"Running ETTJ pipeline for {start_date} to {end_date}")
        
        # Fetch data for the date range
        data = self.fetcher.fetch_week_data(start_date, end_date)
        
        if not data:
            self.logger.warning("No data fetched from ANBIMA API")
            return
        
        self.logger.info(f"Fetched {len(data)} data points")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Save to CSV
        self._save_to_csv(df)
        
        self.logger.info("Pipeline completed successfully")
    
    def _save_to_csv(self, new_data: pd.DataFrame):
        """
        Save ETTJ data to expanding CSV files.
        
        Creates/updates three CSV files:
        - ettj_nominal.csv: Nominal (pre-fixado) rates
        - ettj_real.csv: Real (IPCA-linked) rates
        - ettj_breakeven.csv: Breakeven (implicit) inflation rates
        
        Args:
            new_data: DataFrame with columns: date, du, nominal, real, breakeven
        """
        # Define the three output files
        files = {
            'nominal': 'ettj_nominal.csv',
            'real': 'ettj_real.csv',
            'breakeven': 'ettj_breakeven.csv'
        }
        
        for rate_type, filename in files.items():
            filepath = os.path.join(self.output_dir, filename)
            
            # Filter data for this rate type (only rows where this rate is not None)
            rate_data = new_data[new_data[rate_type].notna()].copy()
            
            if rate_data.empty:
                self.logger.info(f"No {rate_type} data to save")
                continue
            
            # Prepare data for saving
            output_df = rate_data[['date', 'du', rate_type]].copy()
            output_df.columns = ['date', 'du', 'rate']
            
            # Convert date to string for CSV storage
            output_df['date'] = output_df['date'].astype(str)
            
            # Append to existing file or create new one
            if os.path.exists(filepath):
                existing_df = pd.read_csv(filepath)
                combined_df = pd.concat([existing_df, output_df], ignore_index=True)
                # Remove duplicates (same date and du)
                combined_df = combined_df.drop_duplicates(subset=['date', 'du'], keep='last')
                # Sort by date and du
                combined_df = combined_df.sort_values(['date', 'du']).reset_index(drop=True)
                combined_df.to_csv(filepath, index=False)
                self.logger.info(f"Updated {filename} with {len(output_df)} new records")
            else:
                output_df = output_df.sort_values(['date', 'du']).reset_index(drop=True)
                output_df.to_csv(filepath, index=False)
                self.logger.info(f"Created {filename} with {len(output_df)} records")


def main():
    """Main entry point."""
    logger.info("Starting ANBIMA ETTJ pipeline")
    
    pipeline = ETTJPipeline()
    pipeline.run()
    
    logger.info("Pipeline finished")


if __name__ == '__main__':
    main()
