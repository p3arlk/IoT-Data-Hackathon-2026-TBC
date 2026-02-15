"""
STEP 1: Read all raw data files - FIXED VERSION
"""
import pandas as pd
import csv
from config import *
from utils import safe_read_csv, safe_read_excel, Logger, save_output

class DataReader:
    """Read all raw data files"""
    
    def __init__(self):
        self.logger = Logger()
        self.data = {}
        
    def read_all(self):
        """Execute all read operations"""
        
        self.logger.section("STEP 1: READING RAW DATA")
        
        self.read_population_data()
        self.read_death_data()
        self.read_hospital_data()
        self.read_household_data()
        
        self.logger.success(f"Loaded {len(self.data)} datasets")
        return self.data
    
    def read_population_data(self):
        """Read all population-related files"""
        
        self.logger.info("Loading population data...")
        
        # Table 110-06811: Detailed population by District, Sex, Age 
        if POPULATION_DETAILED_FILE.exists():
            try:
                df = pd.read_csv(
                    POPULATION_DETAILED_FILE,
                    skiprows=2,
                    encoding='utf-8',
                    on_bad_lines='skip'  # Skip bad lines
                )
                self.data['population_detailed'] = df
                self.logger.success(f"  → population_detailed: {len(df)} rows")
            except Exception as e:
                self.logger.warning(f"  → Could not load population_detailed: {e}")
        
        # Table 1.1: Population summary
        if POPULATION_SUMMARY_FILE.exists():
            try:
                df = pd.read_csv(
                    POPULATION_SUMMARY_FILE, 
                    skiprows=3, 
                    encoding='utf-8',
                    on_bad_lines='skip'
                )
                # Clean column names - the file has empty columns
                df = df.dropna(how='all', axis=1)  # Drop empty columns
                if len(df.columns) >= 3:
                    df.columns = ['District', 'Male', 'Female', 'Both_sexes'][:len(df.columns)]
                    df = df.dropna(subset=['District'])
                    df = df[df['District'] != 'Whole Territory']
                    self.data['population_summary'] = df
                    self.logger.success(f"  → population_summary: {len(df)} districts")
            except Exception as e:
                self.logger.warning(f"  → Could not load population_summary: {e}")
        
        # Table 1.2: Age proportions
        if POPULATION_AGE_FILE.exists():
            try:
                df = pd.read_csv(
                    POPULATION_AGE_FILE, 
                    skiprows=3, 
                    encoding='utf-8',
                    on_bad_lines='skip'
                )
                df = df.dropna(how='all', axis=1)
                if len(df.columns) >= 4:
                    df.columns = ['District', 'Age_0_14', 'Age_15_24', 'Age_25_64', 'Age_65_plus'][:len(df.columns)]
                    df = df.dropna(subset=['District'])
                    df = df[df['District'] != 'Whole Territory']
                    self.data['population_age'] = df
                    self.logger.success(f"  → population_age: {len(df)} districts")
            except Exception as e:
                self.logger.warning(f"  → Could not load population_age: {e}")
    
    def read_death_data(self):
        """Read death records 2020-2024 - FIXED for CSV issues"""
        
        self.logger.info("Loading death records...")
        
        death_dfs = []
        
        for year, filepath in DEATH_FILES.items():
            if filepath.exists():
                try:
                    # Try reading with different encodings and error handling
                    try:
                        df = pd.read_csv(
                            filepath, 
                            encoding='utf-8',
                            on_bad_lines='skip',
                            engine='python'  # More flexible parser
                        )
                    except:
                        df = pd.read_csv(
                            filepath, 
                            encoding='latin1',
                            on_bad_lines='skip',
                            engine='python'
                        )
                    
                    if df is not None and len(df) > 0:
                        df['Year'] = year
                        
                        # Clean column names
                        df.columns = df.columns.str.strip()
                        
                        # Rename columns if they have different names
                        if 'Cause of death' not in df.columns:
                            # Try to find the right column
                            for col in df.columns:
                                if 'cause' in col.lower() or 'Cause' in col:
                                    df = df.rename(columns={col: 'Cause of death'})
                                if 'age' in col.lower():
                                    df = df.rename(columns={col: 'Age group'})
                                if 'sex' in col.lower():
                                    df = df.rename(columns={col: 'Sex'})
                                if 'count' in col.lower() or 'Count' in col:
                                    df = df.rename(columns={col: 'Count'})
                        
                        death_dfs.append(df)
                        self.logger.success(f"  → deaths_{year}: {len(df)} rows")
                except Exception as e:
                    self.logger.warning(f"  → Could not load deaths_{year}: {e}")
        
        if death_dfs:
            self.data['deaths'] = pd.concat(death_dfs, ignore_index=True)
            self.logger.success(f"  → combined deaths: {len(self.data['deaths'])} rows")
    
    def read_hospital_data(self):
        """Read hospital-related data"""
        
        self.logger.info("Loading hospital data...")
        
        # IPDPDD discharges
        if HOSPITAL_DISCHARGES_FILE.exists():
            try:
                df = pd.read_excel(
                    HOSPITAL_DISCHARGES_FILE,
                    sheet_name='Sheet1',
                    skiprows=2,
                    header=None  # Don't use default header
                )
                
                # Set first row as header
                df.columns = df.iloc[0]
                df = df[1:].reset_index(drop=True)
                
                # Drop empty rows
                df = df.dropna(how='all')
                
                # Rename first column
                df = df.rename(columns={df.columns[0]: 'Disease group'})
                
                self.data['hospital_discharges'] = df
                self.logger.success(f"  → hospital_discharges: {len(df)} disease groups")
            except Exception as e:
                self.logger.warning(f"  → Could not load hospital_discharges: {e}")
        
        # Hospital beds
        if HOSPITAL_BEDS_FILE.exists():
            try:
                df = pd.read_csv(
                    HOSPITAL_BEDS_FILE, 
                    skiprows=2, 
                    encoding='utf-8',
                    on_bad_lines='skip'
                )
                self.data['hospital_beds'] = df
                self.logger.success(f"  → hospital_beds: {len(df)} rows")
            except Exception as e:
                self.logger.warning(f"  → Could not load hospital_beds: {e}")
    
    def read_household_data(self):
    #Read household, income, and labour force data - FIXED for column mismatch
    
        self.logger.info("Loading household & income data...")
        
        # =====================================================================
        # Table 3.1: Households by district
        # =====================================================================
        if HOUSEHOLD_FILE.exists():
            try:
                df = pd.read_csv(
                    HOUSEHOLD_FILE, 
                    skiprows=3, 
                    encoding='utf-8',
                    on_bad_lines='skip',
                    engine='python'
                )
                
                # Drop empty columns
                df = df.dropna(how='all', axis=1)
                df = df.dropna(how='all', axis=0)
                
                # Remove rows with note text
                df = df[~df.iloc[:, 0].astype(str).str.contains('Note', na=False)]
                df = df[~df.iloc[:, 0].astype(str).str.contains('Note\(s\)', na=False)]
                
                # Get the actual number of columns
                n_cols = len(df.columns)
                
                if n_cols >= 4:
                    # Check if first column contains year
                    first_val = str(df.iloc[0, 0]) if len(df) > 0 else ""
                    
                    if '2024' in first_val or 'Year' in first_val:
                        # Format: Year, District, Active, Inactive, Total
                        col_names = ['Year', 'District', 'Economically_active', 'Economically_inactive', 'Total']
                        df.columns = col_names[:n_cols]
                    else:
                        # Format: District, Active, Inactive, Total
                        col_names = ['District', 'Economically_active', 'Economically_inactive', 'Total']
                        df.columns = col_names[:n_cols]
                        # Add Year column
                        df.insert(0, 'Year', 2024)
                    
                    # Clean data
                    df = df.dropna(subset=['District'])
                    df = df[df['District'].astype(str).str.strip() != '']
                    df = df[~df['District'].astype(str).str.contains('District Council', na=False)]
                    df = df[~df['District'].astype(str).str.contains('Note', na=False)]
                    
                    # Convert to numeric
                    for col in ['Economically_active', 'Economically_inactive', 'Total']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    self.data['households'] = df
                    self.logger.success(f"  → households: {len(df)} rows")
                    
            except Exception as e:
                self.logger.warning(f"  → Could not load households: {e}")
        
        # =====================================================================
        # Table 3.2: Household income - FIXED for column mismatch
        # =====================================================================
        if INCOME_FILE.exists():
            try:
                df = pd.read_csv(
                    INCOME_FILE, 
                    skiprows=3, 
                    encoding='utf-8',
                    on_bad_lines='skip',
                    engine='python'
                )
                
                # Drop empty columns
                df = df.dropna(how='all', axis=1)
                df = df.dropna(how='all', axis=0)
                
                # Remove rows with note text
                df = df[~df.iloc[:, 0].astype(str).str.contains('Note', na=False)]
                df = df[~df.iloc[:, 0].astype(str).str.contains('Note\(s\)', na=False)]
                
                # Get the actual number of columns
                n_cols = len(df.columns)
                
                self.logger.info(f"  → Income file has {n_cols} columns")
                
                # Handle different column structures
                if n_cols == 3:
                    # Format: District, Income_active, Income_all
                    df.columns = ['District', 'Income_active', 'Income_all']
                    df.insert(0, 'Year', 2024)
                    
                elif n_cols == 4:
                    # Check if first column is Year or District
                    first_val = str(df.iloc[0, 0]) if len(df) > 0 else ""
                    
                    if '2024' in first_val or 'Year' in first_val:
                        # Format: Year, District, Income_active, Income_all
                        df.columns = ['Year', 'District', 'Income_active', 'Income_all']
                    else:
                        # Format: District, Income_active, Income_all, Extra
                        df.columns = ['District', 'Income_active', 'Income_all', 'Extra']
                        df = df.drop(columns=['Extra'])
                        df.insert(0, 'Year', 2024)
                        
                elif n_cols == 5:
                    # Format: Year, District, Income_active, Income_all, Extra
                    df.columns = ['Year', 'District', 'Income_active', 'Income_all', 'Extra']
                    df = df.drop(columns=['Extra'])
                    
                elif n_cols == 2:
                    # Format: District, Income_all (only one income column)
                    df.columns = ['District', 'Income_all']
                    df['Income_active'] = df['Income_all']  # Use same value as proxy
                    df.insert(0, 'Year', 2024)
                
                # Clean data
                if 'District' in df.columns:
                    df = df.dropna(subset=['District'])
                    df = df[df['District'].astype(str).str.strip() != '']
                    df = df[~df['District'].astype(str).str.contains('District Council', na=False)]
                    df = df[~df['District'].astype(str).str.contains('Note', na=False)]
                    df = df[~df['District'].astype(str).str.contains('Whole Territory', na=False)]
                
                # Convert to numeric
                for col in ['Income_active', 'Income_all']:
                    if col in df.columns:
                        # Remove commas and HK$ before converting
                        df[col] = df[col].astype(str).str.replace(',', '')
                        df[col] = df[col].astype(str).str.replace('HK\$', '', regex=True)
                        df[col] = df[col].astype(str).str.replace(' ', '')
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                self.data['income'] = df
                self.logger.success(f"  → income: {len(df)} rows")
                self.logger.success(f"  → income columns: {df.columns.tolist()}")
                
            except Exception as e:
                self.logger.warning(f"  → Could not load income: {e}")
                import traceback
                traceback.print_exc()
        
        # =====================================================================
        # Table 210-06822: Labour force
        # =====================================================================
        if LABOUR_FORCE_FILE.exists():
            try:
                df = pd.read_csv(
                    LABOUR_FORCE_FILE, 
                    skiprows=2, 
                    encoding='utf-8',
                    on_bad_lines='skip',
                    engine='python'
                )
                self.data['labour_force'] = df
                self.logger.success(f"  → labour_force: {len(df)} rows")
            except Exception as e:
                self.logger.warning(f"  → Could not load labour_force: {e}")

        # =====================================================================
        # Table 2.1 and 2.2: District labour force + participation rate
        # =====================================================================
        if LABOUR_2_1_FILE.exists():
            try:
                df = pd.read_csv(
                    LABOUR_2_1_FILE,
                    skiprows=2,
                    encoding='utf-8',
                    engine='python'
                )

                # Attempt to set sensible column names
                if len(df.columns) >= 4:
                    df.columns = ['District', 'Male', 'Female', 'Both sexes'][:len(df.columns)]
                # Drop summary rows
                df = df[~df['District'].astype(str).str.contains('Whole Territory|Table|Year', na=False)]
                # Convert numeric
                for col in ['Male', 'Female', 'Both sexes']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                self.data['labour_2_1'] = df
                self.logger.success(f"  → labour_2_1: {len(df)} rows")
                try:
                    save_output(df.head(10), 'raw_labour_2_1_head.csv', 'cleaned')
                except Exception:
                    pass
            except Exception as e:
                self.logger.warning(f"  → Could not load labour_2_1: {e}")

        if LABOUR_2_2_FILE.exists():
            try:
                df = pd.read_csv(
                    LABOUR_2_2_FILE,
                    skiprows=2,
                    encoding='utf-8',
                    engine='python'
                )

                if len(df.columns) >= 4:
                    df.columns = ['District', 'Male_pct', 'Female_pct', 'Both_pct'][:len(df.columns)]
                df = df[~df['District'].astype(str).str.contains('Whole Territory|Table|Year', na=False)]
                for col in ['Male_pct', 'Female_pct', 'Both_pct']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                self.data['labour_2_2'] = df
                self.logger.success(f"  → labour_2_2: {len(df)} rows")
                try:
                    save_output(df.head(10), 'raw_labour_2_2_head.csv', 'cleaned')
                except Exception:
                    pass
            except Exception as e:
                self.logger.warning(f"  → Could not load labour_2_2: {e}")

        # =====================================================================
        # Table 130-06609A: Household by income and type of housing (national-level)
        # =====================================================================
        if HOUSING_TYPE_FILE.exists():
            try:
                df = pd.read_csv(
                    HOUSING_TYPE_FILE,
                    skiprows=2,
                    encoding='utf-8',
                    engine='python',
                    on_bad_lines='skip'
                )
                # Drop fully-empty columns
                df = df.dropna(how='all', axis=1)
                # Remove footers
                df = df[~df.iloc[:, 0].astype(str).str.contains('Note|Source|Release Date', na=False)]
                self.data['housing_type'] = df
                self.logger.success(f"  → housing_type: {len(df)} rows")
                try:
                    save_output(df.head(10), 'raw_housing_type_head.csv', 'cleaned')
                except Exception:
                    pass
            except Exception as e:
                self.logger.warning(f"  → Could not load housing_type: {e}")