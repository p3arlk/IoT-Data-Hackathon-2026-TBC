"""
STEP 3: Analyse service gaps, disease mapping, and user personas - FIXED
"""
import pandas as pd
import numpy as np
from config import *
from utils import Logger, save_output

class Analyst:
    """Extract insights from cleaned data"""
    
    def __init__(self, cleaned_data):
        self.data = cleaned_data
        self.insights = {}
        self.logger = Logger()
        
    def analyse_all(self):
        """Execute all analysis steps"""
        
        self.logger.section("STEP 3: ANALYSING DATA")
        
        self.identify_service_gaps()
        self.map_disease_to_equipment()
        self.create_personas()
        self.find_overlooked_conditions()
        
        # Save insights
        for name, df in self.insights.items():
            if isinstance(df, pd.DataFrame):
                save_output(df, f'insights_{name}.csv', 'insights')
        
        self.logger.success("Analysis complete")
        return self.insights
    
    def identify_service_gaps(self):
        """Find high-need, underserved districts - FIXED for NaN values"""
        
        self.logger.info("Identifying service gaps...")
        
        if 'master_district' not in self.data:
            self.logger.warning("No master district data found")
            return
        
        df = self.data['master_district'].copy()
        
        # Check if we have all required columns
        required_cols = ['Income_all', 'demand_potential', 'elderly_2024']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            self.logger.warning(f"Missing columns: {missing_cols}")
            # Create fallback service gaps based on elderly population
            self._create_fallback_service_gaps(df)
            return
        
        # Drop rows with missing values
        df = df.dropna(subset=['Income_all', 'demand_potential'])
        
        if len(df) == 0:
            self.logger.warning("No valid data for service gap analysis")
            return
        
        # Estimate service penetration (proxy: higher income = more access to purchase)
        income_min = df['Income_all'].min()
        income_max = df['Income_all'].max()
        
        if income_max > income_min:
            df['estimated_service'] = (
                (df['Income_all'] - income_min) / 
                (income_max - income_min)
            ) * 100
        else:
            df['estimated_service'] = 50  # Default value
        
        # Calculate service gap
        df['service_gap'] = df['demand_potential'] - df['estimated_service']
        df['gap_status'] = np.where(
            df['service_gap'] > df['service_gap'].median(),
            'Underserved',
            'Well-served'
        )
        
        # Priority score - handle NaN and duplicates
        df['priority_score'] = df['demand_potential'] * (1 - df['estimated_service']/100)
        
        # Remove NaN values for priority calculation
        priority_valid = df['priority_score'].dropna()
        
        if len(priority_valid) >= 4:  # Need at least 4 for qcut
            try:
                df['priority'] = pd.qcut(
                    df['priority_score'], 
                    q=3, 
                    labels=['Low', 'Medium', 'High'],
                    duplicates='drop'  # Drop duplicate edges
                )
            except Exception as e:
                self.logger.warning(f"Could not create priority quartiles: {e}")
                # Fallback: use simple threshold
                median_score = df['priority_score'].median()
                df['priority'] = np.where(
                    df['priority_score'] > median_score,
                    'High',
                    'Low'
                )
        else:
            # Fallback: use simple threshold
            median_score = df['priority_score'].median()
            df['priority'] = np.where(
                df['priority_score'] > median_score,
                'High',
                'Low'
            )
        
        # Fill any remaining NaN values
        df['priority'] = df['priority'].fillna('Low')
        df['gap_status'] = df['gap_status'].fillna('Underserved')
        
        self.insights['service_gaps'] = df.sort_values('service_gap', ascending=False)
        
        underserved = len(df[df['gap_status'] == 'Underserved'])
        self.logger.success(f"  → {underserved} underserved districts identified")
        
        if len(df) > 0:
            self.logger.success(f"  → Top priority: {df.iloc[0]['District'] if 'District' in df.columns else 'N/A'}")
    
    def _create_fallback_service_gaps(self, df):
        """Create fallback service gaps based on elderly population"""
        
        self.logger.info("Creating fallback service gaps...")
        
        if 'elderly_2024' not in df.columns:
            self.logger.error("No elderly population data for fallback")
            return
        
        df = df.copy()
        df = df.dropna(subset=['elderly_2024'])
        
        # Use elderly population as demand proxy
        elderly_max = df['elderly_2024'].max()
        elderly_min = df['elderly_2024'].min()
        
        if elderly_max > elderly_min:
            df['demand_potential'] = (
                (df['elderly_2024'] - elderly_min) / 
                (elderly_max - elderly_min)
            ) * 100
        else:
            df['demand_potential'] = 50
        
        # Assume uniform service penetration
        df['estimated_service'] = 50
        df['service_gap'] = df['demand_potential'] - df['estimated_service']
        df['gap_status'] = np.where(df['service_gap'] > 0, 'Underserved', 'Well-served')
        df['priority_score'] = df['demand_potential']
        
        # Simple priority based on demand
        median_demand = df['demand_potential'].median()
        df['priority'] = np.where(
            df['demand_potential'] > median_demand,
            'High',
            'Low'
        )
        
        self.insights['service_gaps'] = df.sort_values('service_gap', ascending=False)
        self.logger.success(f"  → Created fallback service gaps for {len(df)} districts")
    
    def map_disease_to_equipment(self):
        """Create evidence-based disease to equipment mapping"""
        
        self.logger.info("Mapping diseases to equipment...")
        
        mapping = pd.DataFrame({
            'disease': [
                'Cerebrovascular diseases (Stroke)',
                'Dementia',
                'Chronic lower respiratory diseases',
                'Diabetes mellitus',
                'Malignant neoplasms (Cancer)',
                'Diseases of heart',
                'Pneumonia',
                'Arthrosis',
                'Rheumatoid arthritis',
                'Fracture of femur',
                "Parkinson's disease",
                'Septicaemia'
            ],
            'primary_impairment': [
                'Hemiplegia, paralysis, speech difficulty',
                'Memory loss, wandering, confusion',
                'Breathlessness, low stamina',
                'Neuropathy, foot ulcers, vision problems',
                'General frailty, pain, fatigue',
                'Cardiac insufficiency, chest pain',
                'Respiratory distress, hypoxia',
                'Joint stiffness, pain, reduced mobility',
                'Joint deformity, pain, limited grip',
                'Immobility, fall recovery',
                'Tremor, rigidity, bradykinesia',
                'Systemic infection, sepsis'
            ],
            'equipment_category_1': [
                'Mobility - Wheelchairs', 'Cognitive Support', 'Respiratory',
                'Personal Care', 'Beds & Transfer', 'Monitoring',
                'Respiratory', 'Mobility - Walkers', 'Daily Living',
                'Mobility - Walkers', 'Daily Living', 'Monitoring'
            ],
            'equipment_category_2': [
                'Beds & Transfer', 'Monitoring', 'Monitoring',
                'Bathroom Safety', 'Daily Living', 'Beds & Transfer',
                'Monitoring', 'Bathroom Safety', 'Exercise',
                'Bathroom Safety', 'Mobility - Walkers', 'Beds & Transfer'
            ],
            'specific_equipment': [
                'Wheelchair, transfer board, shower chair, hospital bed',
                'GPS tracker, medication dispenser, sensor mat, automatic lights',
                'Oxygen concentrator, pulse oximeter, nebulizer',
                'Long-handled sponge, diabetic shoes, grab bars',
                'Hospital bed, patient lift, commode, reacher',
                'Blood pressure monitor, fall detector, hospital bed',
                'Oxygen concentrator, CPAP, suction machine',
                'Rollator walker, raised toilet seat, bath board',
                'Adaptive utensils, jar opener, therapy putty',
                'Walker, shower chair, raised toilet seat, bed rail',
                'Utensils with grip, walker, bathroom grab bars',
                'Patient monitor, hospital bed, pulse oximeter'
            ]
        })
        
        self.insights['disease_equipment_map'] = mapping
        
        # Top 5 diseases table
        top5 = mapping.head(5)[['disease', 'primary_impairment', 'equipment_category_1', 'specific_equipment']].copy()
        top5.columns = ['Disease', 'Primary Impairment', 'Primary Equipment', 'Examples']
        self.insights['top5_diseases'] = top5
        
        self.logger.success(f"  → Mapped {len(mapping)} diseases to equipment")
    
    def create_personas(self):
        """Define user personas based on HK demographics"""
        
        self.logger.info("Creating user personas...")
        
        personas = pd.DataFrame({
            'persona': [
                'Solo Ager',
                'Spousal Caregiver Couple',
                'Multi-generational Family Caregiver',
                'Tech-Savvy Pre-Elderly',
                'Frail Elderly - High Dependency',
                'Community-dwelling with Chronic Disease'
            ],
            'age_range': [
                '75-95',
                '70-85',
                '65-80',
                '50-64',
                '80+',
                '65-85'
            ],
            'living_situation': [
                'Alone',
                'With spouse only',
                'With children/grandchildren',
                'Alone or with spouse',
                'With spouse or live-in caregiver',
                'Alone or with spouse'
            ],
            'typical_districts': [
                'Kwun Tong, Wong Tai Sin, Eastern',
                'Sha Tin, Kwai Tsing, Tuen Mun',
                'Yuen Long, North, Tuen Mun',
                'Sai Kung, Central & Western, Wan Chai',
                'Eastern, Wong Tai Sin, Kwun Tong',
                'All districts'
            ],
            'pain_points': [
                'Fall risk, forgetfulness, no caregiver',
                'Physical strain, sleep disruption, transfer difficulty',
                'Space constraints, noise at night, stairs',
                'Future planning, prevention, smart home',
                'Bedsores, incontinence, 24/7 care',
                'Disease management, mobility, medication'
            ],
            'primary_equipment': [
                'Fall detector, GPS tracker, raised toilet seat',
                'Patient lift, hospital bed, shower chair',
                'Hospital bed, rollator walker, bathroom safety',
                'Smart sensors, exercise bike, blood pressure monitor',
                'Pressure relief mattress, commode, patient lift',
                'Oxygen concentrator, wheelchair, medication dispenser'
            ]
        })
        
        self.insights['user_personas'] = personas
        self.logger.success(f"  → Created {len(personas)} user personas")
    
    def find_overlooked_conditions(self):
        """Identify non-fatal but disabling conditions"""
        
        self.logger.info("Identifying overlooked conditions...")
        
        # From hospital discharge data (high volume, low mortality)
        if 'hospital_top' in self.data:
            hospital = self.data['hospital_top']
            
            overlooked = hospital[
                ~hospital['disease'].str.contains('Malignant|Heart|Pneumonia|Cerebrovascular|COVID', 
                                                 case=False, na=False)
            ].head(10)
            
            if len(overlooked) > 0:
                self.insights['overlooked_conditions'] = overlooked[['disease', 'avg_2019_2024']]
                self.logger.success(f"  → Found {len(overlooked)} overlooked conditions")
                for _, row in overlooked.head(3).iterrows():
                    self.logger.success(f"     - {row['disease']}: {row['avg_2019_2024']:,.0f} annual discharges")
            else:
                self._create_fallback_overlooked()
        else:
            self._create_fallback_overlooked()
    
    def _create_fallback_overlooked(self):
        """Create fallback overlooked conditions"""
        
        overlooked = pd.DataFrame({
            'condition': [
                'Arthrosis',
                'Fracture of femur',
                'Rheumatoid arthritis',
                'Cataract',
                'Asthma',
                'Depression',
                'Hearing loss',
                'Visual impairment'
            ],
            'annual_impact': [
                '~8,000 hospital discharges',
                '~11,000 fractures',
                '~10,000 hospital visits',
                '~25,000 surgeries',
                '~7,000 admissions',
                '~5,000 diagnoses',
                '~200,000 prevalence',
                '~150,000 prevalence'
            ],
            'equipment_needed': [
                'Rollator walker, raised toilet seat, grab bars',
                'Walker, shower chair, bed rails, commode',
                'Adaptive tools, therapy putty, exercise equipment',
                'Magnifiers, adaptive lighting, daily living aids',
                'Nebulizer, peak flow meter, air purifier',
                'Medication dispenser, social connection device',
                'Hearing aids, amplified phones',
                'Magnifiers, talking devices, large-print items'
            ]
        })
        
        self.insights['overlooked_conditions'] = overlooked
        self.logger.success(f"  → Created fallback overlooked conditions list ({len(overlooked)} conditions)")