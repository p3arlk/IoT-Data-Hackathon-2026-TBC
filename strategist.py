"""
STEP 5: Generate actionable recommendations
"""
import pandas as pd
import numpy as np
from config import *
from utils import Logger, save_output

class Strategist:
    """Generate actionable recommendations"""
    
    def __init__(self, cleaned_data, insights, forecasts):
        self.data = cleaned_data
        self.insights = insights
        self.forecasts = forecasts
        self.recommendations = {}
        self.logger = Logger()
        
    def generate_all(self):
        """Execute all recommendation generation"""
        
        self.logger.section("STEP 5: GENERATING RECOMMENDATIONS")
        
        self.service_expansion_priorities()
        self.inventory_strategy()
        self.outreach_strategy()
        
        # Save recommendations
        for name, df in self.recommendations.items():
            if isinstance(df, pd.DataFrame):
                save_output(df, f'recommendations_{name}.csv', 'recommendations')
        
        self.logger.success("Recommendations complete")
        return self.recommendations
    
    def service_expansion_priorities(self):
        """Recommend districts for service expansion"""
        
        self.logger.info("Identifying service expansion priorities...")
        
        if 'service_gaps' not in self.insights:
            self.logger.warning("No service gap analysis found")
            return
        
        if 'elderly_2025_2030' not in self.forecasts:
            self.logger.warning("No elderly forecast found")
            return
        
        gaps = self.insights['service_gaps'].copy()
        forecast = self.forecasts['elderly_2025_2030'].copy()
        
        # Merge gap analysis with forecast
        priorities = gaps.merge(
            forecast[['District', 2025, 2030, 'annual_growth']],
            on='District',
            how='left'
        )
        
        # Calculate expansion score
        priorities['expansion_score'] = (
            priorities['service_gap'] * 0.4 +
            (priorities[2030] / 1000) * 0.3 +
            priorities['annual_growth'] * 0.3
        )
        
        priorities = priorities.sort_values('expansion_score', ascending=False)
        
        self.recommendations['expansion_priorities'] = priorities[
            ['District', 'demand_potential', 'service_gap', 2025, 2030, 'expansion_score']
        ].head(5)
        
        self.logger.success(f"  → Top 5 districts for expansion:")
        for i, row in self.recommendations['expansion_priorities'].iterrows():
            self.logger.success(f"     {i+1}. {row['District']}: Score={row['expansion_score']:.0f}")
    
    def inventory_strategy(self):
        """Recommend inventory positioning by district"""
        
        self.logger.info("Developing inventory strategy...")
        
        if 'equipment_demand_2025_2030' not in self.forecasts:
            self.logger.warning("No equipment demand forecast found")
            return
        
        demand = self.forecasts['equipment_demand_2025_2030']
        demand_2025 = demand[demand['Year'] == 2025].copy()
        
        # Top equipment by district
        inventory_plan = []
        
        for district in demand_2025['District'].unique()[:5]:
            district_demand = demand_2025[demand_2025['District'] == district].nlargest(3, 'Estimated_Demand')
            
            if len(district_demand) >= 3:
                inventory_plan.append({
                    'District': district,
                    'Priority_1': district_demand.iloc[0]['Equipment_Category'],
                    'Units_1': district_demand.iloc[0]['Estimated_Demand'],
                    'Priority_2': district_demand.iloc[1]['Equipment_Category'],
                    'Units_2': district_demand.iloc[1]['Estimated_Demand'],
                    'Priority_3': district_demand.iloc[2]['Equipment_Category'],
                    'Units_3': district_demand.iloc[2]['Estimated_Demand'],
                })
        
        self.recommendations['inventory_priorities'] = pd.DataFrame(inventory_plan)
        
        # Seasonal strategy
        self.recommendations['seasonal_strategy'] = {
            'Q1 (Jan-Mar)': 'Pre-position Respiratory equipment for flu season peak',
            'Q2 (Apr-Jun)': 'Stock Mobility equipment (post-fall season recovery)',
            'Q3 (Jul-Sep)': 'Increase Bathroom Safety inventory (summer bathing)',
            'Q4 (Oct-Dec)': 'Prepare Monitoring/Cognitive equipment (winter isolation)'
        }
        
        self.logger.success(f"  → Generated inventory plan for {len(inventory_plan)} districts")
        
        # If analyst found missing equipment suggestions, include them as a supply gap
        if 'missing_equipment_suggestions' in self.insights:
            try:
                missing = self.insights['missing_equipment_suggestions'].copy()
                missing['Recommended_Action'] = 'Consider sourcing / procurement to cover demand for top diseases'
                self.recommendations['supply_gaps'] = missing
                self.logger.success(f"  → Added {len(missing)} missing equipment suggestions to recommendations")
            except Exception as e:
                self.logger.warning(f"  → Could not add missing equipment suggestions: {e}")
    
    def outreach_strategy(self):
        """Recommend targeted outreach channels"""
        
        self.logger.info("Developing outreach strategy...")
        
        if 'service_gaps' not in self.insights:
            self.logger.warning("No service gap analysis found")
            return
        
        if 'user_personas' not in self.insights:
            self.logger.warning("No user personas found")
            return
        
        gaps = self.insights['service_gaps']
        underserved = gaps[gaps['priority'] == 'High'].head(3)
        
        outreach = []
        
        # District-persona matching
        district_persona_map = {
            'Kwun Tong': 'Solo Ager',
            'Wong Tai Sin': 'Solo Ager',
            'Eastern': 'Solo Ager',
            'Sha Tin': 'Spousal Caregiver Couple',
            'Tuen Mun': 'Spousal Caregiver Couple',
            'Kwai Tsing': 'Spousal Caregiver Couple',
            'Yuen Long': 'Multi-generational Family Caregiver',
            'North': 'Multi-generational Family Caregiver'
        }
        
        for _, row in underserved.iterrows():
            district = row['District']
            persona = district_persona_map.get(district, 'General Elderly')
            
            if persona == 'Solo Ager':
                channel = 'District Council elderly centres + door-to-door'
                message = '"Stay independent, stay home"'
            elif persona == 'Spousal Caregiver Couple':
                channel = 'Hospital discharge referrals + caregiver support groups'
                message = '"You care for them, we care for you"'
            elif persona == 'Multi-generational Family Caregiver':
                channel = 'Housing estate roadshows + school networks'
                message = '"Make room for memories, not worry"'
            else:
                channel = 'Community health ambassadors'
                message = '"Age in place with confidence"'
            
            outreach.append({
                'District': district,
                'Priority': row['priority'],
                'Target_Persona': persona,
                'Primary_Channel': channel,
                'Messaging': message,
                'Estimated_Reach': int(row['elderly_2024'] * 0.3),
                'Success_Metric': 'Rental conversions + assessments'
            })
        
        self.recommendations['outreach_plan'] = pd.DataFrame(outreach)
        self.logger.success(f"  → Created outreach plan for {len(outreach)} priority districts")