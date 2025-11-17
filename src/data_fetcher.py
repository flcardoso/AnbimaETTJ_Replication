"""
Data fetcher module for ANBIMA ETTJ (zero-coupon curves).

This module fetches ANBIMA's official ETTJ zero-coupon curves from their public API.
Retrieves nominal (pre-fixado), IPCA-linked (real), and implicit (breakeven) curves.
"""

import pandas as pd
from datetime import date, timedelta, datetime
from typing import List, Dict, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import json
import logging
import os
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ANBIMA ETTJ API endpoint
ANBIMA_AUTH_URL = "https://api.anbima.com.br/oauth/access-token"
ANBIMA_ETTJ_URL = "https://api-sandbox.anbima.com.br/feed/precos-indices/v1/titulos-publicos/curvas-juros"

# Global token cache
_access_token = None
_token_expiry = None

def get_access_token() -> Optional[str]:
    """
    Get OAuth 2.0 access token from ANBIMA API.
    
    Uses client_id and client_secret from environment variables.
    Caches the token until it expires.
    
    Returns
    -------
    str or None
        Access token if successful, None otherwise.
    """
    global _access_token, _token_expiry
    
    # Check if we have a valid cached token
    if _access_token and _token_expiry:
        if datetime.now() < _token_expiry:
            logger.info("Using cached access token (expiry %s)", _token_expiry)
            return _access_token
    
    # Get credentials from environment
    client_id = os.environ.get('ANBIMA_CLIENT_ID')
    client_secret = os.environ.get('ANBIMA_CLIENT_SECRET')  # Note: SECRET, not API_KEY
    

    if not client_id or not client_secret:
        logger.error("ANBIMA_CLIENT_ID and ANBIMA_CLIENT_SECRET must be set in environment")
        return None
    
    try:
        # Prepare OAuth request body
        data = {
            'grant_type': 'client_credentials'
        }
        
        # Encode as JSON
        json_data = json.dumps(data).encode('utf-8')
        
        # Create Basic auth header
        auth_string = f'{client_id}:{client_secret}'
        b64_auth = base64.b64encode(auth_string.encode()).decode()
        
        # Create request
        request = Request(ANBIMA_AUTH_URL, data=json_data, method='POST')
        request.add_header('Content-Type', 'application/json')
        request.add_header('Authorization', f'Basic {b64_auth}')
        
        logger.info("Requesting new access token from ANBIMA")
        
        # Make request
        with urlopen(request, timeout=30) as response:
            if response.status in (200, 201):
                token_data = json.loads(response.read().decode('utf-8'))
                _access_token = token_data.get('access_token')
                
                # Calculate expiry (typically 3600 seconds, subtract buffer)
                expires_in = token_data.get('expires_in', 3600)
                _token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
                
                logger.info("Successfully obtained access token")
                return _access_token
            else:
                logger.error(f"Failed to get access token: HTTP {response.status}")
                return None
                
    except HTTPError as e:
        logger.error(f"HTTP error getting access token: {e.code} - {e.reason}")
        return None
    except Exception as e:
        logger.error(f"Error getting access token: {e}")
        return None

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
        # Get access token first
        access_token = get_access_token()
        if not access_token:
            logger.error("Cannot fetch ETTJ data: failed to obtain access token")
            return None
        
        # Build URL with optional date parameter
        url = ANBIMA_ETTJ_URL
        if ref_date:
            url = f"{url}?data_referencia={ref_date}"
        
        logger.info(f"Fetching ETTJ data from ANBIMA API: {url}")
        
        # Create request with authentication headers
        request = Request(url)
        request.add_header('User-Agent', 'Python-urllib/AnbimaETTJ-Replication')
        request.add_header('Authorization', f'Bearer {access_token}')
        request.add_header('client_id', os.environ.get('ANBIMA_CLIENT_ID'))
        request.add_header('access_token', access_token)
        
        # Perform HTTP GET request
        with urlopen(request, timeout=30) as response:
            if response.status in (200, 201):
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


