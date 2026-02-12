# IoT-Data-Hackathon-2026-TBC

# 🏥 Gerontech Demand Forecasting & Service Gap Analysis
### IOT Data Hackathon 2026 - Challenge 5

---

## 📌 What This Project Does

This project analyzes Hong Kong's aging population and gerontech equipment rental demand to help the **Jockey Club "age at home" Gerontech Education and Rental Service** optimize their service delivery.

### 🎯 Core Objectives:
| Objective | What We Do |
|-----------|------------|
| **Find Service Gaps** | Identify districts with high elderly population but low service penetration |
| **Forecast Demand** | Predict equipment needs by district for 2025-2030 |
| **Map Diseases to Equipment** | Link top diseases to specific gerontech products |
| **Create User Personas** | Define 6 distinct user types with pain points |
| **Optimize Inventory** | Recommend what equipment to stock, where, and when |
| **Pandemic Planning** | Simulate COVID-style demand surges |

---

## 📂 Project Structure
IoT-Data-Hackathon-2026-TBC/  
|  
├── main.py # 🎮 RUN THIS FILE - executes everything  
├── config.py # ⚙️ Settings and parameters  
├── data_reader.py # 📖 Step 1: Reads all CSV/Excel files  
├── data_cleaner.py # 🧹 Step 2: Cleans and standardizes data  
├── analyst.py # 🔍 Step 3: Finds service gaps, maps diseases  
├── forecaster.py # 📈 Step 4: Predicts population & demand  
├── strategist.py # 💡 Step 5: Generates recommendations  
├── visualizer.py # 🎨 Step 6: Creates charts and graphs  
├── utils.py # 🛠️ Helper functions  
├── requirements.txt # 📦 Python dependencies  
├── README.md # 📖 This file  
│  
├── data/  
│  
├── outputs/ # 📊 ALL RESULTS SAVED HERE  
│ ├── forecasts/  
│ ├── insights/  
│ ├── recommendations/  
│ ├── visualizations/  
│ └── cleaned/  
│  
└── venv/ # ⚠️ Virtual environment (do not upload)  


---

## 🚀 How to Run the Code

### Step 1: Install Python
```
python --version  # Requires Python 3.8+
```

### Step 2: Download the Code
```
git clone https://github.com/YOUR_USERNAME/IoT-Data-Hackathon-2026-TBC.git
cd IoT-Data-Hackathon-2026-TBC
```

### Step 3: Set Up Virtual Environment
```
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install Dependencies
```
pip install --upgrade pip

pip install -r requirements.txt
OR
pip install pandas numpy matplotlib seaborn scikit-learn openpyxl
```

### Step 5: RUN THE ANALYSIS
```
python main.py
```

That's it! The script will automatically:  
✅ Read all your data files  
✅ Clean and process the data  
✅ Identify service gaps and underserved districts  
✅ Forecast elderly population 2025-2030  
✅ Predict equipment demand by district  
✅ Generate outreach and inventory recommendations  
✅ Create visualization charts  

**📊 Output Files**

**After running, check the outputs/ folder:**

**📈 Forecasts (outputs/forecasts/)**

|File|Description|
|-----------|------------|
|**forecast_elderly_2025_2030.csv**|Elderly population by district 2025-2030|
|**forecast_equipment_demand_2025_2030.csv**|Equipment demand by district and category|
|**forecast_pandemic_scenario.csv**|COVID-19 scenario simulation|


**🔍 Insights (outputs/insights/)**

|File|Description|
|-----------|------------|
|**insights_service_gaps.csv** |Underserved districts with priority scores|
|**insights_top5_diseases.csv**	|Top causes of death and needed equipment|
|**insights_user_personas.csv**	|6 user personas with pain points|
|**insights_disease_equipment_map.csv** |Disease → equipment mapping matrix|
|**insights_overlooked_conditions.csv**	|Non-fatal but disabling conditions|


**💡 Recommendations (outputs/recommendations/)**

|File|Description|
|-----------|------------|
|**recommendations_expansion_priorities.csv**	|Top 5 districts for service expansion|
|**recommendations_inventory_priorities.csv**	|Equipment stocking priorities by district|
|**recommendations_outreach_plan.csv** |Targeted outreach strategies|


**🎨 Visualizations (outputs/visualizations/)**

|File|Description|
|-----------|------------|
|**aging_trend.png**	|HK elderly population 2019-2030|
|**service_gaps.png**	|Top 10 underserved districts|
|**demand_forecast.png** |Equipment demand by category 2025-2030|
