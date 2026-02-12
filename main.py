"""
MAIN ORCHESTRATION SCRIPT
Run the entire analysis pipeline
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import *
from utils import Logger
from data_reader import DataReader
from data_cleaner import DataCleaner
from analyst import Analyst
from forecaster import Forecaster
from strategist import Strategist
from visualizer import Visualizer

def main():
    """Run complete analysis pipeline"""
    
    logger = Logger()
    
    logger.section("IOT HACKATHON 2026 - CHALLENGE 5")
    logger.info("Gerontech Demand Forecasting & Service Gap Analysis")
    
    # STEP 1: READ
    logger.info("\n📂 Step 1: Reading data...")
    reader = DataReader()
    raw_data = reader.read_all()
    
    # STEP 2: CLEAN
    logger.info("\n🧹 Step 2: Cleaning data...")
    cleaner = DataCleaner(raw_data)
    cleaned = cleaner.clean_all()
    
    # STEP 3: ANALYSE
    logger.info("\n🔍 Step 3: Analysing data...")
    analyst = Analyst(cleaned)
    insights = analyst.analyse_all()
    
    # STEP 4: PREDICT
    logger.info("\n📈 Step 4: Forecasting...")
    forecaster = Forecaster(cleaned, insights)
    forecasts = forecaster.forecast_all()
    
    # STEP 5: RECOMMEND
    logger.info("\n💡 Step 5: Generating recommendations...")
    strategist = Strategist(cleaned, insights, forecasts)
    recommendations = strategist.generate_all()
    
    # STEP 6: VISUALIZE
    logger.info("\n🎨 Step 6: Creating visualizations...")
    visualizer = Visualizer(cleaned, insights, forecasts, recommendations)
    visualizer.create_all()
    
    # FINAL SUMMARY
    logger.section("ANALYSIS COMPLETE")
    
    elderly_2024 = cleaned['elderly_population']['elderly_2024'].sum()
    elderly_2030 = forecasts['elderly_2025_2030'][
        forecasts['elderly_2025_2030']['District'] == 'Hong Kong Total'
    ][2030].values[0]
    
    logger.success(f"📊 Elderly Population: {elderly_2024:,} (2024) → {elderly_2030:,} (2030)")
    
    if 'service_gaps' in insights:
        top_gap = insights['service_gaps'].iloc[0]['District']
        logger.success(f"📍 Top Priority District: {top_gap}")
    
    if 'top5_diseases' in insights:
        top_disease = insights['top5_diseases'].iloc[0]['Disease']
        logger.success(f"🏥 Top Disease: {top_disease}")
    
    if 'equipment_demand_2025_2030' in forecasts:
        demand_2025 = forecasts['equipment_demand_2025_2030'][
            forecasts['equipment_demand_2025_2030']['Year'] == 2025
        ]['Estimated_Demand'].sum()
        logger.success(f"📦 Equipment Demand 2025: {demand_2025:,.0f} units")
    
    logger.success(f"\n✅ All outputs saved to: {OUTPUT_DIR}")
    logger.info(logger.execution_time())
    
    return {
        'raw': raw_data,
        'cleaned': cleaned,
        'insights': insights,
        'forecasts': forecasts,
        'recommendations': recommendations
    }

if __name__ == "__main__":
    results = main()