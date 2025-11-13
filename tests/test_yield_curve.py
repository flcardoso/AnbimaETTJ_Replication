"""
Tests for the yield curve model.
"""

import unittest
import numpy as np
import sys
import os
from data_fetcher import BondDataFetcher

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from yield_curve_model import NelsonSiegelSvensson


class TestNelsonSiegelSvensson(unittest.TestCase):
    """Test cases for NSS model."""
    
    

    def setUp(self):
        """Set up test fixtures."""
        self.model = NelsonSiegelSvensson()
    
    def test_curve_calculation(self):
        """Test NSS curve calculation."""
        # Test with known parameters
        t = np.array([1.0, 2.0, 5.0, 10.0])
        beta0, beta1, beta2, beta3 = 10.0, -2.0, 1.0, 0.5
        tau1, tau2 = 1.0, 5.0
        
        yields = self.model.curve(t, beta0, beta1, beta2, beta3, tau1, tau2)
        
        # Check that yields are returned for all maturities
        self.assertEqual(len(yields), len(t))
        
        # Check that yields are reasonable (positive)
        self.assertTrue(np.all(yields > 0))
    
    def test_fit_and_predict(self):
        """Test model fitting and prediction."""
        # Create sample data
        maturities = np.array([0.25, 0.5, 1.0, 2.0, 5.0, 10.0])
        yields = np.array([10.0, 10.5, 11.0, 11.3, 11.8, 12.0])
        
        # Fit the model
        params = self.model.fit(maturities, yields)
        
        # Check that parameters are returned
        self.assertIn('beta0', params)
        self.assertIn('beta1', params)
        self.assertIn('tau1', params)
        
        # Predict yields
        predicted = self.model.predict(maturities)
        
        # Check prediction shape
        self.assertEqual(len(predicted), len(maturities))
        
        # Check that fit is reasonable (RMSE < 0.5%)
        rmse = np.sqrt(np.mean((yields - predicted) ** 2))
        self.assertLess(rmse, 0.5)
    
    def test_forward_rate(self):
        """Test forward rate calculation."""
        # Create and fit a simple model
        maturities = np.array([1.0, 2.0, 5.0, 10.0])
        yields = np.array([11.0, 11.3, 11.8, 12.0])
        
        self.model.fit(maturities, yields)
        
        # Calculate forward rate
        forward = self.model.forward_rate(1.0, horizon=0.25)
        
        # Check that forward rate is reasonable
        self.assertIsInstance(forward, (float, np.floating))
        self.assertGreater(forward, 0)
        self.assertLess(forward, 30)


class TestDataFetcher(unittest.TestCase):
    """Test cases for data fetcher."""
    
    def test_fetch_market_data(self):
        """Test fetching market data."""
        from data_fetcher import BondDataFetcher
        from datetime import datetime
        
        fetcher = BondDataFetcher()
        data = fetcher.fetch_market_data(datetime(2024, 1, 15))
        
        # Check that both data types are returned
        self.assertIn('nominal', data)
        self.assertIn('inflation_linked', data)
        
        # Check nominal data structure
        nominal = data['nominal']
        self.assertIn('maturity_date', nominal.columns)
        self.assertIn('yield', nominal.columns)
        self.assertGreater(len(nominal), 0)
        
        # Check inflation-linked data structure
        inflation = data['inflation_linked']
        self.assertIn('maturity_date', inflation.columns)
        self.assertIn('real_yield', inflation.columns)
        self.assertGreater(len(inflation), 0)


if __name__ == '__main__':
    unittest.main()
