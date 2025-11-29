Uber NYC 2015 – Exploratory Data Analysis

Author: Linda Mthembu
Tools: Python (Pandas, NumPy, Matplotlib, Seaborn, Plotly, Folium)

Project Overview

This project performs an end-to-end exploratory data analysis (EDA) on Uber trip data from New York City for the year 2015.
The objective is to identify patterns in ride demand, understand temporal usage trends, analyse geographic hotspots, and assess dispatch base activity.

The analysis follows a full data analytics lifecycle, starting from raw data loading to the creation of automated pivot tables and interactive visualisations.

Repository Structure
Uber-NYC-2015-Analysis/
│
├── data/                 # Raw dataset (excluded from GitHub due to size)
│
├── notebooks/
│   └── uber_analytics_analysis.ipynb
│
├── outputs/              # Plots and exported visualisations (ignored)
│
└── src/                  # Scripts for extensions and modular code

Skills Demonstrated

Loading and cleaning multi-file datasets

Handling corrupted CSV files and encoding issues

Data wrangling and feature engineering

Exploratory Data Analysis using Python

Static and interactive visualisation

Geospatial analysis using Folium

Automated pivot table generation

Version control using Git and GitHub

1. Data Loading and Preparation

The dataset originally contains over 15 million records. To ensure efficient processing, a curated sample of approximately one million rows was used.

Data cleaning steps included:

Dropping duplicate rows

Handling missing values

Parsing datetime fields

Extracting additional features such as month, weekday, hour, and minute

Example:

uber_15 = pd.read_csv(DATA_DIR / "uber-raw-data-janjune-15_sample.csv")
uber_15.shape

2. Exploratory Data Analysis
Monthly Demand

June showed the highest ride volume among the months analysed.

Weekday Demand

Friday and Saturday displayed the strongest demand, particularly during evening hours. Thursday evenings also exhibited behaviour similar to early weekend nights.

Hourly Demand

Peak usage typically occurred between 5 PM and 9 PM on most weekdays.

3. Geospatial Hotspot Analysis

Using Folium, a heatmap was created to visualise the geographic distribution of ride pickups.
High-density pickup areas included:

Midtown Manhattan

Lower Manhattan

Brooklyn Heights

Code used:

HeatMap(rush_uber[['Lat','Lon','size']].values).add_to(basemap)

4. Dispatch Base Activity (FOIL Dataset)

The FOIL dataset was analysed to understand operational patterns such as:

The variation in active vehicles per dispatch base

The distribution of fleet sizes

Interactive Plotly visualisations were used to explore these patterns.

Example:

px.violin(uber_foil, x='dispatching_base_number', y='active_vehicles')

5. Automated Pivot Table Generation

A reusable function was developed to automatically create pivot tables with heatmap formatting for any pair of time-based variables.

def gen_pivot_table(df, col1, col2):
    pivot = df.groupby([col1, col2]).size().unstack()
    return pivot.style.background_gradient(cmap="viridis")

Key Insights and Recommendations
Demand Insights

June had the highest overall activity.

Fridays and Saturdays consistently showed elevated trip volumes.

Evening hours represented the daily peak periods across most weekdays.

Geographic Insights

The majority of trips originated from central and high-traffic areas of Manhattan.

Tourist and commercial areas played a significant role in demand concentration.

Operational Recommendations

Increase driver availability during the early evening peak periods.

Prioritise fleet distribution around Midtown and Downtown Manhattan.

Conduct further analysis on dispatch base performance to improve fleet allocation.

How to Run the Project
Clone the repository
git clone https://github.com/deerealllinda/uber-nyc-2015-analysis.git

Install dependencies
pip install -r requirements.txt

Open the notebook
jupyter notebook notebooks/uber_analytics_analysis.ipynb

Data Availability

Large raw data files are excluded from the repository due to GitHub file size limits.
The dataset can be downloaded from public sources such as Kaggle, or the curated sample used in this project can be provided on request.

Contact

Linda Mthembu
Data Analyst | Python | Power BI | Machine Learning
Email: lindamthembu36@gmail.com

GitHub:https://github.com/deerealilinda

LinkedIn: www.linkedin.com/in/linda-mthembu-66b877270