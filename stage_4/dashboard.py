import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
import os

# Set Page Layout
st.set_page_config(page_title="Google Play Store Insights", layout="wide")

# Get the current working directory
current_directory = os.getcwd()

# Build the absolute path to the data.parquet file
data_file_path = os.path.join(current_directory, "data", "data.parquet")

# Display the absolute path (for debugging purposes)
st.write(f"Looking for the data file at: {data_file_path}")

# Load Data
@st.cache_data
def load_data():
    # Check if the file exists at the absolute path
    if os.path.exists(data_file_path):
        return pd.read_parquet(data_file_path)
    else:
        st.error(f"File not found at {data_file_path}")
        return None

df = load_data()

# Data Preprocessing
df['revenue'] = df['Installs'] * df['Price']

# Create economic zone columns if not present
if 'economic_zone' in df.columns:
    df = pd.get_dummies(df, columns=['economic_zone'])

zone_mapping = {
    'Developed': 'economic_zone_Developed',
    'Emerging': 'economic_zone_Emerging',
    'Frontier': 'economic_zone_Frontier',
    'Other': 'economic_zone_Other'
}

# Sidebar Filters
st.sidebar.header("Filters")
category_filter = st.sidebar.multiselect("Select Category", df["Category"].unique(), default=df["Category"].unique())
region_filter = st.sidebar.multiselect("Select Region", df["geo_region"].unique(), default=df["geo_region"].unique())
zone_options = ['Developed', 'Emerging', 'Frontier', 'Other']
zone_filter = st.sidebar.multiselect("Select Economic Zones", zone_options, default=zone_options)
date_range = st.sidebar.date_input("Select Date Range", [df['Released'].min().date(), df['Released'].max().date()])

zone_columns = [zone_mapping[z] for z in zone_filter if zone_mapping[z] in df.columns]

# Filter Data
df_filtered = df[
    (df['Category'].isin(category_filter)) &
    (df['geo_region'].isin(region_filter)) &
    (df[zone_columns].any(axis=1) if zone_columns else True) &
    (df['Released'].between(pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])))
]

# Helper: Format large numbers
def format_number(n):
    return f"{n:,.0f}"

# Main Dashboard Header
st.title("📊 Google Play Store Insights Dashboard")
st.markdown("Explore comprehensive insights into app performance across categories, regions, and economic zones.")

# KPIs Section
col1, col2, col3 = st.columns(3)

with col1:
    total_revenue = df_filtered['revenue'].sum()
    st.metric("💰 Total Revenue", f"${format_number(total_revenue)}")

with col2:
    total_installs = df_filtered['Installs'].sum()
    st.metric("📥 Total Installs", format_number(total_installs))

with col3:
    avg_rating = df_filtered['Rating'].mean()
    st.metric("⭐ Average Rating", f"{avg_rating:.2f}")

st.divider()

# Category Revenue Share
st.subheader("📊 Category Revenue Share")
category_revenue = df_filtered.groupby('Category')['revenue'].sum().reset_index()
fig_cat_rev = px.bar(category_revenue, x='revenue', y='Category', orientation='h', title="Revenue by Category")
st.plotly_chart(fig_cat_rev, use_container_width=True)

# Top Revenue Apps & Developers
col1, col2 = st.columns(2)

with col1:
    st.subheader("🌎 Top Revenue Apps by Region")
    top_apps_region = df_filtered.groupby(['geo_region', 'App Name'])['revenue'].sum().reset_index()
    top_apps_region = top_apps_region.sort_values(['geo_region', 'revenue'], ascending=[True, False])
    fig_top_apps = px.bar(top_apps_region, x='revenue', y='App Name', color='geo_region', orientation='h',
                          title="Top Revenue Apps by Region", height=600)
    st.plotly_chart(fig_top_apps, use_container_width=True)

with col2:
    st.subheader("👨‍💻 Top Developers by Revenue")
    top_devs = df_filtered.groupby('Developer Id')['revenue'].sum().nlargest(10).reset_index()
    fig_top_devs = px.bar(top_devs, x='revenue', y='Developer Id', orientation='h', title="Top 10 Developers by Revenue")
    st.plotly_chart(fig_top_devs, use_container_width=True)

# Economic Zone Revenue & Market Share
col1, col2 = st.columns(2)

with col1:
    st.subheader("🌍 Economic Zone Revenue Share")
    zone_revenue_cols = [col for col in df_filtered.columns if 'economic_zone_' in col]
    zone_revenue = df_filtered[zone_revenue_cols].sum().reset_index()
    zone_revenue.columns = ['Zone', 'Revenue']
    zone_revenue['Zone'] = zone_revenue['Zone'].str.replace('economic_zone_', '')
    fig_zone_share = px.bar(zone_revenue, x='Revenue', y='Zone', orientation='h', title="Revenue by Economic Zone")
    st.plotly_chart(fig_zone_share, use_container_width=True)

with col2:
    st.subheader("📈 Market Share by Geo-Region")
    market_share = df_filtered.groupby('geo_region')['revenue'].sum().reset_index()
    fig_market_share = px.bar(market_share, x='revenue', y='geo_region', orientation='h', title="Market Share by Geo-Region")
    st.plotly_chart(fig_market_share, use_container_width=True)

# Predictive Analytics KPIs
st.subheader("🔮 Predictive Analytics")

# 1. Forecasted Revenue Growth Rate
st.markdown("**📊 Forecasted Revenue Growth Rate**")
historical_revenue = df_filtered.groupby('Released')['revenue'].sum().reset_index()
historical_revenue['year'] = historical_revenue['Released'].dt.year
yearly_growth = historical_revenue.groupby('year')['revenue'].sum().pct_change().fillna(0) * 100
fig_forecast = px.line(yearly_growth.reset_index(), x='year', y='revenue', title="Forecasted Revenue Growth Rate")
st.plotly_chart(fig_forecast, use_container_width=True)

# 2. Market Expansion Opportunity Score
st.markdown("**🌟 Market Expansion Opportunity Score**")
opportunity_score = df_filtered.groupby(['geo_region', 'Category'])[['revenue', 'Installs']].sum().reset_index()
opportunity_score['score'] = (
    0.5 * opportunity_score['revenue'] + 0.5 * opportunity_score['Installs']
)
top_opportunities = opportunity_score.sort_values('score', ascending=False).head(10)
fig_opportunity = px.bar(top_opportunities, x='score', y='Category', color='geo_region',
                         orientation='h', title="Top Market Expansion Opportunities")
st.plotly_chart(fig_opportunity, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("© 2025 Google Play Store Insights | Built with ❤️ by Team G8")