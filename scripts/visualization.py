import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create figures directory if it doesn't exist
if not os.path.exists('../figures'):
    os.makedirs('../figures')

print("Loading data...")
# Load Data
try:
    df_sales = pd.read_csv('../data/Fact_Sales.csv')
    df_customers = pd.read_csv('../data/Dim_Customers.csv')
    df_products = pd.read_csv('../data/Dim_Products.csv')
    
    # Load Access Data
    df_access_orders = pd.read_csv('../data/access_Orders.csv')
    
    print("Data loaded successfully.")
    
    # Set style
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    # 1. Sales Distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(df_sales['TotalAmount'], bins=50, kde=True)
    plt.title('Distribution of Sales Amounts (SQL Server)')
    plt.xlabel('Amount ($)')
    plt.savefig('../figures/sales_distribution.png')
    print("Generated sales_distribution.png")
    
    # 2. Top Countries
    plt.figure(figsize=(12, 6))
    country_counts = df_customers['Country'].value_counts().head(10)
    sns.barplot(x=country_counts.values, y=country_counts.index)
    plt.title('Top 10 Countries by Customer Count')
    plt.savefig('../figures/top_countries.png')
    print("Generated top_countries.png")
    
    # 3. Access Orders Status
    plt.figure(figsize=(8, 8))
    status_counts = df_access_orders['Status ID'].value_counts()
    plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%')
    plt.title('Access Orders Status Distribution')
    plt.savefig('../figures/access_order_status.png')
    print("Generated access_order_status.png")
    
    print("All figures generated in /figures folder.")

except Exception as e:
    print(f"Error: {e}")
