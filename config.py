"""
Configuration settings for the entire project
"""
from pathlib import Path

# =============================================================================
# PATHS
# =============================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'outputs'
FORECAST_DIR = OUTPUT_DIR / 'forecasts'
VIZ_DIR = OUTPUT_DIR / 'visualizations'
REPORT_DIR = OUTPUT_DIR / 'reports'
CLEANED_DIR = OUTPUT_DIR / 'cleaned'
INSIGHTS_DIR = OUTPUT_DIR / 'insights'
RECOMMENDATIONS_DIR = OUTPUT_DIR / 'recommendations'

# Create directories
for dir_path in [OUTPUT_DIR, FORECAST_DIR, VIZ_DIR, REPORT_DIR, 
                 CLEANED_DIR, INSIGHTS_DIR, RECOMMENDATIONS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# =============================================================================
# DATA FILES - Use glob pattern to find files
# =============================================================================
POPULATION_DETAILED_FILE = DATA_DIR / 'Table 110-06811 _ Land-based non-institutional population by District Council district, sex and age.csv'
POPULATION_SUMMARY_FILE = DATA_DIR / 'Table 1.1 _ Land-based non-institutional population by District Council district and sex.csv'
POPULATION_AGE_FILE = DATA_DIR / 'Table 1.2 _ Proportion of land-based non-institutional population by District Council district and age.csv'

# Find death files with pattern matching
DEATH_FILES = {}
for year in [2020, 2021, 2022, 2023, 2024]:
    # Try different possible filenames
    possible_names = [
        DATA_DIR / f'Number of registered deaths by leading cause of death by sex by age group, {year}.csv',
        DATA_DIR / f'deaths_{year}.csv',
        DATA_DIR / f'Deaths_{year}.csv'
    ]
    for filepath in possible_names:
        if filepath.exists():
            DEATH_FILES[year] = filepath
            break

HOSPITAL_DISCHARGES_FILE = DATA_DIR / 'IPDPDD by disease group-en.xlsx'
HOSPITAL_BEDS_FILE = DATA_DIR / 'Table 930-92083 _ Medical institutions with hospital beds by area and type of institution.csv'

HOUSEHOLD_FILE = DATA_DIR / 'Table 3.1 _ Domestic households by District Council district and type of households.csv'
INCOME_FILE = DATA_DIR / 'Table 3.2 _ Median monthly household income by District Council district and type of households.csv'
LABOUR_FORCE_FILE = DATA_DIR / 'Table 210-06822 _ Labour force and labour force participation rate by District Council district, sex and age.csv'
# Additional tables used by the pipeline
HOUSING_TYPE_FILE = DATA_DIR / 'Table 130-06609A _ Domestic households by monthly household income and type of housing (excluding foreign domestic helpers).csv'
LABOUR_2_1_FILE = DATA_DIR / 'Table 2.1 _ Labour force by District Council district and sex.csv'
LABOUR_2_2_FILE = DATA_DIR / 'Table 2.2 _ Labour force participation rate by District Council district and sex.csv'

# =============================================================================
# MODEL PARAMETERS
# =============================================================================
FORECAST_YEARS = [2025, 2026, 2027, 2028, 2029, 2030]
HISTORICAL_YEARS = [2019, 2020, 2021, 2022, 2023, 2024]

# Equipment adoption rates (% of elderly population)
EQUIPMENT_ADOPTION_RATES = {
    'Mobility - Wheelchairs': 0.12,
    'Mobility - Walkers': 0.15,
    'Bathroom Safety': 0.18,
    'Beds & Transfer': 0.08,
    'Monitoring': 0.10,
    'Respiratory': 0.06,
    'Daily Living': 0.05,
    'Exercise': 0.04,
    'Cognitive Support': 0.07
}

# Annual adoption growth rate (5% per year)
ADOPTION_GROWTH_RATE = 0.05

# Pandemic multipliers (2020 pattern)
PANDEMIC_MULTIPLIERS = {
    'Respiratory': 3.5,
    'Monitoring': 2.8,
    'Cognitive Support': 1.8,
    'Mobility - Wheelchairs': 0.7,
    'Mobility - Walkers': 0.65,
    'Exercise': 1.9,
    'Bathroom Safety': 0.85,
    'Beds & Transfer': 1.2,
    'Daily Living': 1.1
}

# =============================================================================
# HONG KONG DISTRICTS
# =============================================================================
HK_DISTRICTS = [
    'Central and Western', 'Wan Chai', 'Eastern', 'Southern',
    'Yau Tsim Mong', 'Sham Shui Po', 'Kowloon City', 'Wong Tai Sin',
    'Kwun Tong', 'Kwai Tsing', 'Tsuen Wan', 'Tuen Mun',
    'Yuen Long', 'North', 'Tai Po', 'Sha Tin', 'Sai Kung', 'Islands'
]

# =============================================================================
# VISUALIZATION SETTINGS
# =============================================================================
PLOT_STYLE = 'seaborn-v0_8-whitegrid'
COLOR_PALETTE = 'husl'
FIGURE_DPI = 300