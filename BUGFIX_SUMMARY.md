# Fix for Duplicate Yields and Parameters Issue

## Problem
The repository was storing the same yields and parameters for all days of the week. When querying data for different dates (Monday-Friday), identical data was being stored with different dates, creating duplicates.

### Example of the Issue
Before the fix, the output files showed:
```csv
date,du,rate
2025-11-03,21,10.3884
2025-11-04,21,10.3884  <- Same rate as Nov 3
2025-11-05,21,10.3884  <- Same rate as Nov 3
2025-11-06,21,10.3884  <- Same rate as Nov 3
2025-11-07,21,10.3884  <- Same rate as Nov 3
```

All different dates had identical rates, suggesting they were actually the same data point stored multiple times.

## Root Cause
The code was using the **requested date** instead of the **actual data date** from the API response.

When the ANBIMA API was queried for dates without data (e.g., holidays), it would return the most recent available data. However, the code was tagging this data with the requested date instead of the actual date from the response's `data_referencia` field.

## Solution
Modified the data fetcher to:
1. Extract the `data_referencia` field from the API response
2. Use this actual date instead of the requested date
3. Log warnings when the API returns data for a different date than requested
4. Let the existing deduplication logic remove any duplicates

## How It Works Now

### Scenario: Requesting data for a week where only Monday has data

**Before the fix:**
```
Request Mon (2024-11-11) → Store with date 2024-11-11 ✓
Request Tue (2024-11-12) → Store with date 2024-11-12 ✗ (actually Mon data)
Request Wed (2024-11-13) → Store with date 2024-11-13 ✗ (actually Mon data)
Request Thu (2024-11-14) → Store with date 2024-11-14 ✗ (actually Mon data)
Request Fri (2024-11-15) → Store with date 2024-11-15 ✗ (actually Mon data)
Result: 5 records with identical data but different dates
```

**After the fix:**
```
Request Mon (2024-11-11) → API returns data_referencia=2024-11-11 → Store with date 2024-11-11 ✓
Request Tue (2024-11-12) → API returns data_referencia=2024-11-11 → Store with date 2024-11-11 ✓
Request Wed (2024-11-13) → API returns data_referencia=2024-11-11 → Store with date 2024-11-11 ✓
Request Thu (2024-11-14) → API returns data_referencia=2024-11-11 → Store with date 2024-11-11 ✓
Request Fri (2024-11-15) → API returns data_referencia=2024-11-11 → Store with date 2024-11-11 ✓
Deduplication: All have same (date, du) → Keep only 1 record ✓
Result: 1 record with correct date
```

## Changes Made

### 1. `src/data_fetcher.py`
- Modified `fetch_ettj_for_date()` to extract and use `data_referencia` from API response
- Modified `fetch_parameters_for_date()` to extract and use `data_referencia` from API response
- Added warning logs when API returns data for a different date than requested
- Handles both dict and list API response formats

### 2. `tests/test_ettj.py`
Added comprehensive tests:
- `test_fetch_extracts_date_from_response`: Validates date extraction from dict responses
- `test_fetch_extracts_date_from_list_response`: Validates date extraction from list responses
- `test_parameters_extracts_date_from_response`: Validates parameter date extraction
- `test_week_data_deduplicates_when_api_returns_same_date`: Validates full deduplication flow

## Testing
- All 4 new tests pass
- 10/12 existing tests pass (2 pre-existing failures unrelated to this fix)
- No security vulnerabilities found (CodeQL scan: 0 alerts)

## Impact
After this fix is deployed:
- No more duplicate data will be stored
- Existing duplicates can be removed by running the pipeline again (deduplication will clean them up)
- Users will see warnings in logs when API returns data for different dates than requested
- CSV files will accurately reflect the dates of the actual data

## Next Steps
The fix is complete and tested. When deployed via GitHub Actions:
1. The pipeline will fetch data for the previous week
2. If the API returns the same data for multiple dates, it will correctly identify them as the same date
3. Deduplication will automatically remove any duplicates
4. Only unique (date, du) combinations will be stored
