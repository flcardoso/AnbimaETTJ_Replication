# AnbimaETTJ_Replication - Implementation Summary

## Overview
This repository implements an automated daily pipeline for replicating the Anbima ETTJ (Estrutura a Termo de Taxa de Juros - Term Structure of Interest Rates) for Brazilian government bonds.

## What Was Implemented

### 1. Core Modules

#### Data Fetcher (`src/data_fetcher.py`)
- Fetches Brazilian government bond data
- Currently uses sample data structure
- Ready for integration with real data sources (Anbima API, B3, etc.)
- Handles both nominal (LTN/NTN-F) and inflation-linked (NTN-B) bonds

#### Yield Curve Model (`src/yield_curve_model.py`)
- Implements the Nelson-Siegel-Svensson (NSS) model
- NSS is the industry standard for yield curve fitting
- Uses sophisticated optimization:
  - Differential evolution for global optimization
  - L-BFGS-B for local refinement
- Calculates forward rates for any maturity

#### Pipeline (`src/pipeline.py`)
- Orchestrates the entire workflow
- Fits yield curves for both nominal and real bonds
- Generates all required outputs
- Handles CSV file management with deduplication

### 2. Output Files

The system generates four CSV files daily in the `output/` directory:

1. **nominal_yields.csv**
   - Date, tenor (in years), and nominal yield
   - Yields from LTN/NTN-F bonds
   
2. **inflation_linked_yields.csv**
   - Date, tenor (in years), and real yield
   - Yields from NTN-B bonds (inflation-indexed)
   
3. **breakeven_inflation.csv**
   - Date, tenor (in years), and implied inflation
   - Calculated as: Nominal Yield - Real Yield
   - Represents market's inflation expectations
   
4. **forward_rates.csv**
   - Date, tenor, nominal forward rate, and real forward rate
   - 3-month forward rates by default
   - Expected future interest rates

### 3. Automation

#### GitHub Actions Workflow (`.github/workflows/daily_update.yml`)
- Runs daily at 9:00 PM BRT (00:00 UTC)
- Can also be triggered manually
- Automatically commits and pushes results
- Proper security permissions configured

### 4. Configuration (`config.yaml`)
- Model parameters (initial guesses, bounds)
- Output tenors: 0.25, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30 years
- File paths and naming
- Schedule settings

### 5. Testing (`tests/test_yield_curve.py`)
- Unit tests for NSS model
- Tests for curve calculation, fitting, and prediction
- Tests for data fetching
- All tests pass successfully

### 6. Documentation
- Comprehensive README with:
  - Installation instructions
  - Usage examples
  - Methodology explanation
  - Project structure
  - References

## Technical Details

### Nelson-Siegel-Svensson Model

The NSS model fits yield curves with 6 parameters:

```
y(t) = β₀ + β₁[(1-e^(-t/τ₁))/(t/τ₁)] + 
       β₂[((1-e^(-t/τ₁))/(t/τ₁)) - e^(-t/τ₁)] + 
       β₃[((1-e^(-t/τ₂))/(t/τ₂)) - e^(-t/τ₂)]
```

**Parameters:**
- β₀: Long-term level (asymptotic yield)
- β₁: Short-term component (loading on short factor)
- β₂, β₃: Medium-term components (loading on medium factors)
- τ₁, τ₂: Decay factors (control curvature)

**Why NSS?**
- Used by central banks worldwide
- Flexible enough to capture various curve shapes
- Smooth interpolation between observed points
- Stable extrapolation for long maturities

### Data Flow

1. **Fetch** bond data (maturities and yields)
2. **Calculate** time to maturity for each bond
3. **Fit** NSS model to minimize sum of squared errors
4. **Generate** yields for standard tenors
5. **Calculate** derived metrics (breakeven, forwards)
6. **Save** to CSV files (with deduplication)

## Usage

### Manual Execution
```bash
cd src
python pipeline.py
```

### Automated Execution
- Runs automatically via GitHub Actions
- Daily at 9:00 PM BRT
- Results automatically committed to repository

### Customization
- Edit `config.yaml` to change tenors, model parameters, etc.
- Edit `.github/workflows/daily_update.yml` to change schedule

## Dependencies
- pandas >= 2.0.0
- numpy >= 1.24.0
- scipy >= 1.10.0 (optimization)
- requests >= 2.31.0
- python-dateutil >= 2.8.2
- pyyaml >= 6.0

## Security
- CodeQL security scanning: ✅ Passed
- Explicit workflow permissions set
- No secrets in code
- Output files excluded from git

## Next Steps for Production

To use this system in production:

1. **Integrate Real Data Sources**
   - Replace sample data in `data_fetcher.py`
   - Connect to Anbima API (requires subscription)
   - Or use B3 market data
   - Add error handling for data availability

2. **Add Data Validation**
   - Check for missing data
   - Validate yield ranges
   - Alert on anomalous values

3. **Enhance Model**
   - Add model diagnostics (R², residuals)
   - Implement alternative models (e.g., cubic splines)
   - Add model selection logic

4. **Monitoring**
   - Add logging to external service
   - Email/Slack notifications on failures
   - Dashboard for visualizing results

5. **Historical Backfill**
   - Fetch and process historical data
   - Build complete time series

## Files Created

```
.github/workflows/daily_update.yml  - GitHub Actions automation
.gitignore                          - Git ignore rules
config.yaml                         - Configuration settings
requirements.txt                    - Python dependencies
README.md                           - User documentation
src/__init__.py                     - Package initialization
src/data_fetcher.py                 - Bond data fetching
src/pipeline.py                     - Main orchestration
src/yield_curve_model.py            - NSS model implementation
tests/test_yield_curve.py           - Unit tests
```

## Testing Results

All tests pass:
- ✅ NSS curve calculation
- ✅ Model fitting and prediction
- ✅ Forward rate calculation
- ✅ Data fetching

## Security Check Results

CodeQL analysis:
- ✅ No security vulnerabilities found
- ✅ Proper workflow permissions configured
- ✅ No secrets exposed

## Sample Output

### Nominal Yields (2025-11-11)
- 1Y: 11.48%
- 5Y: 12.11%
- 10Y: 12.30%

### Real Yields (2025-11-11)
- 1Y: 5.55%
- 5Y: 6.00%
- 10Y: 6.20%

### Breakeven Inflation (2025-11-11)
- 1Y: 5.93%
- 5Y: 6.11%
- 10Y: 6.10%

(Note: These are from sample data for demonstration)

## References

1. Nelson, C. R., & Siegel, A. F. (1987). Parsimonious Modeling of Yield Curves. Journal of Business, 60(4), 473-489.

2. Svensson, L. E. (1994). Estimating and Interpreting Forward Interest Rates: Sweden 1992-1994. NBER Working Paper No. 4871.

3. Anbima - Brazilian Financial and Capital Markets Association
   Website: https://www.anbima.com.br
