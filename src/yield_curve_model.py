"""
Yield curve model implementation using Nelson-Siegel-Svensson (NSS) model.

The NSS model is widely used for fitting yield curves and is the standard
model used by many central banks, including for Brazilian government bonds.
"""

import numpy as np
from scipy.optimize import minimize, differential_evolution
from typing import List, Tuple, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NelsonSiegelSvensson:
    """
    Nelson-Siegel-Svensson yield curve model.
    
    The NSS model is defined as:
    y(t) = beta0 + beta1 * ((1 - exp(-t/tau1)) / (t/tau1)) +
           beta2 * (((1 - exp(-t/tau1)) / (t/tau1)) - exp(-t/tau1)) +
           beta3 * (((1 - exp(-t/tau2)) / (t/tau2)) - exp(-t/tau2))
    
    Where:
    - beta0: long-term interest rate level
    - beta1: short-term component
    - beta2: medium-term component
    - beta3: second medium-term component
    - tau1, tau2: decay factors
    """
    
    def __init__(self):
        """Initialize the NSS model."""
        self.params = None
        self.logger = logger
        
    @staticmethod
    def curve(t: np.ndarray, beta0: float, beta1: float, beta2: float, 
              beta3: float, tau1: float, tau2: float) -> np.ndarray:
        """
        Calculate yield curve using NSS formula.
        
        Args:
            t: Time to maturity (in years)
            beta0-beta3: NSS parameters
            tau1, tau2: Decay factors
            
        Returns:
            Yields for given maturities
        """
        # Avoid division by zero
        t = np.maximum(t, 1e-10)
        
        # Calculate components
        component1 = (1 - np.exp(-t/tau1)) / (t/tau1)
        component2 = component1 - np.exp(-t/tau1)
        component3 = (1 - np.exp(-t/tau2)) / (t/tau2) - np.exp(-t/tau2)
        
        return beta0 + beta1 * component1 + beta2 * component2 + beta3 * component3
    
    def fit(self, maturities: np.ndarray, yields: np.ndarray) -> Dict[str, float]:
        """
        Fit the NSS model to observed bond yields.
        
        Args:
            maturities: Time to maturity in years
            yields: Observed yields (in %)
            
        Returns:
            Dictionary of fitted parameters
        """
        self.logger.info(f"Fitting NSS model to {len(maturities)} data points")
        
        def objective(params):
            """Objective function to minimize (sum of squared errors)."""
            beta0, beta1, beta2, beta3, tau1, tau2 = params
            predicted = self.curve(maturities, beta0, beta1, beta2, beta3, tau1, tau2)
            return np.sum((yields - predicted) ** 2)
        
        # Parameter bounds
        bounds = [
            (-5, 30),    # beta0
            (-30, 30),   # beta1
            (-30, 30),   # beta2
            (-30, 30),   # beta3
            (0.1, 10),   # tau1
            (0.1, 10),   # tau2
        ]
        
        # Initial guess based on yield curve characteristics
        initial_guess = [
            np.mean(yields),          # beta0: average yield
            yields[0] - yields[-1],   # beta1: short-long spread
            0.0,                       # beta2
            0.0,                       # beta3
            1.0,                       # tau1
            5.0,                       # tau2
        ]
        
        # Use differential evolution for global optimization
        result = differential_evolution(
            objective, 
            bounds, 
            seed=42,
            maxiter=1000,
            atol=1e-7,
            tol=1e-7
        )
        
        # Refine with local optimization
        result_local = minimize(
            objective,
            result.x,
            method='L-BFGS-B',
            bounds=bounds
        )
        
        if result_local.success:
            self.params = {
                'beta0': result_local.x[0],
                'beta1': result_local.x[1],
                'beta2': result_local.x[2],
                'beta3': result_local.x[3],
                'tau1': result_local.x[4],
                'tau2': result_local.x[5],
            }
            self.logger.info(f"Model fitted successfully. RMSE: {np.sqrt(result_local.fun/len(maturities)):.4f}")
        else:
            self.logger.warning("Local optimization failed, using global result")
            self.params = {
                'beta0': result.x[0],
                'beta1': result.x[1],
                'beta2': result.x[2],
                'beta3': result.x[3],
                'tau1': result.x[4],
                'tau2': result.x[5],
            }
        
        return self.params
    
    def predict(self, maturities: np.ndarray) -> np.ndarray:
        """
        Predict yields for given maturities using fitted model.
        
        Args:
            maturities: Time to maturity in years
            
        Returns:
            Predicted yields
        """
        if self.params is None:
            raise ValueError("Model must be fitted before prediction")
        
        return self.curve(
            maturities,
            self.params['beta0'],
            self.params['beta1'],
            self.params['beta2'],
            self.params['beta3'],
            self.params['tau1'],
            self.params['tau2']
        )
    
    def forward_rate(self, maturity: float, horizon: float = 0.25) -> float:
        """
        Calculate forward rate at a given maturity.
        
        Args:
            maturity: Starting maturity in years
            horizon: Forward period in years (default 3 months)
            
        Returns:
            Forward rate
        """
        if self.params is None:
            raise ValueError("Model must be fitted before calculating forward rates")
        
        # Calculate spot rates
        y1 = self.predict(np.array([maturity]))[0]
        y2 = self.predict(np.array([maturity + horizon]))[0]
        
        # Calculate forward rate
        # f = ((1 + y2/100)**(maturity + horizon) / (1 + y1/100)**maturity)**(1/horizon) - 1
        forward = ((maturity + horizon) * y2 - maturity * y1) / horizon
        
        return forward
