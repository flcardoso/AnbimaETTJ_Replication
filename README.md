# AnbimaETTJ_Replication

Automated daily replication of Brazilian government bond yield curves (ETTJ - Estrutura a Termo de Taxa de Juros).

## Overview

This repository fetches publicly available Brazilian government bond data and fits a Nelson-Siegel-Svensson (NSS) yield curve model to extract parameters. The system runs automatically at a specified time and generates CSV files containing:

- **Nominal yields** - Yields from nominal government bonds (LTN/NTN-F)
- **Inflation-linked yields** - Real yields from inflation-indexed bonds (NTN-B)
- **Breakeven inflation rates** - Implied inflation expectations
- **Forward rates** - Expected future interest rates for both nominal and real curves

## Features

- 🤖 **Automated daily execution** via GitHub Actions
- 📊 **Nelson-Siegel-Svensson model** for robust yield curve fitting
- 📈 **Multiple yield curve outputs** (nominal, real, breakeven, forwards)
- 💾 **CSV exports** with historical data accumulation
- 🔧 **Configurable** tenors and model parameters

## Installation

```bash
# Clone the repository
git clone https://github.com/flcardoso/AnbimaETTJ_Replication.git
cd AnbimaETTJ_Replication

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Manual Execution

Run the pipeline manually:

```bash
cd src
python pipeline.py
```

### Automated Execution

The pipeline runs automatically daily at 9:00 PM BRT (configured in `.github/workflows/daily_update.yml`). 

To modify the schedule, edit the cron expression in the workflow file:

```yaml
schedule:
  - cron: '0 0 * * *'  # Adjust as needed
```

### Configuration

Edit `config.yaml` to customize:

- Model parameters (initial guesses, bounds)
- Output tenors (e.g., 1Y, 5Y, 10Y)
- Output directory and file names
- Scheduling parameters

## Output Files

All outputs are saved in the `output/` directory:

1. **nominal_yields.csv** - Nominal yield curves
   - Columns: date, tenor_years, yield

2. **inflation_linked_yields.csv** - Real yield curves  
   - Columns: date, tenor_years, yield

3. **breakeven_inflation.csv** - Implied inflation expectations
   - Columns: date, tenor_years, breakeven_inflation

4. **forward_rates.csv** - Forward rates (3-month horizon)
   - Columns: date, tenor_years, nominal_forward, inflation_forward

## Methodology

### Nelson-Siegel-Svensson Model

The NSS model fits the yield curve with 6 parameters:

```
y(t) = β₀ + β₁[(1-e^(-t/τ₁))/(t/τ₁)] + β₂[((1-e^(-t/τ₁))/(t/τ₁)) - e^(-t/τ₁)] + β₃[((1-e^(-t/τ₂))/(t/τ₂)) - e^(-t/τ₂)]
```

Where:
- **β₀** - Long-term level
- **β₁** - Short-term component  
- **β₂, β₃** - Medium-term components
- **τ₁, τ₂** - Decay factors

### Data Sources

The current implementation uses sample data structure. For production use, integrate with:
- Anbima API (requires subscription)
- B3 (Brazilian stock exchange) market data
- Other financial data providers

## Project Structure

```
AnbimaETTJ_Replication/
├── .github/
│   └── workflows/
│       └── daily_update.yml    # GitHub Actions workflow
├── src/
│   ├── __init__.py
│   ├── data_fetcher.py         # Bond data fetching
│   ├── yield_curve_model.py    # NSS model implementation
│   └── pipeline.py             # Main pipeline orchestration
├── output/                     # Generated CSV files
├── config.yaml                 # Configuration file
├── requirements.txt            # Python dependencies
└── README.md
```

## Dependencies

- pandas >= 2.0.0
- numpy >= 1.24.0
- scipy >= 1.10.0 (for optimization)
- requests >= 2.31.0
- python-dateutil >= 2.8.2
- pyyaml

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

See LICENSE file for details.

## References

- [Anbima ETTJ Documentation](https://www.anbima.com.br)
- Nelson, C. R., & Siegel, A. F. (1987). Parsimonious Modeling of Yield Curves
- Svensson, L. E. (1994). Estimating and Interpreting Forward Interest Rates
