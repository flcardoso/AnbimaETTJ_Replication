"""
Data fetcher module for Brazilian government bond data.

This module fetches publicly available bond data from Anbima and other sources.
Since Anbima requires authentication for direct API access, we'll use publicly
available market data as a fallback or simulation.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import os
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ANBIMA ETTJ API endpoint
ANBIMA_ETTJ_URL = "https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/curvas-juros"


def fetch_anbima_ettj_api(ref_date: Optional[str] = None) -> Optional[dict]:
    """
    Helper function to fetch ETTJ data from ANBIMA's public API.
    
    Calls the ANBIMA public ETTJ endpoint and returns the parsed JSON response.
    Uses only standard library (urllib.request + json).
    
    Parameters
    ----------
    ref_date : str, optional
        Reference date in YYYY-MM-DD format. If provided, will be sent as a query parameter.
        If None, the API will return data for the latest available date.
    
    Returns
    -------
    dict or None
        Parsed JSON response from the API, or None if the request fails or returns no data.
        
    Raises
    ------
    URLError, HTTPError
        Network-related errors are logged and re-raised.
    """
    try:
        # Build URL with optional date parameter
        url = ANBIMA_ETTJ_URL
        if ref_date:
            url = f"{url}?data_referencia={ref_date}"
        
        logger.info(f"Fetching ETTJ data from ANBIMA API: {url}")
        
        # Create request (no authentication headers for now as per requirements)
        request = Request(url)
        request.add_header('User-Agent', 'Python-urllib/AnbimaETTJ-Replication')
        
        # Perform HTTP GET request
        with urlopen(request, timeout=30) as response:
            if response.status == 200:
                data = response.read()
                # Parse JSON response
                json_data = json.loads(data.decode('utf-8'))
                logger.info(f"Successfully fetched ETTJ data from ANBIMA API")
                return json_data
            else:
                logger.warning(f"ANBIMA API returned status {response.status}")
                return None
                
    except HTTPError as e:
        logger.error(f"HTTP error fetching ETTJ data: {e.code} - {e.reason}")
        raise
    except URLError as e:
        logger.error(f"URL error fetching ETTJ data: {e.reason}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching ETTJ data: {e}")
        raise


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

    def fetch_ettj_for_date(self, ref_date: date) -> List[Dict]:
        """
        Fetch ANBIMA ETTJ zero-coupon curves for a specific date.
        
        Retrieves nominal (pre-fixado), IPCA-linked (real), and implicit (breakeven)
        curves from ANBIMA's public API for the given reference date.
        
        Parameters
        ----------
        ref_date : date
            Reference date to fetch ETTJ data for.
        
        Returns
        -------
        list of dict
            List of dictionaries, one per vertex, containing:
            - date: reference date (date object)
            - du: business days to maturity (int)
            - nominal: pre-fixed rate (float, percent)
            - real: IPCA-linked rate (float, percent)
            - breakeven: implicit inflation rate (float, percent)
            
            Returns empty list if no data available for the date or if request fails.
        
        Examples
        --------
        >>> fetcher = BondDataFetcher()
        >>> data = fetcher.fetch_ettj_for_date(date(2024, 11, 14))
        >>> # Returns: [{'date': date(2024,11,14), 'du': 21, 'nominal': 11.5, 'real': 6.2, 'breakeven': 5.0}, ...]
        """
        # Convert date to string format expected by API
        date_str = ref_date.strftime('%Y-%m-%d')
        
        try:
            # Call the helper function to fetch from API
            api_response = fetch_anbima_ettj_api(date_str)
            
            # Handle case where API returns None or no data
            if not api_response:
                self.logger.warning(f"No ETTJ data returned from API for {date_str}")
                return []
            
            # Parse the API response and extract curve data
            result = []
            
            # The actual API structure may vary, so we need to handle different formats
            # Based on typical ANBIMA API structure, we expect something like:
            # { "data_referencia": "YYYY-MM-DD", "curvas": [...] }
            # or { "curvas_juros": [...] }
            
            curves_data = None
            if isinstance(api_response, dict):
                # Try different possible keys
                curves_data = (
                    api_response.get('curvas') or 
                    api_response.get('curvas_juros') or
                    api_response.get('data') or
                    []
                )
            elif isinstance(api_response, list):
                curves_data = api_response
            
            if not curves_data:
                self.logger.warning(f"No curve data found in API response for {date_str}")
                return []
            
            # Process each vertex in the curves
            for item in curves_data:
                try:
                    # Extract vertex data
                    # Typical fields: vertice_du, taxa_prefixadas, taxa_ipca, taxa_implicita
                    vertex_entry = {
                        'date': ref_date,
                        'du': item.get('vertice_du') or item.get('du') or item.get('prazo_du'),
                        'nominal': item.get('taxa_prefixadas') or item.get('taxa_nominal') or item.get('taxa_pre'),
                        'real': item.get('taxa_ipca') or item.get('taxa_real'),
                        'breakeven': item.get('taxa_implicita') or item.get('taxa_breakeven')
                    }
                    
                    # Only add if we have at least DU and one rate
                    if vertex_entry['du'] is not None and any([
                        vertex_entry['nominal'] is not None,
                        vertex_entry['real'] is not None,
                        vertex_entry['breakeven'] is not None
                    ]):
                        result.append(vertex_entry)
                    
                except (KeyError, TypeError) as e:
                    self.logger.warning(f"Error parsing vertex data: {e}")
                    continue
            
            if result:
                self.logger.info(f"Successfully parsed {len(result)} ETTJ vertices for {date_str}")
            else:
                self.logger.warning(f"No valid vertices found in API response for {date_str}")
                
            return result
            
        except (URLError, HTTPError) as e:
            # Network errors - log and return empty list
            self.logger.error(f"Network error fetching ETTJ for {date_str}: {e}")
            return []
        except Exception as e:
            # Unexpected errors - log and return empty list
            self.logger.error(f"Unexpected error fetching ETTJ for {date_str}: {e}")
            return []

    def download_tesouro_csv(self,dest_path: str | Path = "data/precotaxatesourodireto.csv") -> Path:
        """
        Download the Tesouro Direto historical prices/rates CSV and save it locally.

        Parameters
        ----------
        dest_path : str or Path
            Where to save the file (relative to repo root). Folder is created if needed.

        Returns
        -------
        Path
            The full path to the downloaded file.
        """
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Downloading Tesouro Direto CSV to {dest_path} ...")
        with urlopen(self.TD_URL) as resp, open(dest_path, "wb") as f:
            # stream bytes exactly as served (semicolon-separated, comma decimals)
            chunk = resp.read(8192)
            while chunk:
                f.write(chunk)
                chunk = resp.read(8192)

        print("Download completed.")
        return dest_path

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
