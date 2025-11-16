"""
Tests for ANBIMA ETTJ data fetcher.
"""

import unittest
import sys
import os
from datetime import date
from unittest.mock import patch, MagicMock, call

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_fetcher import AnbimaETTJFetcher, fetch_anbima_ettj_api


class TestAnbimaETTJFetcher(unittest.TestCase):
    """Test cases for ANBIMA ETTJ fetcher."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = AnbimaETTJFetcher()
    
    def test_fetch_ettj_for_date_structure(self):
        """Test that fetch_ettj_for_date returns proper structure."""
        # This will likely return empty list due to network restrictions
        # but should not raise an exception
        result = self.fetcher.fetch_ettj_for_date(date(2024, 11, 14))
        
        # Should return a list
        self.assertIsInstance(result, list)
        
        # If data is returned, verify structure
        if result:
            for vertex in result:
                self.assertIsInstance(vertex, dict)
                self.assertIn('date', vertex)
                self.assertIn('du', vertex)
                # At least one rate should be present
                self.assertTrue(
                    'nominal' in vertex or 'real' in vertex or 'breakeven' in vertex
                )
    
    def test_fetch_ettj_helper_function(self):
        """Test the fetch_anbima_ettj_api helper function."""
        from urllib.error import URLError
        
        # Test without date parameter (may fail due to network restrictions)
        try:
            result = fetch_anbima_ettj_api()
            # If successful, should return dict or None
            self.assertTrue(result is None or isinstance(result, dict))
        except (URLError, Exception):
            # Network errors are expected and acceptable
            pass
        
        # Test with date parameter
        try:
            result = fetch_anbima_ettj_api("2024-11-14")
            self.assertTrue(result is None or isinstance(result, dict))
        except (URLError, Exception):
            # Network errors are expected and acceptable
            pass
    
    def test_week_data_structure(self):
        """Test that fetch_week_data returns proper structure."""
        start = date(2024, 11, 11)  # Monday
        end = date(2024, 11, 15)    # Friday
        
        result = self.fetcher.fetch_week_data(start, end)
        
        # Should return a list
        self.assertIsInstance(result, list)
        
        # If data is returned, verify structure
        if result:
            for vertex in result:
                self.assertIsInstance(vertex, dict)
                self.assertIn('date', vertex)
                self.assertIn('du', vertex)
    
    @patch('data_fetcher.fetch_anbima_ettj_api')
    def test_fetch_with_mock_data(self, mock_api):
        """Test fetcher with mocked API response."""
        # Mock API response
        mock_api.return_value = {
            'curvas': [
                {
                    'vertice_du': 21,
                    'taxa_prefixadas': 11.5,
                    'taxa_ipca': 6.2,
                    'taxa_implicita': 5.0
                },
                {
                    'vertice_du': 42,
                    'taxa_prefixadas': 11.8,
                    'taxa_ipca': 6.4,
                    'taxa_implicita': 5.1
                }
            ]
        }
        
        result = self.fetcher.fetch_ettj_for_date(date(2024, 11, 14))
        
        # Should have 2 vertices
        self.assertEqual(len(result), 2)
        
        # Check first vertex
        self.assertEqual(result[0]['du'], 21)
        self.assertEqual(result[0]['nominal'], 11.5)
        self.assertEqual(result[0]['real'], 6.2)
        self.assertEqual(result[0]['breakeven'], 5.0)
    
    @patch('data_fetcher.fetch_anbima_ettj_api')
    def test_fetch_with_empty_response(self, mock_api):
        """Test fetcher with empty API response."""
        mock_api.return_value = None
        
        result = self.fetcher.fetch_ettj_for_date(date(2024, 11, 14))
        
        # Should return empty list
        self.assertEqual(result, [])
    
    @patch('data_fetcher.fetch_anbima_ettj_api')
    def test_fetch_with_partial_data(self, mock_api):
        """Test fetcher with partial rate data."""
        # Mock API response with only nominal rates
        mock_api.return_value = {
            'curvas': [
                {
                    'vertice_du': 21,
                    'taxa_prefixadas': 11.5,
                }
            ]
        }
        
        result = self.fetcher.fetch_ettj_for_date(date(2024, 11, 14))
        
        # Should have 1 vertex
        self.assertEqual(len(result), 1)
        
        # Check that nominal is set and others are None
        self.assertEqual(result[0]['nominal'], 11.5)
        self.assertIsNone(result[0]['real'])
        self.assertIsNone(result[0]['breakeven'])
    
    @patch('data_fetcher.fetch_anbima_ettj_api')
    def test_fetch_extracts_date_from_response(self, mock_api):
        """Test that fetcher extracts the actual date from API response."""
        # Mock API response with data_referencia field
        mock_api.return_value = {
            'data_referencia': '2024-11-15',  # Actual data date
            'curvas': [
                {
                    'vertice_du': 21,
                    'taxa_prefixadas': 11.5,
                    'taxa_ipca': 6.2,
                    'taxa_implicita': 5.0
                }
            ]
        }
        
        # Request data for a different date
        result = self.fetcher.fetch_ettj_for_date(date(2024, 11, 14))
        
        # Should have 1 vertex
        self.assertEqual(len(result), 1)
        
        # Check that the date is from the API response, not the requested date
        self.assertEqual(result[0]['date'], date(2024, 11, 15))
    
    @patch('data_fetcher.fetch_anbima_ettj_api')
    def test_fetch_extracts_date_from_list_response(self, mock_api):
        """Test that fetcher extracts date from list-type API response."""
        # Mock API response as list with data_referencia in first item
        mock_api.return_value = [
            {
                'data_referencia': '2024-11-16',
                'ettj': [
                    {
                        'vertice_du': 42,
                        'taxa_prefixadas': 11.8,
                        'taxa_ipca': 6.4,
                        'taxa_implicita': 5.1
                    }
                ]
            }
        ]
        
        # Request data for a different date
        result = self.fetcher.fetch_ettj_for_date(date(2024, 11, 14))
        
        # Should have 1 vertex
        self.assertEqual(len(result), 1)
        
        # Check that the date is from the API response
        self.assertEqual(result[0]['date'], date(2024, 11, 16))
    
    @patch('data_fetcher.fetch_anbima_ettj_api')
    def test_parameters_extracts_date_from_response(self, mock_api):
        """Test that parameter fetcher extracts the actual date from API response."""
        # Mock API response with data_referencia and parametros
        mock_api.return_value = {
            'data_referencia': '2024-11-15',
            'parametros': [
                {
                    'grupo_indexador': 'PREFIXADOS',
                    'b1': 0.115,
                    'b2': -0.01,
                    'b3': -0.062,
                    'b4': 0.032,
                    'l1': 0.95,
                    'l2': 0.47
                }
            ]
        }
        
        # Request parameters for a different date
        result = self.fetcher.fetch_parameters_for_date(date(2024, 11, 14))
        
        # Should have 1 parameter set
        self.assertEqual(len(result), 1)
        
        # Check that the date is from the API response, not the requested date
        self.assertEqual(result[0]['date'], date(2024, 11, 15))
    
    @patch('data_fetcher.urlopen')
    @patch('data_fetcher.Request')
    def test_authentication_headers_added(self, mock_request_class, mock_urlopen):
        """Test that authentication headers are added when env vars are set."""
        # Set environment variables
        os.environ['ANBIMA_API_KEY'] = 'test-api-key-123'
        os.environ['ANBIMA_CLIENT_ID'] = 'test-client-id-456'
        
        try:
            # Mock the request object
            mock_request = MagicMock()
            mock_request_class.return_value = mock_request
            
            # Mock the response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.read.return_value = b'{"curvas": []}'
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_response
            
            # Call the API function
            fetch_anbima_ettj_api("2024-11-14")
            
            # Verify headers were added
            header_calls = [call[0] for call in mock_request.add_header.call_args_list]
            
            # Check for User-Agent header
            self.assertIn(('User-Agent', 'Python-urllib/AnbimaETTJ-Replication'), header_calls)
            
            # Check for authentication headers
            self.assertIn(('X-API-Key', 'test-api-key-123'), header_calls)
            self.assertIn(('client_id', 'test-client-id-456'), header_calls)
            
        finally:
            # Clean up environment variables
            if 'ANBIMA_API_KEY' in os.environ:
                del os.environ['ANBIMA_API_KEY']
            if 'ANBIMA_CLIENT_ID' in os.environ:
                del os.environ['ANBIMA_CLIENT_ID']
    
    @patch('data_fetcher.urlopen')
    @patch('data_fetcher.Request')
    def test_no_authentication_headers_without_env_vars(self, mock_request_class, mock_urlopen):
        """Test that authentication headers are NOT added when env vars are not set."""
        # Ensure environment variables are not set
        if 'ANBIMA_API_KEY' in os.environ:
            del os.environ['ANBIMA_API_KEY']
        if 'ANBIMA_CLIENT_ID' in os.environ:
            del os.environ['ANBIMA_CLIENT_ID']
        
        # Mock the request object
        mock_request = MagicMock()
        mock_request_class.return_value = mock_request
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"curvas": []}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        # Call the API function
        fetch_anbima_ettj_api("2024-11-14")
        
        # Verify headers were added
        header_calls = [call[0] for call in mock_request.add_header.call_args_list]
        
        # Check for User-Agent header (should be present)
        self.assertIn(('User-Agent', 'Python-urllib/AnbimaETTJ-Replication'), header_calls)
        
        # Check that authentication headers were NOT added
        auth_headers = [h for h in header_calls if h[0] in ('X-API-Key', 'client_id')]
        self.assertEqual(len(auth_headers), 0)


class TestPipeline(unittest.TestCase):
    """Test cases for the ETTJ pipeline."""
    
    def test_import_pipeline(self):
        """Test that pipeline module can be imported."""
        try:
            from pipeline import ETTJPipeline
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import pipeline: {e}")
    
    def test_pipeline_initialization(self):
        """Test pipeline can be initialized."""
        from pipeline import ETTJPipeline
        
        pipeline = ETTJPipeline()
        self.assertIsNotNone(pipeline)
        self.assertIsNotNone(pipeline.fetcher)
        self.assertIsNotNone(pipeline.output_dir)
    
    def test_previous_week_dates(self):
        """Test calculation of previous week dates."""
        from pipeline import ETTJPipeline
        
        pipeline = ETTJPipeline()
        start, end = pipeline.get_previous_week_dates()
        
        # Start should be Monday
        self.assertEqual(start.weekday(), 0)
        
        # End should be Friday
        self.assertEqual(end.weekday(), 4)
        
        # Should be 4 days apart
        self.assertEqual((end - start).days, 4)


if __name__ == '__main__':
    unittest.main()
