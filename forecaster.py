"""
STEP 4: Forecast aging population and equipment demand
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from config import *
from utils import Logger, save_output

class Forecaster:
    """Predict future elderly population and equipment demand"""
    
    def __init__(self, cleaned_data, insights):
        self.data = cleaned_data
        self.insights = insights
        self.forecasts = {}
        self.logger = Logger()
        
    def forecast_all(self):
        """Execute all forecasting models"""
        
        self.logger.section("STEP 4: FORECASTING")
        
        self.forecast_elderly_population()
        self.forecast_equipment_demand()
        self.simulate_pandemic_scenario()
        
        # Save forecasts
        for name, df in self.forecasts.items():
            if isinstance(df, pd.DataFrame):
                save_output(df, f'forecast_{name}.csv', 'forecasts')
        
        self.logger.success("Forecasting complete")
        return self.forecasts
    
    def forecast_elderly_population(self):
        """Linear regression forecast of elderly population by district"""
        
        self.logger.info("Forecasting elderly population 2025-2030...")
        
        if 'elderly_population' not in self.data:
            self.logger.warning("No elderly population data found")
            return
        
        df = self.data['elderly_population'].copy()
        
        # Prepare time series
        years = np.array(HISTORICAL_YEARS).reshape(-1, 1)
        forecast_years = np.array(FORECAST_YEARS).reshape(-1, 1)
        
        results = []
        
        for _, row in df.iterrows():
            district = row['District']
            
            # Get population values
            pop_values = row[[f'elderly_{year}' for year in HISTORICAL_YEARS]].values.astype(float)
            
            # Fit linear regression
            model = LinearRegression()
            model.fit(years, pop_values)
            
            # Predict
            pred = model.predict(forecast_years)
            r2 = r2_score(pop_values, model.predict(years))
            
            result = {'District': district}
            for i, year in enumerate(FORECAST_YEARS):
                result[year] = int(pred[i])
            result['annual_growth'] = model.coef_[0]
            result['r2_score'] = r2
            
            results.append(result)
        
        forecast_df = pd.DataFrame(results)
        
        # Add HK total
        hk_total = {'District': 'Hong Kong Total'}
        for year in FORECAST_YEARS:
            hk_total[year] = forecast_df[year].sum()
        hk_total['annual_growth'] = forecast_df['annual_growth'].mean()
        hk_total['r2_score'] = forecast_df['r2_score'].mean()
        
        forecast_df = pd.concat([forecast_df, pd.DataFrame([hk_total])], ignore_index=True)
        self.forecasts['elderly_2025_2030'] = forecast_df
        
        # Summary
        elderly_2024 = df['elderly_2024'].sum()
        elderly_2030 = hk_total[2030]
        growth = ((elderly_2030 / elderly_2024) - 1) * 100
        
        self.logger.success(f"  → HK elderly 2030: {elderly_2030:,} (+{growth:.1f}% from 2024)")
        
        # Top 5 districts by 2030
        top5 = forecast_df[forecast_df['District'] != 'Hong Kong Total'].nlargest(5, 2030)
        for _, row in top5.iterrows():
            self.logger.success(f"     - {row['District']}: {row[2030]:,}")
    
    def forecast_equipment_demand(self):
        """Forecast equipment demand based on elderly population"""
        
        self.logger.info("Forecasting equipment demand 2025-2030...")
        
        if 'elderly_2025_2030' not in self.forecasts:
            self.logger.warning("No elderly population forecast found")
            return
        
        elderly_forecast = self.forecasts['elderly_2025_2030']
        district_forecast = elderly_forecast[elderly_forecast['District'] != 'Hong Kong Total'].copy()
        
        demand_forecasts = []
        
        for year in FORECAST_YEARS:
            # Adoption increases each year
            year_factor = 1 + (ADOPTION_GROWTH_RATE * (year - 2024))
            
            for _, row in district_forecast.iterrows():
                district = row['District']
                elderly_pop = row[year]
                
                for category, base_rate in EQUIPMENT_ADOPTION_RATES.items():
                    adjusted_rate = base_rate * year_factor
                    estimated_demand = int(elderly_pop * adjusted_rate)
                    
                    if estimated_demand > 100:  # Only significant demand
                        demand_forecasts.append({
                            'District': district,
                            'Year': year,
                            'Equipment_Category': category,
                            'Elderly_Population': elderly_pop,
                            'Adoption_Rate': round(adjusted_rate, 3),
                            'Estimated_Demand': estimated_demand,
                            'Growth_vs_2024': f"{(year_factor - 1) * 100:.0f}%"
                        })
        
        self.forecasts['equipment_demand_2025_2030'] = pd.DataFrame(demand_forecasts)
        
        # Summary
        demand_2025 = self.forecasts['equipment_demand_2025_2030'][
            self.forecasts['equipment_demand_2025_2030']['Year'] == 2025
        ]
        demand_2030 = self.forecasts['equipment_demand_2025_2030'][
            self.forecasts['equipment_demand_2025_2030']['Year'] == 2030
        ]
        
        total_2025 = demand_2025['Estimated_Demand'].sum()
        total_2030 = demand_2030['Estimated_Demand'].sum()
        growth = ((total_2030 / total_2025) - 1) * 100
        
        self.logger.success(f"  → Total demand 2025: {total_2025:,} units")
        self.logger.success(f"  → Total demand 2030: {total_2030:,} units (+{growth:.1f}%)")
        
        # Top 5 district-category for 2025
        top5 = demand_2025.nlargest(5, 'Estimated_Demand')
        for _, row in top5.iterrows():
            self.logger.success(f"     - {row['District']}: {row['Equipment_Category']} - {row['Estimated_Demand']:,} units")
    
    def simulate_pandemic_scenario(self):
        """Simulate demand under pandemic conditions (2020 pattern)"""
        
        self.logger.info("Simulating pandemic scenario...")
        
        if 'equipment_demand_2025_2030' not in self.forecasts:
            self.logger.warning("No equipment demand forecast found")
            return
        
        base_forecast = self.forecasts['equipment_demand_2025_2030']
        base_2025 = base_forecast[base_forecast['Year'] == 2025].copy()
        
        pandemic_demand = []
        
        for _, row in base_2025.iterrows():
            category = row['Equipment_Category']
            multiplier = PANDEMIC_MULTIPLIERS.get(category, 1.0)
            
            pandemic_demand.append({
                'District': row['District'],
                'Equipment_Category': category,
                'Normal_Demand': row['Estimated_Demand'],
                'Pandemic_Demand': int(row['Estimated_Demand'] * multiplier),
                'Multiplier': multiplier,
                'Difference': int(row['Estimated_Demand'] * (multiplier - 1))
            })
        
        self.forecasts['pandemic_scenario'] = pd.DataFrame(pandemic_demand)
        
        # Summary
        resp_increase = self.forecasts['pandemic_scenario'][
            self.forecasts['pandemic_scenario']['Equipment_Category'] == 'Respiratory'
        ]['Difference'].sum()
        
        mobility_decrease = self.forecasts['pandemic_scenario'][
            self.forecasts['pandemic_scenario']['Equipment_Category'].isin(['Mobility - Wheelchairs', 'Mobility - Walkers'])
        ]['Difference'].sum()
        
        self.logger.success(f"  → Respiratory surge: +{resp_increase:,} units")
        self.logger.success(f"  → Mobility drop: {mobility_decrease:,} units")