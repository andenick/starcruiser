# StarCruiser Employment Data Dictionary

**Version**: 1.0
**Last Updated**: November 22, 2025
**Purpose**: Comprehensive reference guide for all employment series and variables

---

## Overview

This data dictionary provides definitions, metadata, and usage notes for employment data series imported from public data sources. Use this reference when:
- Selecting series for analysis
- Understanding series definitions
- Interpreting results
- Combining data across sources
- Citing data in research

---

## Table of Contents

1. [BLS Series Definitions](#bls-series-definitions)
2. [FRED Series Definitions](#fred-series-definitions)
3. [ALFRED Vintage Structure](#alfred-vintage-structure)
4. [Philadelphia Fed Real-Time Data](#philadelphia-fed-real-time-data)
5. [Shaikh-Tonak Historical Tables](#shaikh-tonak-historical-tables)
6. [BEA NIPA Employment](#bea-nipa-employment)
7. [Census Employment Variables](#census-employment-variables)
8. [Common Codes and Classifications](#common-codes-and-classifications)
9. [Usage Notes and Caveats](#usage-notes-and-caveats)

---

## BLS Series Definitions

### Series ID Structure

BLS series IDs follow standardized patterns. Example: **CES0000000001**
- CE: Survey prefix (Current Employment Statistics)
- S: Seasonal adjustment (S = Seasonally Adjusted, U = Not Adjusted)
- Industry code: 0000000 (All industries)
- Data type: 001 (All employees, in thousands)

### Key Employment Series

#### Unemployment and Labor Force (LN Prefix - Labor Force Statistics)

**LNS14000000** - Unemployment Rate
- **Definition**: Unemployed persons as percent of civilian labor force
- **Unit**: Percent
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Coverage**: Ages 16+, civilian noninstitutional population
- **Source Survey**: Current Population Survey (CPS) - Household survey
- **Historical Range**: 1948-present
- **Notes**: Most widely-watched employment indicator

**LNS11300000** - Labor Force Participation Rate
- **Definition**: Civilian labor force as percent of civilian noninstitutional population
- **Unit**: Percent
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Coverage**: Ages 16+
- **Historical Range**: 1948-present
- **Notes**: Key indicator of labor market engagement

**LNS12300000** - Employment-Population Ratio
- **Definition**: Employed persons as percent of civilian noninstitutional population
- **Unit**: Percent
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Coverage**: Ages 16+
- **Historical Range**: 1948-present

#### Total Employment (CES Prefix - Current Employment Statistics)

**CES0000000001** - All Employees, Total Nonfarm
- **Definition**: Total employed in nonfarm establishments
- **Unit**: Thousands of persons
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Coverage**: All nonfarm industries
- **Source Survey**: Current Employment Statistics (CES) - Establishment survey
- **Historical Range**: 1939-present
- **Notes**: "Headline" jobs number, most reported employment statistic

#### Industry Employment (CES Series)

**CES2000000001** - All Employees, Construction
- **Definition**: Total employed in construction industry
- **Unit**: Thousands of persons
- **NAICS**: 23 (Construction)
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Historical Range**: 1939-present

**CES3000000001** - All Employees, Manufacturing
- **Definition**: Total employed in manufacturing
- **Unit**: Thousands of persons
- **NAICS**: 31-33 (Manufacturing)
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Historical Range**: 1939-present
- **Notes**: Key cyclical indicator

**CES4000000001** - All Employees, Trade, Transportation, and Utilities
- **Definition**: Total employed in trade, transportation, and utilities
- **Unit**: Thousands of persons
- **NAICS**: 42, 44-45, 48-49, 22
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Historical Range**: 1939-present

**CES5000000001** - All Employees, Information
- **Definition**: Total employed in information sector
- **Unit**: Thousands of persons
- **NAICS**: 51 (Information)
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Historical Range**: 1990-present
- **Notes**: Newer industry classification

**CES6000000001** - All Employees, Professional and Business Services
- **Definition**: Total employed in professional and business services
- **Unit**: Thousands of persons
- **NAICS**: 54, 55, 56
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Historical Range**: 1939-present

**CES7000000001** - All Employees, Education and Health Services
- **Definition**: Total employed in education and health services
- **Unit**: Thousands of persons
- **NAICS**: 61, 62
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Historical Range**: 1939-present

**CES8000000001** - All Employees, Leisure and Hospitality
- **Definition**: Total employed in leisure and hospitality
- **Unit**: Thousands of persons
- **NAICS**: 71, 72 (Arts, entertainment, recreation, accommodation, food services)
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Historical Range**: 1939-present

### BLS Survey Methodologies

#### Current Employment Statistics (CES) - Establishment Survey
- **What**: Monthly survey of ~144,000 businesses and government agencies
- **Coverage**: Nonfarm employment, hours, earnings
- **Unit of Measurement**: Jobs (one person with two jobs counted twice)
- **Sample Size**: ~629,000 worksites
- **Response Rate**: ~62%
- **Revisions**: Preliminary → Revised → Final (benchmarked to QCEW annually)

#### Current Population Survey (CPS) - Household Survey
- **What**: Monthly survey of ~60,000 households
- **Coverage**: Labor force status, demographics
- **Unit of Measurement**: Persons (one person with two jobs counted once)
- **Sample Size**: ~110,000 individuals
- **Response Rate**: ~82%
- **Administered by**: Census Bureau for BLS

**Key Difference**: CES counts jobs, CPS counts people

---

## FRED Series Definitions

FRED series are curated by Federal Reserve Bank of St. Louis, primarily sourcing from BLS but also other agencies.

### Employment Series in StarCruiser FRED Data

**UNRATE** - Unemployment Rate
- **Source**: BLS (CPS)
- **Equivalent BLS Series**: LNS14000000
- **Unit**: Percent
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Historical Range**: 1948-present

**PAYEMS** - All Employees, Total Nonfarm
- **Source**: BLS (CES)
- **Equivalent BLS Series**: CES0000000001
- **Unit**: Thousands of persons
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Historical Range**: 1939-present

**CIVPART** - Civilian Labor Force Participation Rate
- **Source**: BLS (CPS)
- **Equivalent BLS Series**: LNS11300000
- **Unit**: Percent
- **Seasonal Adjustment**: Seasonally Adjusted
- **Frequency**: Monthly
- **Historical Range**: 1948-present

### FRED Data Advantages
- Unified API access to multiple sources
- Consistent data format across series
- Easy access to metadata
- Built-in data transformations (changes, growth rates)
- Widely used in research and policy

---

## ALFRED Vintage Structure

ALFRED (Archival FRED) tracks how employment data changes over time as revisions occur.

### Data Structure

Each observation has:
- **series_id**: FRED series identifier (e.g., UNRATE, PAYEMS)
- **date**: The period the data refers to (e.g., 2020-03-01 for March 2020)
- **value**: The employment value for that period
- **realtime_start**: When this vintage first became available
- **realtime_end**: When this vintage was superseded by a revision

### Example

```
series_id | date       | value | realtime_start | realtime_end
----------|------------|-------|----------------|-------------
PAYEMS    | 2020-03-01 | 152.5 | 2020-04-03     | 2020-05-01
PAYEMS    | 2020-03-01 | 152.3 | 2020-05-01     | 2021-02-05
PAYEMS    | 2020-03-01 | 152.4 | 2021-02-05     | 9999-12-31
```

**Interpretation**:
- Initial estimate (April 3, 2020): 152.5M jobs in March 2020
- First revision (May 1, 2020): Revised down to 152.3M
- Second revision (Feb 5, 2021): Revised up to 152.4M
- Final value (as of data collection): 152.4M

### Uses of Vintage Data

1. **Revision Analysis**: How much do employment numbers change?
2. **Real-Time Economics**: What did policymakers see at the time?
3. **Forecast Evaluation**: Compare forecasts to data available then vs now
4. **Data Reliability**: Which series revised most/least?

### Vintage Counts

StarCruiser ALFRED data contains **508,393 vintage observations**, meaning 508,393 individual (series, date, vintage) combinations across all employment series from 1939-present.

---

## Philadelphia Fed Real-Time Data

### File Structure

Three vintages types for EMPLOY series:

#### 1. First/Second/Third Releases
**File**: `EMPLOY_first_second_third.xlsx`

- **First**: Initial release value
- **Second**: First revision
- **Third**: Second revision (or final if no further revisions)

Enables comparison of:
- Initial vs revised employment data
- Revision magnitude
- Revision direction (up or down)

#### 2. Monthly Vintages
**File**: `EMPLOY_monthly_vintages.xlsx`

Each column represents data as it appeared on a specific month.
- Captures monthly snapshots of entire employment series
- Shows how historical data changes each month
- Enables "as of" analysis (what did series look like in June 2020?)

#### 3. Quarterly Vintages
**File**: `EMPLOY_quarterly_vintages.xlsx`

Each column represents data as it appeared on a specific quarter.
- Less frequent snapshots than monthly
- Sufficient for quarterly analysis
- Smaller file size

### Use Cases

1. **Policy Analysis**: What data did Federal Reserve see when making decisions?
2. **Nowcasting**: Compare real-time estimates to final values
3. **Revision Patterns**: Systematic revision biases?
4. **Economic History**: How did employment picture evolve?

---

## Shaikh-Tonak Historical Tables

### Background

Extracted from BLS historical publications (1964-1990) as part of Shaikh-Tonak research on productive vs unproductive labor.

### Table Structure

**File Naming**: `table_p[PAGE]_camelot[page]_[TABLE_NUM].csv`
- PAGE: Page number in original BLS publication
- TABLE_NUM: Table number on that page (0, 1, 2...)

### Special Classifications

#### Productive vs Unproductive Labor

Shaikh-Tonak framework distinguishes:
- **Productive Labor**: Produces commodities for sale (manufacturing, agriculture, mining, construction, transportation)
- **Unproductive Labor**: Facilitates circulation and distribution (retail trade, finance, real estate, advertising, management)

This classification differs from standard NAICS and enables analysis of:
- Value production vs value circulation
- Structural economic change
- Labor allocation patterns

### Industry Details

Tables contain employment breakdowns for:
- **Manufacturing**: Durable vs nondurable goods, detailed industries
- **Services**: Financial, business, personal services
- **Production Workers**: Vs non-production workers
- **Private Sector**: Detailed industry employment

### Temporal Coverage

- **Range**: 1964-1990 (monthly)
- **Frequency**: Monthly
- **Unit**: Thousands of persons
- **Geographic**: National

### Data Quality Notes

- Extraction quality: ~95% (some OCR challenges from scanned PDFs)
- Original source: Official BLS publications
- Verification: Cross-checked against BLS archives where possible

---

## BEA NIPA Employment

### National Income and Product Accounts (NIPA)

BEA integrates employment data within national accounts framework.

### Key Tables

#### T10101 - GDP by Major Industry
- **Employment Metric**: Full-time and part-time employees by industry
- **Unit**: Thousands of persons
- **Frequency**: Annual (A), Quarterly (Q)
- **Coverage**: All industries in GDP accounts

#### T10102 - Employment by Industry (Annual)
- **Employment Metric**: Full-time equivalent (FTE) employees
- **Unit**: Thousands of FTE jobs
- **Frequency**: Annual
- **Historical Range**: 1929-present
- **Detail**: Detailed industry breakdown (NAICS)

#### T10103 - FTE Employees by Industry
- **Employment Metric**: Full-time equivalent standardization
- **Unit**: Thousands of FTE jobs
- **Frequency**: Annual (A), Quarterly (Q)
- **Purpose**: Standardize part-time to FTE for productivity analysis

### Full-Time Equivalent (FTE)

**Definition**: Conversion of part-time jobs to full-time equivalents
- 2 half-time jobs = 1 FTE job
- Enables consistent productivity calculations
- Used in GDP per worker calculations

**Conversion**:
```
FTE = (Full-time jobs × 1.0) + (Part-time jobs × part-time factor)
```
Part-time factor varies by industry (typically 0.4-0.6)

### BEA vs BLS Employment

**BEA**:
- FTE employees
- Integrated with GDP accounts
- Industry employment as share of value added
- Includes self-employed (in some tables)

**BLS**:
- Headcount employees
- Pure labor market statistics
- Detailed industry breakdowns
- Excludes self-employed (in CES)

---

## Census Employment Variables

### American Community Survey (ACS)

#### Employment Status Variables

**ESR** - Employment Status Recode
- 1: Employed, at work
- 2: Employed, with job but not at work
- 3: Unemployed
- 4: Armed forces, at work
- 5: Armed forces, with job but not at work
- 6: Not in labor force

#### Industry Variables

**NAICSP** - NAICS Industry Recode (Person)
- 2-digit: Major sectors (11-99)
- 3-digit: Subsectors
- 4-digit: Industry groups
- 6-digit: Detailed industries (where available)

**Example NAICS Codes**:
- 11: Agriculture, Forestry, Fishing
- 23: Construction
- 31-33: Manufacturing
- 42: Wholesale Trade
- 44-45: Retail Trade
- 54: Professional, Scientific, Technical Services
- 61: Educational Services
- 62: Health Care and Social Assistance

#### Occupation Variables

**SOCP** - SOC Occupation Code (Person)
- 2-digit: Major groups (11-53)
- 3-digit: Minor groups
- 4-digit: Broad occupations
- 6-digit: Detailed occupations

**Example SOC Codes**:
- 11: Management Occupations
- 15: Computer and Mathematical Occupations
- 25: Education, Training, and Library Occupations
- 29: Healthcare Practitioners and Technical Occupations
- 41: Sales and Related Occupations
- 43: Office and Administrative Support Occupations

#### Geographic Variables

**COUNTY** - County FIPS Code
- 5-digit code: State (2) + County (3)
- Example: 36061 = New York County (Manhattan), NY

**PUMA** - Public Use Microdata Area
- Geographic unit for ACS microdata
- ~100,000+ population areas
- Nested within states

**METAREA** - Metropolitan Statistical Area
- OMB-defined metro areas
- Based on commuting patterns
- Updated periodically

### County Business Patterns (CBP)

#### Establishment Employment

**EMP** - Mid-March Employment
- **Definition**: Number of employees during pay period including March 12
- **Unit**: Persons
- **Coverage**: Establishments with payroll
- **Excludes**: Self-employed, agricultural workers, most government

**PAYANN** - Annual Payroll
- **Unit**: Thousands of dollars
- **Purpose**: Employment cost measure
- **Use**: Calculate average wage per employee

**ESTAB** - Number of Establishments
- **Definition**: Single physical location with economic activity
- **Unit**: Count
- **Use**: Business density, establishment size distribution

---

## Common Codes and Classifications

### NAICS (North American Industry Classification System)

**2-Digit Sectors** (Broad Industries):
- 11: Agriculture, Forestry, Fishing and Hunting
- 21: Mining, Quarrying, and Oil and Gas Extraction
- 22: Utilities
- 23: Construction
- 31-33: Manufacturing
- 42: Wholesale Trade
- 44-45: Retail Trade
- 48-49: Transportation and Warehousing
- 51: Information
- 52: Finance and Insurance
- 53: Real Estate and Rental and Leasing
- 54: Professional, Scientific, and Technical Services
- 55: Management of Companies and Enterprises
- 56: Administrative and Support and Waste Management Services
- 61: Educational Services
- 62: Health Care and Social Assistance
- 71: Arts, Entertainment, and Recreation
- 72: Accommodation and Food Services
- 81: Other Services (except Public Administration)
- 92: Public Administration

**NAICS Versions**:
- 1997, 2002, 2007, 2012, 2017, 2022
- Industries reclassified periodically
- Bridge tables available for continuity

### SOC (Standard Occupational Classification)

**2-Digit Major Groups**:
- 11-13: Management, Business, Financial Occupations
- 15, 17, 19: Computer, Math, Architecture, Engineering, Science
- 21: Community and Social Service Occupations
- 23: Legal Occupations
- 25: Education, Training, and Library Occupations
- 27: Arts, Design, Entertainment, Sports, Media Occupations
- 29: Healthcare Practitioners and Technical Occupations
- 31: Healthcare Support Occupations
- 33: Protective Service Occupations
- 35: Food Preparation and Serving Occupations
- 37: Building and Grounds Cleaning and Maintenance
- 39: Personal Care and Service Occupations
- 41: Sales and Related Occupations
- 43: Office and Administrative Support Occupations
- 45: Farming, Fishing, and Forestry Occupations
- 47: Construction and Extraction Occupations
- 49: Installation, Maintenance, and Repair Occupations
- 51: Production Occupations
- 53: Transportation and Material Moving Occupations

### Geographic Codes

#### FIPS (Federal Information Processing Standards)

**State FIPS** (2 digits):
- 01: Alabama
- 06: California
- 36: New York
- 48: Texas
- (Full list: 01-56 for states and DC)

**County FIPS** (5 digits): State (2) + County (3)
- 36061: New York County (Manhattan), NY
- 06037: Los Angeles County, CA
- 48201: Harris County (Houston), TX

### Seasonal Adjustment Codes

- **S**: Seasonally Adjusted
- **U**: Not Seasonally Adjusted (Unadjusted)

**When to use**:
- SA: Time series analysis, trend identification, month-to-month comparisons
- NSA: Year-over-year comparisons, comparing same month across years

---

## Usage Notes and Caveats

### Data Harmonization

#### Survey Differences

**CES (Establishment Survey) vs CPS (Household Survey)**:
- **CES counts jobs**, CPS counts people
- Person with 2 jobs: CES counts 2, CPS counts 1
- Different samples, different methodologies
- Can diverge in short run, converge long run
- Both valid, different purposes

**Recommendations**:
- Use CES for industry-level employment trends
- Use CPS for unemployment, labor force participation, demographics
- Don't directly compare levels between surveys
- Both useful for comprehensive labor market picture

#### Seasonal Adjustment

- Always check if series is SA or NSA
- Don't seasonally adjust an already-adjusted series
- SA appropriate for monthly changes
- NSA appropriate for year-over-year growth

#### Revisions

- Employment data revised regularly
- Use ALFRED/Philadelphia Fed to understand revision patterns
- Latest vintage typically most accurate
- But contemporaneous analysis requires real-time data
- Revisions can be substantial during economic turning points

### Data Gaps and Discontinuities

#### Industry Classification Changes

NAICS revised periodically (2002, 2007, 2012, 2017, 2022):
- Some industries reclassified
- Breaks in time series continuity
- BLS provides bridge tables and continuous series where possible

**Solutions**:
- Use BLS continuous series (created to span NAICS changes)
- Apply bridge tables for custom series
- Note discontinuities in analysis

#### Geographic Boundary Changes

Counties and MSAs redefined periodically:
- County mergers/splits (rare)
- MSA redefinitions (every decade)
- Can affect continuity of local area series

**Solutions**:
- Use Census geographic crosswalks
- Note boundary changes in analysis
- Consider broader geographic units for long-term analysis

#### Survey Redesigns

CPS redesigned periodically (major redesigns 1994, 2003):
- Methodology improvements
- Can cause level shifts
- BLS provides adjustment factors where possible

### Data Quality Indicators

#### Sample Size

Larger samples = more reliable:
- National: Highly reliable
- State: Generally reliable
- Metro: Reliable for large metros, less so for small
- County: Varies widely by county size

**Census ACS**:
- 1-year estimates: Large areas only (65,000+ population)
- 5-year estimates: All areas, more reliable for small areas

#### Margins of Error

- ACS provides margins of error (MOE)
- Check MOE before analyzing small geographies
- Large MOE = unreliable estimate

#### Revisions as Quality Signal

- Series with small revisions: More reliable real-time
- Series with large revisions: Less reliable real-time, but useful vintage data

---

## Common Analysis Patterns

### Labor Market Health

**Key Indicators**:
1. Unemployment Rate (UNRATE / LNS14000000)
2. Labor Force Participation (CIVPART / LNS11300000)
3. Total Employment (PAYEMS / CES0000000001)
4. Employment-Population Ratio (LNS12300000)

**Interpretation**:
- Falling unemployment + rising participation = strong labor market
- Falling unemployment + falling participation = potential discouraged workers
- Rising employment + rising population = check employment-population ratio

### Industry Employment Trends

**Use CES Industry Series**:
- Manufacturing (CES3000000001): Cyclical indicator
- Construction (CES2000000001): Leading indicator (sensitive to interest rates)
- Retail (CES4200000001): Consumer demand
- Professional Services (CES6000000001): High-wage job growth

**Analysis**:
- Month-over-month: Use SA data
- Year-over-year: Can use NSA or SA
- Industry share of total employment: Structural change

### Geographic Employment Analysis

**Census Data Best For**:
- County-level employment totals
- Local labor market analysis
- Demographic employment patterns
- Small area estimation

**Combine with BLS for**:
- State-level industry detail (from future BLS bulk download)
- Metro area monthly trends
- Real-time local unemployment

### Employment Revisions

**ALFRED/Philadelphia Fed for**:
- Magnitude of revisions by series
- Systematic revision bias?
- Forecast evaluation
- Real-time decision making

**Analysis**:
- Initial vs final: How wrong were initial estimates?
- Revision patterns: Do revisions cluster at turning points?
- Series reliability: Which series most/least revised?

---

## Data Update Schedule

### BLS
- **Release**: First Friday of month (for previous month)
- **Revisions**: Previous 2 months revised
- **Annual Benchmarks**: February each year (revises past 5 years)

### FRED/ALFRED
- **Update**: Shortly after BLS release
- **Vintages**: New vintage created with each release
- **Frequency**: Monthly for employment series

### Philadelphia Fed
- **Real-Time Data**: Updated monthly
- **Vintages**: Added to dataset as available

### BEA
- **Advance GDP**: ~1 month after quarter end (includes employment)
- **Revisions**: Second and third estimates (2nd and 3rd months)
- **Annual Revisions**: July each year
- **Comprehensive Revisions**: Every 5 years

### Census
- **ACS**: Released annually (September for previous year)
- **1-Year Estimates**: Large areas only
- **5-Year Estimates**: All areas (most current)

---

## Recommended Citation Format

When using StarCruiser employment data:

```
Bureau of Labor Statistics. (2025). [Series Name] [Data set].
U.S. Department of Labor. Retrieved [Date] from public data sources
at $DATA_ROOT/API_MODULES/BLS/
```

For combined analysis:
```
Employment data compiled from multiple sources including Bureau of Labor
Statistics, Federal Reserve Economic Data (FRED), Bureau of Economic Analysis,
and U.S. Census Bureau, accessed via public economic data sources
($DATA_ROOT/), [Date].
```

---

## Additional Resources

### BLS Documentation
- CES Technical Notes: https://www.bls.gov/ces/cesstn.htm
- CPS Technical Notes: https://www.bls.gov/cps/documentation.htm
- JOLTS Documentation: https://www.bls.gov/jlt/jltdef.htm

### FRED Resources
- FRED Help: https://fred.stlouisfed.org/docs/api/fred/
- ALFRED Documentation: https://alfred.stlouisfed.org/

### Census Documentation
- ACS Documentation: https://www.census.gov/programs-surveys/acs/technical-documentation.html
- CBP Methodology: https://www.census.gov/programs-surveys/cbp/technical-documentation/methodology.html

### Industry/Occupation Classification
- NAICS: https://www.census.gov/naics/
- SOC: https://www.bls.gov/soc/

---

**Last Updated**: November 22, 2025
**Version**: 1.0
**Maintainer**: StarCruiser Project
**Location**: Technical/DATA_DICTIONARY.md
