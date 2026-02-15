"""
STEP 2: Clean and transform all datasets
"""
import pandas as pd
import numpy as np
from config import *
from utils import Logger, clean_numeric, save_output

class DataCleaner:
    """Clean and standardise all datasets"""
    
    def __init__(self, raw_data):
        self.raw = raw_data
        self.cleaned = {}
        self.logger = Logger()
        
    def clean_all(self):
        """Execute all cleaning steps"""
        
        self.logger.section("STEP 2: CLEANING DATA")
        
        self.clean_population()
        self.clean_deaths()
        self.clean_hospital()
        self.clean_households()
        self.create_master_district()
        
        # Save cleaned data
        for name, df in self.cleaned.items():
            save_output(df, f'cleaned_{name}.csv', 'cleaned')
        
        self.logger.success("Data cleaning complete")
        return self.cleaned
    
    def clean_population(self):
        """Extract elderly population time series 2019-2024"""
        
        self.logger.info("Cleaning population data...")
        
        # Manually extracted from Table 110-06811
        # This is the most reliable method given the complex CSV format
        elderly_data = {
            'District': HK_DISTRICTS,
            'elderly_2019': [42000, 30900, 98700, 44500, 52300, 70200, 70000, 79000,
                            126900, 90500, 50200, 81700, 102400, 51400, 49600, 119300, 76900, 29400],
            'elderly_2020': [43200, 31900, 101400, 47100, 55000, 75300, 74400, 81400,
                            129400, 92900, 52600, 85700, 108200, 53500, 53000, 124200, 81300, 30600],
            'elderly_2021': [43600, 34100, 120000, 52400, 52400, 83600, 77500, 90200,
                            143800, 103800, 54900, 93400, 96200, 52900, 55600, 135600, 75400, 26300],
            'elderly_2022': [44200, 34900, 125300, 54700, 54300, 88000, 80700, 93600,
                            148800, 108700, 58100, 100000, 103700, 60800, 60600, 143900, 81500, 28000],
            'elderly_2023': [46400, 36900, 132900, 57400, 58800, 93200, 87100, 98900,
                            156100, 116800, 63700, 111600, 116100, 66500, 65700, 156200, 87400, 29700],
            'elderly_2024': [48600, 37800, 137600, 60900, 57700, 94800, 90200, 105100,
                            159600, 120000, 65800, 118000, 125100, 71700, 74500, 161200, 93900, 33400]
        }
        
        self.cleaned['elderly_population'] = pd.DataFrame(elderly_data)
        
        # Calculate growth rates
        for district in self.cleaned['elderly_population']['District']:
            mask = self.cleaned['elderly_population']['District'] == district
            p2019 = self.cleaned['elderly_population'].loc[mask, 'elderly_2019'].values[0]
            p2024 = self.cleaned['elderly_population'].loc[mask, 'elderly_2024'].values[0]
            growth = ((p2024 / p2019) - 1) * 100
            self.cleaned['elderly_population'].loc[mask, 'growth_2019_2024'] = growth
        
        self.logger.success(f"  → Elderly population: {len(self.cleaned['elderly_population'])} districts")
        self.logger.success(f"  → HK elderly 2024: {self.cleaned['elderly_population']['elderly_2024'].sum():,}")
        
        # Clean age proportions if available
        if 'population_age' in self.raw:
            df = self.raw['population_age'].copy()
            for col in ['Age_0_14', 'Age_15_24', 'Age_25_64', 'Age_65_plus']:
                df[col] = clean_numeric(df[col])
            self.cleaned['age_props'] = df
            self.logger.success(f"  → Age proportions: {len(df)} districts")
    
    def clean_deaths(self):
        """Clean and combine death records"""
        
        self.logger.info("Cleaning death records...")
        
        if 'deaths' not in self.raw:
            self.logger.warning("No death data found")
            return
        
        df = self.raw['deaths'].copy()
        
        # Clean cause names
        df['cause_clean'] = df['Cause of death'].str.replace('ICD-10:.*\)', '', regex=True)
        df['cause_clean'] = df['cause_clean'].str.replace('†', '')
        df['cause_clean'] = df['cause_clean'].str.strip()
        
        # Filter for total population
        self.cleaned['deaths_total'] = df[
            (df['Sex'] == 'Total') & 
            (df['Age group'] == 'All ages')
        ].copy()
        
        # Create pivot table by cause and year
        self.cleaned['deaths_by_cause'] = pd.pivot_table(
            self.cleaned['deaths_total'],
            values='Count',
            index='cause_clean',
            columns='Year',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Calculate totals
        year_cols = [2020, 2021, 2022, 2023, 2024]
        self.cleaned['deaths_by_cause']['total_2020_2024'] = (
            self.cleaned['deaths_by_cause'][year_cols].sum(axis=1)
        )
        self.cleaned['deaths_by_cause'] = self.cleaned['deaths_by_cause'].sort_values(
            'total_2020_2024', ascending=False
        )
        
        self.logger.success(f"  → Death records: {len(self.cleaned['deaths_total'])} rows")
        self.logger.success(f"  → Top cause: {self.cleaned['deaths_by_cause'].iloc[0]['cause_clean']}")
    
    def clean_hospital(self):
        """Clean hospital discharge data"""
        
        self.logger.info("Cleaning hospital data...")
        
        if 'hospital_discharges' not in self.raw:
            self.logger.warning("No hospital discharge data found")
            return
        
        df = self.raw['hospital_discharges'].copy()
        
        # Rename columns
        df.columns = ['disease', 'icd10', '2017', '2018', '2019', '2020', 
                     '2021', '2022', '2023', '2024']
        
        # Drop footer rows
        df = df[df['disease'].notna()]
        df = df[~df['disease'].str.contains('Overall|Notes', na=False)]
        
        # Convert to numeric
        for year in ['2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024']:
            df[year] = clean_numeric(df[year])
        
        # Calculate averages
        df['avg_2019_2024'] = df[['2019', '2020', '2021', '2022', '2023', '2024']].mean(axis=1)
        df = df.sort_values('avg_2019_2024', ascending=False)
        
        self.cleaned['hospital_discharges'] = df
        self.cleaned['hospital_top'] = df.head(20)
        
        self.logger.success(f"  → Hospital discharges: {len(df)} disease groups")
    
    def clean_households(self):
        """Clean household and income data"""
        
        self.logger.info("Cleaning household data...")
        
        # Income data - with fallback
        if 'income' in self.raw:
            income_data = self.raw['income'].copy()
            
            # Filter for 2024
            if 'Year' in income_data.columns:
                income_2024 = income_data[income_data['Year'] == 2024].copy()
            else:
                income_2024 = income_data.copy()
            
            if len(income_2024) > 0:
                self.cleaned['income_2024'] = income_2024[['District', 'Income_all']].dropna()
                self.logger.success(f"  → Income data: {len(self.cleaned['income_2024'])} districts")
            else:
                self.logger.warning("  → No 2024 income data found, using fallback")
                self._create_fallback_income()
        else:
            self.logger.warning("  → No income data found, using fallback")
            self._create_fallback_income()
        
        # Household data - with fallback
        if 'households' in self.raw:
            hh_data = self.raw['households'].copy()
            
            # Filter for 2024
            if 'Year' in hh_data.columns:
                hh_2024 = hh_data[hh_data['Year'] == 2024].copy()
            else:
                hh_2024 = hh_data.copy()
            
            if len(hh_2024) > 0:
                for col in ['Economically_active', 'Economically_inactive', 'Total']:
                    if col in hh_2024.columns:
                        hh_2024[col] = clean_numeric(hh_2024[col]) * 1000
                
                if 'Total' in hh_2024.columns and 'Economically_inactive' in hh_2024.columns:
                    hh_2024['inactive_ratio'] = hh_2024['Economically_inactive'] / hh_2024['Total']
                
                self.cleaned['households_2024'] = hh_2024
                self.logger.success(f"  → Household data: {len(self.cleaned['households_2024'])} districts")
            else:
                self.logger.warning("  → No 2024 household data found, using fallback")
                self._create_fallback_households()
        else:
            self.logger.warning("  → No household data found, using fallback")
            self._create_fallback_households()

        # -----------------------------------------------------------------
        # Labour 2.1 / 2.2: district labour numbers and participation rates
        # -----------------------------------------------------------------
        if 'labour_2_1' in self.raw:
            try:
                lf = self.raw['labour_2_1'].copy()
                # Ensure district column name
                if 'District' in lf.columns:
                    lf = lf.rename(columns={lf.columns[0]: 'District'}) if lf.columns[0] != 'District' else lf
                # Numeric conversion done in reader but coerce again
                for col in ['Male', 'Female', 'Both sexes']:
                    if col in lf.columns:
                        lf[col] = clean_numeric(lf[col])

                # Create labour_score normalized 0-1 based on Both sexes
                if 'Both sexes' in lf.columns:
                    min_v = lf['Both sexes'].min()
                    max_v = lf['Both sexes'].max()
                    if pd.notna(min_v) and pd.notna(max_v) and max_v > min_v:
                        lf['labour_score'] = (lf['Both sexes'] - min_v) / (max_v - min_v)
                    else:
                        lf['labour_score'] = 0.5

                self.cleaned['labour_2024'] = lf
                self.logger.success(f"  → Cleaned labour_2_1: {len(lf)} districts")
            except Exception as e:
                self.logger.warning(f"  → Could not clean labour_2_1: {e}")

        if 'labour_2_2' in self.raw:
            try:
                lp = self.raw['labour_2_2'].copy()
                for col in ['Male_pct', 'Female_pct', 'Both_pct']:
                    if col in lp.columns:
                        lp[col] = clean_numeric(lp[col])
                self.cleaned['labour_participation'] = lp
                self.logger.success(f"  → Cleaned labour participation (2.2): {len(lp)} rows")
            except Exception as e:
                self.logger.warning(f"  → Could not clean labour_2_2: {e}")

        # -----------------------------------------------------------------
        # Housing type (national-level by income brackets) - INFO ONLY
        # -----------------------------------------------------------------
        if 'housing_type' in self.raw:
            try:
                h = self.raw['housing_type'].copy()
                # This table is structured as Year/Quarter x Income range -> housing types
                # Too granular and aggregate to extract district-level insights
                # Store as-is for reference; no district-level cleaning needed
                self.cleaned['housing_type_national'] = h.head(20)  # Store first 20 rows as reference
                self.logger.success(f"  → Housing type (national aggregate): {len(h)} rows (reference only)")
            except Exception as e:
                self.logger.warning(f"  → Could not process housing_type: {e}")

    def _create_fallback_income(self):
        """Create fallback income data from known HK values"""
        
        fallback_income = pd.DataFrame({
            'District': HK_DISTRICTS,
            'Income_all': [
                42400, 40800, 32500, 36000, 29000, 24500, 31100, 25600,
                24200, 25500, 34200, 26200, 30000, 25800, 31300, 31000, 41200, 31000
            ]
        })
        self.cleaned['income_2024'] = fallback_income
        self.logger.success(f"  → Created fallback income data for {len(fallback_income)} districts")

    def _create_fallback_households(self):
        """Create fallback household data from elderly population"""
        
        # Use elderly population as proxy for inactive households
        elderly = self.cleaned['elderly_population'][['District', 'elderly_2024']].copy()
        elderly['Economically_inactive'] = elderly['elderly_2024'] * 0.7  # 70% of elderly are inactive
        elderly['Economically_active'] = elderly['elderly_2024'] * 0.3   # 30% still active
        elderly['Total'] = elderly['Economically_active'] + elderly['Economically_inactive']
        elderly['inactive_ratio'] = elderly['Economically_inactive'] / elderly['Total']
        
        self.cleaned['households_2024'] = elderly.rename(columns={'elderly_2024': 'elderly_population'})
        self.logger.success(f"  → Created fallback household data for {len(elderly)} districts")
    
    def create_master_district(self):
        """Combine all district-level data - FIXED for missing data"""
        
        self.logger.info("Creating master district dataset...")
        
        # Start with elderly population (always available)
        if 'elderly_population' not in self.cleaned:
            self.logger.error("No elderly population data available!")
            return
        
        master = self.cleaned['elderly_population'][
            ['District', 'elderly_2024', 'growth_2019_2024']
        ].copy()
        
        self.logger.info(f"  → Base districts: {len(master)}")
        
        # Add income if available
        if 'income_2024' in self.cleaned:
            income_data = self.cleaned['income_2024'][['District', 'Income_all']].copy()
            master = master.merge(income_data, on='District', how='left')
            self.logger.success(f"  → Added income data: {income_data['Income_all'].notna().sum()} districts")
        else:
            self.logger.warning("  → No income data available")
            # Add placeholder
            master['Income_all'] = 30000  # HK median income as fallback
        
        # Add household inactive ratio if available
        if 'households_2024' in self.cleaned:
            if 'inactive_ratio' in self.cleaned['households_2024'].columns:
                hh_data = self.cleaned['households_2024'][['District', 'inactive_ratio']].copy()
                master = master.merge(hh_data, on='District', how='left')
                self.logger.success(f"  → Added household data: {hh_data['inactive_ratio'].notna().sum()} districts")
        else:
            self.logger.warning("  → No household data available")
            # Add placeholder based on elderly population
            master['inactive_ratio'] = master['elderly_2024'] / master['elderly_2024'].max() * 0.5
        
        # Add age proportions if available
        if 'age_props' in self.cleaned:
            age_data = self.cleaned['age_props'][['District', 'Age_65_plus']].copy()
            master = master.merge(age_data, on='District', how='left')
            self.logger.success(f"  → Added age proportions: {age_data['Age_65_plus'].notna().sum()} districts")
        else:
            self.logger.warning("  → No age proportions data available")
            # Calculate from elderly population
            total_population_by_district = {
                'Central and Western': 229.4,
                'Wan Chai': 162.0,
                'Eastern': 514.4,
                'Southern': 254.7,
                'Yau Tsim Mong': 299.7,
                'Sham Shui Po': 432.3,
                'Kowloon City': 412.5,
                'Wong Tai Sin': 406.7,
                'Kwun Tong': 662.4,
                'Kwai Tsing': 491.6,
                'Tsuen Wan': 306.2,
                'Tuen Mun': 531.0,
                'Yuen Long': 671.1,
                'North': 338.4,
                'Tai Po': 327.9,
                'Sha Tin': 698.9,
                'Sai Kung': 498.2,
                'Islands': 195.3
            }
            
            # Calculate Age_65_plus percentage
            master['Age_65_plus'] = master.apply(
                lambda row: (row['elderly_2024'] / (total_population_by_district.get(row['District'], 1) * 1000)) * 100,
                axis=1
            )
            self.logger.success(f"  → Calculated age proportions from elderly population")
        
        # Fill NaN values with reasonable defaults
        master['Income_all'] = master['Income_all'].fillna(30000)  # HK median
        master['inactive_ratio'] = master['inactive_ratio'].fillna(0.35)  # HK average
        master['Age_65_plus'] = master['Age_65_plus'].fillna(22.3)  # HK average
        
        # Calculate demand potential index
        # Normalize each factor to 0-1 scale
        
        # Income score (lower income = higher need)
        income_min = master['Income_all'].min()
        income_max = master['Income_all'].max()
        if income_max > income_min:
            master['income_score'] = 1 - (master['Income_all'] - income_min) / (income_max - income_min)
        else:
            master['income_score'] = 0.5
        
        # Elderly score (higher elderly = higher need)
        elderly_min = master['elderly_2024'].min()
        elderly_max = master['elderly_2024'].max()
        if elderly_max > elderly_min:
            master['elderly_score'] = (master['elderly_2024'] - elderly_min) / (elderly_max - elderly_min)
        else:
            master['elderly_score'] = 0.5
        
        # Inactive ratio score (more inactive = higher need)
        inactive_min = master['inactive_ratio'].min()
        inactive_max = master['inactive_ratio'].max()
        if inactive_max > inactive_min:
            master['inactive_score'] = (master['inactive_ratio'] - inactive_min) / (inactive_max - inactive_min)
        else:
            master['inactive_score'] = 0.5
        
        # Composite score (0-100)
        master['demand_potential'] = (
            master['elderly_score'] * 0.5 +      # 50% weight - elderly population
            master['income_score'] * 0.3 +        # 30% weight - income (lower = higher need)
            master['inactive_score'] * 0.2        # 20% weight - living alone/inactive
        ) * 100
        
        # Ensure all values are within 0-100
        master['demand_potential'] = master['demand_potential'].clip(0, 100)
        
        self.cleaned['master_district'] = master.sort_values('demand_potential', ascending=False)
        
        self.logger.success(f"  → Master dataset created: {len(master)} districts")
        self.logger.success(f"  → Top demand district: {master.iloc[0]['District']} ({master.iloc[0]['demand_potential']:.1f})")
        self.logger.success(f"  → Bottom demand district: {master.iloc[-1]['District']} ({master.iloc[-1]['demand_potential']:.1f})")
        
        # Print summary statistics
        self.logger.info(f"  → Demand potential range: {master['demand_potential'].min():.1f} - {master['demand_potential'].max():.1f}")
        self.logger.info(f"  → Mean demand potential: {master['demand_potential'].mean():.1f}")