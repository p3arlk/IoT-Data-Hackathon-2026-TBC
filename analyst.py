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
        
        # Estimate service penetration (proxy): combine income and labour availability
        income_min = df['Income_all'].min()
        income_max = df['Income_all'].max()

        # Merge labour score if available
        if 'labour_2024' in self.data:
            lf = self.data['labour_2024'][['District', 'labour_score']].copy()
            df = df.merge(lf, on='District', how='left')
        else:
            df['labour_score'] = None

        # Normalized income (0-1)
        if income_max > income_min:
            df['income_norm'] = (df['Income_all'] - income_min) / (income_max - income_min)
        else:
            df['income_norm'] = 0.5

        # labour_score should already be 0-1; fill missing with median
        df['labour_score'] = df['labour_score'].fillna(df['labour_score'].median() if 'labour_score' in df.columns else 0.5)

        # Combine into estimated service penetration (weights: income 60%, labour 40%)
        df['estimated_service'] = (df['income_norm'] * 0.6 + df['labour_score'] * 0.4) * 100
        
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
        
        # Available equipment provided by the program
        available_equipment = [
            'Hospital Electric Bed', 'Powered mattress', 'Mattress with special function', 'Seat Cushion',
            'Safety Bed rail', 'Supporting Grip', 'Portable toilet frame',
            'Auto-wrapping commode', 'Shower commode chair', 'Rotary shower chair',
            'Robotic assist walker', 'Rollator wheelchair', 'Exoskeleton', 'Wheelchair with recliner function', 'Power wheelchair',
            'Hearing aids', 'Bone conduction hearing aids',
            'Foldable hoist', 'Assembled Ramp', 'Fall prevention package', 'Portable hair washing machine'
        ]

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
        
        # Identify top 10 diseases by deaths if available, else fall back to mapping list
        top_diseases = []
        if 'deaths_by_cause' in self.data:
            try:
                db = self.data['deaths_by_cause'].copy()
                if 'total_2020_2024' in db.columns:
                    top_diseases = db.sort_values('total_2020_2024', ascending=False).head(10)['cause_clean'].tolist()
                else:
                    top_diseases = db.head(10)['cause_clean'].tolist()
            except Exception:
                top_diseases = mapping['disease'].head(10).tolist()
        else:
            top_diseases = mapping['disease'].head(10).tolist()

        # Build top10 mapping and compare to available equipment
        rows = []
        def normalize(text):
            return str(text).lower().replace('-', ' ').replace('\u2019', "'")

        avail_norm = [normalize(a) for a in available_equipment]

        for disease in top_diseases:
            # Try to find mapping row
            row_map = mapping[mapping['disease'].str.lower() == disease.lower()]
            if len(row_map) == 0:
                # Try fuzzy / contains
                row_map = mapping[mapping['disease'].str.lower().str.contains(disease.split('(')[0].strip().lower(), na=False)]

            req_e = []
            examples = ''
            if len(row_map) > 0:
                examples = row_map.iloc[0]['specific_equipment']
                req_e = [e.strip() for e in str(examples).split(',') if e.strip()]
            else:
                req_e = []

            missing = []
            provided = []
            for eq in req_e:
                eq_n = normalize(eq)
                matched = False
                for a, a_n in zip(available_equipment, avail_norm):
                    # if any keyword overlaps
                    if any(token in a_n for token in eq_n.split() if len(token) > 3) or any(token in eq_n for token in a_n.split() if len(token) > 3):
                        provided.append(a)
                        matched = True
                        break
                if not matched:
                    missing.append(eq)

            rows.append({
                'Disease': disease,
                'Required_Equipment': '; '.join(req_e) if req_e else None,
                'Provided_Examples': '; '.join(sorted(set(provided))) if provided else None,
                'Missing_Equipment': '; '.join(sorted(set(missing))) if missing else None
            })

        top10_df = pd.DataFrame(rows)
        self.insights['top10_disease_equipment'] = top10_df

        # Aggregate unique missing equipments to suggest
        missing_set = set()
        for m in top10_df['Missing_Equipment'].dropna():
            for part in m.split(';'):
                missing_set.add(part.strip())

        missing_list = sorted([m for m in missing_set if m])
        self.insights['missing_equipment_suggestions'] = pd.DataFrame({'Missing_Equipment': missing_list})

        # Keep previous top5 output for backwards compatibility
        top5 = mapping.head(5)[['disease', 'primary_impairment', 'equipment_category_1', 'specific_equipment']].copy()
        top5.columns = ['Disease', 'Primary Impairment', 'Primary Equipment', 'Examples']
        self.insights['top5_diseases'] = top5

        self.logger.success(f"  → Mapped {len(mapping)} diseases to equipment")
        self.logger.success(f"  → Top 10 disease equipment gaps computed: {len(top10_df)} diseases")
    
    def create_personas(self):
        """Define user personas based on actual district clustering"""
        
        self.logger.info("Creating data-driven user personas...")
        
        if 'master_district' not in self.data:
            self.logger.warning("No master district data for persona generation")
            self._create_hardcoded_personas()
            return
        
        df = self.data['master_district'].copy()
        
        # Select key features for segmentation
        features = ['elderly_2024', 'Income_all', 'labour_score', 'inactive_ratio']
        
        # Check if all features exist
        if not all(f in df.columns for f in features):
            self.logger.warning(f"Missing features for segmentation")
            self._create_hardcoded_personas()
            return
        
        df_segment = df[['District'] + features].copy()
        df_segment = df_segment.dropna(subset=features)
        
        if len(df_segment) < 6:
            self.logger.warning(f"Not enough districts for segmentation ({len(df_segment)} < 6)")
            self._create_hardcoded_personas()
            return
        
        # Create segmentation based on quantiles - divide into High/Medium/Low groups
        df_segment['elderly_level'] = pd.qcut(df_segment['elderly_2024'], q=3, labels=['Low', 'Medium', 'High'], duplicates='drop')
        df_segment['income_level'] = pd.qcut(df_segment['Income_all'], q=3, labels=['Low', 'Medium', 'High'], duplicates='drop')
        df_segment['labour_level'] = pd.qcut(df_segment['labour_score'], q=3, labels=['Low', 'Medium', 'High'], duplicates='drop')
        df_segment['inactive_level'] = pd.qcut(df_segment['inactive_ratio'], q=3, labels=['Low', 'Medium', 'High'], duplicates='drop')
        
        # Define 6 personas based on actual district patterns
        personas_data = []
        
        # Persona 1: High Elderly + Low Income + Low Labour = High-Need Solo Agers
        p1 = df_segment[(df_segment['elderly_level'] == 'High') & (df_segment['income_level'] == 'Low')]
        if len(p1) > 0:
            personas_data.append({
                'Persona': 'High-Need Solo Elderly',
                'Character': 'Elderly living alone with limited income, highest vulnerability',
                'Age_Range': '75-95',
                'Living_Situation': 'Alone, limited family support',
                'Typical_Districts': ', '.join(p1['District'].tolist()),
                'Pain_Points': 'Fall risk, no caregiver, social isolation, limited financial access',
                'Primary_Equipment': 'Fall detectors, safety rails, grab bars, mobility aids, call systems',
                'District_Count': len(p1),
                'Avg_Elderly_Pop': int(p1['elderly_2024'].mean()),
                'Avg_Monthly_Income': int(p1['Income_all'].mean()),
                'Avg_Labour_Score': round(p1['labour_score'].mean(), 2)
            })
        
        # Persona 2: High Elderly + Medium/High Income + High Labour = Supported Affluent Elderly
        p2 = df_segment[(df_segment['elderly_level'] == 'High') & (df_segment['income_level'].isin(['Medium', 'High'])) & (df_segment['labour_level'] == 'High')]
        if len(p2) > 0:
            personas_data.append({
                'Persona': 'Affluent Supported Elderly',
                'Character': 'Elderly in wealthy areas with strong family networks',
                'Age_Range': '70-85',
                'Living_Situation': 'With family, adequate support',
                'Typical_Districts': ', '.join(p2['District'].tolist()),
                'Pain_Points': 'Accessibility, spousal strain, preventive care, health optimization',
                'Primary_Equipment': 'Transfer lifts, hospital beds, adaptive bathrooms, monitoring devices',
                'District_Count': len(p2),
                'Avg_Elderly_Pop': int(p2['elderly_2024'].mean()),
                'Avg_Monthly_Income': int(p2['Income_all'].mean()),
                'Avg_Labour_Score': round(p2['labour_score'].mean(), 2)
            })
        
        # Persona 3: Medium Elderly + Low Income + High Inactive = Economically Dependent Families
        p3 = df_segment[(df_segment['elderly_level'] == 'Medium') & (df_segment['income_level'] == 'Low') & (df_segment['inactive_level'] == 'High')]
        if len(p3) > 0:
            personas_data.append({
                'Persona': 'Economically Dependent Multi-Gen',
                'Character': 'Families with elderly + unemployed, space & financial constraints',
                'Age_Range': '65-80',
                'Living_Situation': 'With children/grandchildren, crowded housing',
                'Typical_Districts': ', '.join(p3['District'].tolist()),
                'Pain_Points': 'Space limitations, family caregiving burden, financial pressure, stairs',
                'Primary_Equipment': 'Space-saving walkers, fold-away equipment, bathroom safety aids',
                'District_Count': len(p3),
                'Avg_Elderly_Pop': int(p3['elderly_2024'].mean()),
                'Avg_Monthly_Income': int(p3['Income_all'].mean()),
                'Avg_Labour_Score': round(p3['labour_score'].mean(), 2)
            })
        
        # Persona 4: Low Elderly + High Income + High Labour = Tech-Savvy Pre-Elderly
        p4 = df_segment[(df_segment['elderly_level'] == 'Low') & (df_segment['income_level'] == 'High') & (df_segment['labour_level'] == 'High')]
        if len(p4) > 0:
            personas_data.append({
                'Persona': 'Tech-Savvy Pre-Elderly Professionals',
                'Character': 'High-income, high-employment areas, proactive health planning',
                'Age_Range': '50-70',
                'Living_Situation': 'Alone or with spouse, independent',
                'Typical_Districts': ', '.join(p4['District'].tolist()),
                'Pain_Points': 'Prevention, future planning, smart home integration, accessibility',
                'Primary_Equipment': 'Smart monitoring devices, exercise equipment, blood pressure monitors',
                'District_Count': len(p4),
                'Avg_Elderly_Pop': int(p4['elderly_2024'].mean()),
                'Avg_Monthly_Income': int(p4['Income_all'].mean()),
                'Avg_Labour_Score': round(p4['labour_score'].mean(), 2)
            })
        
        # Persona 5: High Elderly + High Inactive = Frail Dependent
        p5 = df_segment[(df_segment['elderly_level'] == 'High') & (df_segment['inactive_level'] == 'High')]
        if len(p5) > 0:
            personas_data.append({
                'Persona': 'Frail High-Dependency Elderly',
                'Character': 'Lowest functional capacity, highest care needs, 24/7 support',
                'Age_Range': '80-95+',
                'Living_Situation': 'With live-in caregiver or intensive family support',
                'Typical_Districts': ', '.join(p5['District'].tolist()),
                'Pain_Points': 'Bedsores, incontinence, complex medical needs, caregiver burnout',
                'Primary_Equipment': 'Pressure-relief mattresses, commodes, patient lifts, positioning aids',
                'District_Count': len(p5),
                'Avg_Elderly_Pop': int(p5['elderly_2024'].mean()),
                'Avg_Monthly_Income': int(p5['Income_all'].mean()),
                'Avg_Labour_Score': round(p5['labour_score'].mean(), 2)
            })
        
        # Persona 6: Remaining districts (middle-of-road)
        used_districts = set()
        for p in [p1, p2, p3, p4, p5]:
            used_districts.update(p['District'].tolist())
        p6 = df_segment[~df_segment['District'].isin(used_districts)]
        
        if len(p6) > 0:
            personas_data.append({
                'Persona': 'Mainstream Mixed-Needs Districts',
                'Character': 'Average elderly density, income, employment - diverse needs',
                'Age_Range': '65-85',
                'Living_Situation': 'Mixed (alone, couples, families)',
                'Typical_Districts': ', '.join(p6['District'].tolist()),
                'Pain_Points': 'Diverse: mobility issues, chronic disease management, social support',
                'Primary_Equipment': 'Balanced spectrum: walkers, grabs bars, beds, monitoring devices',
                'District_Count': len(p6),
                'Avg_Elderly_Pop': int(p6['elderly_2024'].mean()),
                'Avg_Monthly_Income': int(p6['Income_all'].mean()),
                'Avg_Labour_Score': round(p6['labour_score'].mean(), 2)
            })
        
        self.insights['user_personas'] = pd.DataFrame(personas_data)
        self.logger.success(f"  → Created {len(personas_data)} data-driven user personas from district clustering")
        for i, p in enumerate(personas_data):
            self.logger.success(f"     {i+1}. {p['Persona']} ({p['District_Count']} districts)")
    
    def _create_hardcoded_personas(self):
        """Fallback hardcoded personas if clustering fails"""
        
        personas = pd.DataFrame({
            'Persona': [
                'Solo Ager',
                'Spousal Caregiver Couple',
                'Multi-generational Family Caregiver',
                'Tech-Savvy Pre-Elderly',
                'Frail Elderly - High Dependency',
                'Community-dwelling with Chronic Disease'
            ],
            'Age_Range': ['75-95', '70-85', '65-80', '50-64', '80+', '65-85'],
            'Living_Situation': [
                'Alone',
                'With spouse only',
                'With children/grandchildren',
                'Alone or with spouse',
                'With spouse or live-in caregiver',
                'Alone or with spouse'
            ],
            'Typical_Districts': [
                'Kwun Tong, Wong Tai Sin, Eastern',
                'Sha Tin, Kwai Tsing, Tuen Mun',
                'Yuen Long, North, Tuen Mun',
                'Sai Kung, Central & Western, Wan Chai',
                'Eastern, Wong Tai Sin, Kwun Tong',
                'All districts'
            ],
            'Pain_Points': [
                'Fall risk, forgetfulness, no caregiver',
                'Physical strain, sleep disruption, transfer difficulty',
                'Space constraints, noise at night, stairs',
                'Future planning, prevention, smart home',
                'Bedsores, incontinence, 24/7 care',
                'Disease management, mobility, medication'
            ],
            'Primary_Equipment': [
                'Fall detector, GPS tracker, raised toilet seat',
                'Patient lift, hospital bed, shower chair',
                'Hospital bed, rollator walker, bathroom safety',
                'Smart sensors, exercise bike, blood pressure monitor',
                'Pressure relief mattress, commode, patient lift',
                'Oxygen concentrator, wheelchair, medication dispenser'
            ]
        })
        
        self.insights['user_personas'] = personas
        self.logger.success(f"  → Created fallback personas ({len(personas)} personas)")
    
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
        """Create fallback overlooked conditions - expanding to top 10 underserving conditions"""
        
        overlooked = pd.DataFrame({
            'condition': [
                'Arthrosis (Osteoarthritis)',
                'Fracture of femur (Hip fracture)',
                'Rheumatoid arthritis',
                'Cataract',
                'Asthma',
                'Depression & Mental Health',
                'Hearing loss',
                'Visual impairment',
                'Chronic pain syndrome',
                'Balance disorders & Vertigo'
            ],
            'annual_impact': [
                '~8,000 hospital discharges',
                '~11,000 fractures',
                '~10,000 hospital visits',
                '~25,000 surgeries',
                '~7,000 admissions',
                '~5,000+ diagnoses',
                '~200,000 prevalence',
                '~150,000 prevalence',
                '~6,000+ chronic cases',
                '~4,000 emergency visits'
            ],
            'equipment_needed': [
                'Rollator walker, raised toilet seat, grab bars',
                'Walker, shower chair, bed rails, commode',
                'Adaptive utensils, therapy putty, exercise aids',
                'Magnifiers, adaptive lighting, reading aids',
                'Nebulizer, peak flow meter, air purifier',
                'Medication dispenser, fall detector',
                'Hearing aids, amplified phones, visual alerts',
                'Magnifiers, talking devices, large-print items, lighting',
                'Pain relief cushions, massagers, ergonomic aids',
                'Balance board, handrails, walking aids, vestibular tools'
            ]
        })
        
        self.insights['overlooked_conditions'] = overlooked
        self.logger.success(f"  → Created fallback overlooked conditions list ({len(overlooked)} conditions)")