class AnbimaETTJFetcher:
    """Fetches ANBIMA ETTJ zero-coupon curves."""

    def __init__(self):
        """Initialize the ANBIMA ETTJ fetcher."""
        self.logger = logger

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
        >>> fetcher = AnbimaETTJFetcher()
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
            
            # Extract the actual reference date from API response
            actual_date = ref_date  # Default to requested date
            curves_data = None
            
            if isinstance(api_response, dict):
                # Try to extract actual date from response
                date_from_response = api_response.get('data_referencia') or api_response.get('dataReferencia')
                if date_from_response:
                    try:
                        # Parse the date string to a date object
                        actual_date = datetime.strptime(date_from_response, '%Y-%m-%d').date()
                        if actual_date != ref_date:
                            self.logger.warning(
                                f"API returned data for {actual_date} instead of requested {ref_date}"
                            )
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Could not parse date from API response: {e}")
                
                # Try different possible keys for curves data
                curves_data = (
                    api_response.get('ettj') or
                    api_response.get('curvas') or 
                    api_response.get('curvas_juros') or
                    api_response.get('data') or
                    []
                )
            elif isinstance(api_response, list):
                # API returns list with single dict containing 'ettj' key
                if len(api_response) > 0 and isinstance(api_response[0], dict):
                    # Try to extract date from first item
                    first_item = api_response[0]
                    date_from_response = first_item.get('data_referencia') or first_item.get('dataReferencia')
                    if date_from_response:
                        try:
                            actual_date = datetime.strptime(date_from_response, '%Y-%m-%d').date()
                            if actual_date != ref_date:
                                self.logger.warning(
                                    f"API returned data for {actual_date} instead of requested {ref_date}"
                                )
                        except (ValueError, TypeError) as e:
                            self.logger.warning(f"Could not parse date from API response: {e}")
                    
                    curves_data = first_item.get('ettj', api_response)
                else:
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
                        'date': actual_date,  # Use actual date from API response
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
    
    def fetch_week_data(self, start_date: date, end_date: date) -> List[Dict]:
        """
        Fetch ETTJ data for a range of dates (typically a week).
        
        Only returns data for dates where ANBIMA has published data.
        Skips weekends and Brazilian holidays automatically.
        
        Parameters
        ----------
        start_date : date
            Start date of the range (inclusive).
        end_date : date
            End date of the range (inclusive).
        
        Returns
        -------
        list of dict
            Combined list of all vertex data for all valid dates in the range.
        """
        all_data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                daily_data = self.fetch_ettj_for_date(current_date)
                if daily_data:  # Only add if we got valid data
                    all_data.extend(daily_data)
            
            current_date += timedelta(days=1)
        
        return all_data

    def fetch_parameters_for_date(self, ref_date: date) -> List[Dict]:
        """Fetch NSS curve parameters (Nelson-Siegel-Svensson) for a specific date."""
        date_str = ref_date.strftime('%Y-%m-%d')
        try:
            api_response = fetch_anbima_ettj_api(date_str)
            if not api_response:
                self.logger.warning(f"No parameter data returned from API for {date_str}")
                return []
            
            # Extract the actual reference date from API response
            actual_date = ref_date  # Default to requested date
            parametros_list = []
            
            if isinstance(api_response, list) and api_response:
                first = api_response[0]
                if isinstance(first, dict):
                    # Try to extract date from response
                    date_from_response = first.get('data_referencia') or first.get('dataReferencia')
                    if date_from_response:
                        try:
                            actual_date = datetime.strptime(date_from_response, '%Y-%m-%d').date()
                            if actual_date != ref_date:
                                self.logger.warning(
                                    f"API returned parameters for {actual_date} instead of requested {ref_date}"
                                )
                        except (ValueError, TypeError) as e:
                            self.logger.warning(f"Could not parse date from API response: {e}")
                    
                    parametros_list = first.get('parametros', []) or []
            elif isinstance(api_response, dict):
                # Try to extract date from response
                date_from_response = api_response.get('data_referencia') or api_response.get('dataReferencia')
                if date_from_response:
                    try:
                        actual_date = datetime.strptime(date_from_response, '%Y-%m-%d').date()
                        if actual_date != ref_date:
                            self.logger.warning(
                                f"API returned parameters for {actual_date} instead of requested {ref_date}"
                            )
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Could not parse date from API response: {e}")
                
                parametros_list = api_response.get('parametros', []) or []
            
            if not parametros_list:
                self.logger.warning(f"No NSS parameters found in API response for {date_str}")
                return []
            
            result=[]
            for p in parametros_list:
                try:
                    entry={
                        'date': actual_date,  # Use actual date from API response
                        'grupo_indexador': p.get('grupo_indexador'),
                        'b1': p.get('b1'),
                        'b2': p.get('b2'),
                        'b3': p.get('b3'),
                        'b4': p.get('b4'),
                        'l1': p.get('l1'),
                        'l2': p.get('l2')
                    }
                    if entry['grupo_indexador'] and entry['b1'] is not None:
                        result.append(entry)
                except Exception as e:
                    self.logger.warning(f"Error parsing parameter block: {e}")
            if result:
                self.logger.info(f"Parsed {len(result)} NSS parameter sets for {date_str}")
            return result
        except (URLError, HTTPError) as e:
            self.logger.error(f"Network error fetching parameters for {date_str}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching parameters for {date_str}: {e}")
            return []

    def fetch_parameters_week(self, start_date: date, end_date: date) -> List[Dict]:
        """Fetch NSS parameters for each business day in the given date range."""
        all_params=[]
        current_date=start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:
                daily=self.fetch_parameters_for_date(current_date)
                if daily:
                    all_params.extend(daily)
            current_date += timedelta(days=1)
        return all_params

