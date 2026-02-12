"""
STEP 6: Create visualizations
"""
import matplotlib.pyplot as plt
import seaborn as sns
from config import *
from utils import Logger, save_output

class Visualizer:
    """Create all visualizations"""
    
    def __init__(self, cleaned_data, insights, forecasts, recommendations):
        self.data = cleaned_data
        self.insights = insights
        self.forecasts = forecasts
        self.recommendations = recommendations
        self.logger = Logger()
        
    def create_all(self):
        """Create all visualizations"""
        
        self.logger.section("STEP 6: CREATING VISUALIZATIONS")
        
        self.plot_aging_trend()
        self.plot_service_gaps()
        self.plot_demand_forecast()
        
        self.logger.success("Visualizations complete")
    
    def plot_aging_trend(self):
        """Plot elderly population trend 2019-2030"""
        
        if 'elderly_population' not in self.data:
            return
        
        if 'elderly_2025_2030' not in self.forecasts:
            return
        
        plt.figure(figsize=(12, 6))
        
        # Historical
        historical = self.data['elderly_population']
        hk_historical = [
            historical['elderly_2019'].sum(),
            historical['elderly_2020'].sum(),
            historical['elderly_2021'].sum(),
            historical['elderly_2022'].sum(),
            historical['elderly_2023'].sum(),
            historical['elderly_2024'].sum()
        ]
        
        # Forecast
        forecast = self.forecasts['elderly_2025_2030']
        hk_forecast = forecast[forecast['District'] == 'Hong Kong Total'].iloc[0]
        hk_forecast_values = [hk_forecast[year] for year in FORECAST_YEARS]
        
        # Plot
        years_hist = [2019, 2020, 2021, 2022, 2023, 2024]
        years_forecast = FORECAST_YEARS
        
        plt.plot(years_hist, hk_historical, 'o-', linewidth=2, markersize=8, label='Historical', color='#3498db')
        plt.plot(years_forecast, hk_forecast_values, 'o--', linewidth=2, markersize=8, label='Forecast', color='#e74c3c')
        
        plt.fill_between(years_forecast, 
                        [v * 0.95 for v in hk_forecast_values],
                        [v * 1.05 for v in hk_forecast_values],
                        alpha=0.2, color='#e74c3c')
        
        plt.xlabel('Year')
        plt.ylabel('Elderly Population (65+)')
        plt.title('Hong Kong Aging Population Trend 2019-2030', fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        save_path = VIZ_DIR / 'aging_trend.png'
        plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close()
        
        self.logger.success(f"  → Saved: aging_trend.png")
    
    def plot_service_gaps(self):
        """Plot service gap analysis"""
        
        if 'service_gaps' not in self.insights:
            return
        
        df = self.insights['service_gaps'].head(10)
        
        plt.figure(figsize=(10, 6))
        
        colors = ['#e74c3c' if x == 'Underserved' else '#2ecc71' for x in df['gap_status']]
        
        plt.barh(range(len(df)), df['service_gap'], color=colors)
        plt.yticks(range(len(df)), df['District'])
        plt.xlabel('Service Gap Score (Higher = More Underserved)')
        plt.title('Top 10 Districts by Service Gap', fontsize=14, fontweight='bold')
        
        save_path = VIZ_DIR / 'service_gaps.png'
        plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close()
        
        self.logger.success(f"  → Saved: service_gaps.png")
    
    def plot_demand_forecast(self):
        """Plot equipment demand forecast"""
        
        if 'equipment_demand_2025_2030' not in self.forecasts:
            return
        
        df = self.forecasts['equipment_demand_2025_2030']
        
        # Aggregate by year and category
        yearly = df.groupby(['Year', 'Equipment_Category'])['Estimated_Demand'].sum().reset_index()
        
        plt.figure(figsize=(14, 6))
        
        for category in yearly['Equipment_Category'].unique()[:5]:
            cat_data = yearly[yearly['Equipment_Category'] == category]
            plt.plot(cat_data['Year'], cat_data['Estimated_Demand'], 'o-', linewidth=2, label=category)
        
        plt.xlabel('Year')
        plt.ylabel('Estimated Demand (Units)')
        plt.title('Equipment Demand Forecast 2025-2030', fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        save_path = VIZ_DIR / 'demand_forecast.png'
        plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close()
        
        self.logger.success(f"  → Saved: demand_forecast.png")