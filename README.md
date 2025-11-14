# AnbimaETTJ_Replication

Automated weekly fetching of ANBIMA's official ETTJ (Estrutura a Termo de Taxa de Juros) zero-coupon curves for Brazilian government bonds.

## Overview

This repository fetches ANBIMA's official ETTJ zero-coupon curves from their public API and stores them in cumulative CSV files. The system runs automatically weekly on Mondays at 8:00 AM BRT, fetching data for the previous week (Monday-Friday) and storing only valid dates (skipping weekends and Brazilian holidays automatically).

The three curves retrieved are:
- **Nominal (Pre-fixado)** - Nominal interest rate curve
- **Real (IPCA)** - Real interest rate curve (inflation-indexed)
- **Breakeven (Implicit)** - Implied inflation expectations (difference between nominal and real)

## Features

- 🤖 **Automated weekly execution** via GitHub Actions (Mondays at 8:00 AM BRT)
- 📊 **Official ANBIMA ETTJ curves** - Zero-coupon curves from the authoritative source
- 📈 **Three curve types** - Nominal, Real (IPCA), and Breakeven inflation
- 💾 **Cumulative CSV storage** - Historical data accumulation with automatic deduplication
- 🗓️ **Smart date handling** - Only stores valid dates with actual data (no weekends/holidays)
- 🧪 **Testing script** - View downloaded data structure and content

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

This will fetch data for the previous week (Monday-Friday) and update the CSV files.

### Testing the API

To test the ANBIMA API and view what data is being downloaded:

```bash
python test_anbima_api.py
```

This script will:
- Test direct API calls for recent dates
- Display the raw JSON response from ANBIMA
- Show parsed data structure
- Test week data fetching

### Automated Execution

The pipeline runs automatically weekly on **Mondays at 8:00 AM BRT** (configured in `.github/workflows/daily_update.yml`). 

To modify the schedule, edit the cron expression in the workflow file:

```yaml
schedule:
  - cron: '0 11 * * 1'  # Mondays at 11:00 UTC (8:00 BRT)
```

### Configuration

Edit `config.yaml` to customize:

- API endpoint URL
- Output directory and file names
- Scheduling parameters

## Output Files

All outputs are saved in the `output/` directory as expanding CSV files:

1. **ettj_nominal.csv** - Nominal (pre-fixado) zero-coupon curve
   - Columns: date, du (business days), rate
   
2. **ettj_real.csv** - Real (IPCA-linked) zero-coupon curve
   - Columns: date, du (business days), rate
   
3. **ettj_breakeven.csv** - Breakeven (implicit) inflation curve
   - Columns: date, du (business days), rate

Each file is cumulative, with new data appended automatically and duplicates removed.

## Data Source

The data comes from ANBIMA's public API:
- **API Endpoint**: `https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/curvas-juros`
- **Data**: Official ETTJ zero-coupon curves published by ANBIMA
- **Update Frequency**: Daily (on business days)
- **Curve Types**: Nominal, IPCA-linked, and implicit (breakeven)

## Project Structure

```
AnbimaETTJ_Replication/
├── .github/
│   └── workflows/
│       └── daily_update.yml    # GitHub Actions workflow
├── src/
│   ├── __init__.py
│   ├── data_fetcher.py         # ANBIMA API data fetching
│   └── pipeline.py             # Main pipeline orchestration
├── output/                     # Generated CSV files (cumulative)
│   ├── ettj_nominal.csv
│   ├── ettj_real.csv
│   └── ettj_breakeven.csv
├── test_anbima_api.py          # Testing script to view API data
├── config.yaml                 # Configuration file
├── requirements.txt            # Python dependencies
└── README.md
```

## Dependencies

- pandas >= 2.0.0
- numpy >= 1.24.0
- scipy >= 1.10.0
- requests >= 2.31.0
- python-dateutil >= 2.8.2
- pyyaml >= 6.0

## How It Works

1. **Weekly Trigger**: GitHub Actions runs every Monday at 8:00 AM BRT
2. **Date Calculation**: Pipeline calculates the previous week's date range (Monday-Friday)
3. **Data Fetching**: For each weekday in the range:
   - Attempts to fetch ETTJ data from ANBIMA API
   - Skips weekends automatically
   - Skips dates with no data (e.g., Brazilian holidays)
4. **Data Storage**: Valid data is:
   - Parsed into structured format (date, du, rate)
   - Split into three files (nominal, real, breakeven)
   - Appended to existing CSV files
   - Deduplicated (same date + du combination)
   - Sorted by date and du

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

See LICENSE file for details.

## References

- [ANBIMA - Associação Brasileira das Entidades dos Mercados Financeiro e de Capitais](https://www.anbima.com.br)
- [ANBIMA ETTJ Documentation](https://www.anbima.com.br/pt_br/informar/curvas-de-juros.htm)
