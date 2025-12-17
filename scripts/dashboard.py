
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_PATH = '../data/'
FIGURES_PATH = '../figures/'

# Créer le dossier figures si nécessaire
os.makedirs(FIGURES_PATH, exist_ok=True)

# =============================================================================
# CHARGEMENT DES DONNÉES
# =============================================================================

def load_data():
    """Charger les données depuis les fichiers CSV"""
    data = {}
    
    files = [
        'Fact_Sales', 'Dim_Customers', 'Dim_Products', 'Dim_Employees',
        'Sales_By_Month', 'Sales_By_Category', 'Sales_By_Country', 'Top_Products'
    ]
    
    for file in files:
        filepath = f'{DATA_PATH}{file}.csv'
        if os.path.exists(filepath):
            data[file] = pd.read_csv(filepath)
            print(f"✅ {file} chargé: {len(data[file])} lignes")
        else:
            print(f"⚠️ {file} non trouvé")
            data[file] = pd.DataFrame()
    
    # Convertir les dates
    if not data['Fact_Sales'].empty:
        data['Fact_Sales']['OrderDate'] = pd.to_datetime(data['Fact_Sales']['OrderDate'])
    
    return data

# =============================================================================
# CALCUL DES KPIs
# =============================================================================

def calculate_kpis(data):
    """Calculer les indicateurs clés"""
    fact_sales = data['Fact_Sales']
    
    if fact_sales.empty:
        return {}
    
    kpis = {
        'total_revenue': fact_sales['TotalAmount'].sum(),
        'total_orders': fact_sales['OrderID'].nunique(),
        'avg_order_value': fact_sales['TotalAmount'].sum() / fact_sales['OrderID'].nunique(),
        'total_quantity': fact_sales['Quantity'].sum(),
        'total_customers': fact_sales['CustomerID'].nunique(),
        'total_products': fact_sales['ProductID'].nunique()
    }
    
    return kpis

# =============================================================================
# CRÉATION DES GRAPHIQUES
# =============================================================================

def create_kpi_cards(kpis):
    """Créer les cartes KPI"""
    fig = make_subplots(
        rows=2, cols=3,
        specs=[[{'type': 'indicator'}]*3, [{'type': 'indicator'}]*3]
    )
    
    indicators = [
        ('💰 Chiffre d\'affaires', kpis.get('total_revenue', 0), '$', ',.0f'),
        ('📋 Commandes', kpis.get('total_orders', 0), '', ','),
        ('💵 Panier moyen', kpis.get('avg_order_value', 0), '$', ',.2f'),
        ('📦 Quantité vendue', kpis.get('total_quantity', 0), '', ','),
        ('👥 Clients actifs', kpis.get('total_customers', 0), '', ','),
        ('🛒 Produits vendus', kpis.get('total_products', 0), '', ',')
    ]
    
    positions = [(1,1), (1,2), (1,3), (2,1), (2,2), (2,3)]
    
    for (title, value, prefix, fmt), (row, col) in zip(indicators, positions):
        fig.add_trace(
            go.Indicator(
                mode='number',
                value=value,
                title={'text': title, 'font': {'size': 14}},
                number={'prefix': prefix, 'valueformat': fmt, 'font': {'size': 28}}
            ),
            row=row, col=col
        )
    
    fig.update_layout(
        title_text='📊 Indicateurs Clés de Performance (KPIs)',
        height=400,
        template='plotly_white'
    )
    
    return fig

def create_sales_trend(data):
    """Créer le graphique d'évolution des ventes"""
    fact_sales = data['Fact_Sales']
    
    if fact_sales.empty:
        return go.Figure()
    
    monthly_sales = fact_sales.groupby(
        fact_sales['OrderDate'].dt.to_period('M')
    )['TotalAmount'].sum().reset_index()
    monthly_sales['OrderDate'] = monthly_sales['OrderDate'].astype(str)
    
    fig = px.area(
        monthly_sales,
        x='OrderDate',
        y='TotalAmount',
        title='📈 Évolution mensuelle du chiffre d\'affaires',
        labels={'OrderDate': 'Période', 'TotalAmount': 'Ventes ($)'}
    )
    
    fig.update_layout(template='plotly_white')
    return fig

def create_category_chart(data):
    """Créer le graphique des ventes par catégorie"""
    sales_by_category = data['Sales_By_Category']
    
    if sales_by_category.empty:
        return go.Figure()
    
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'pie'}, {'type': 'bar'}]],
        subplot_titles=('Répartition (%)', 'Montant ($)')
    )
    
    # Pie chart
    fig.add_trace(
        go.Pie(
            labels=sales_by_category['CategoryName'],
            values=sales_by_category['TotalSales'],
            hole=0.4,
            textinfo='percent+label',
            textposition='outside'
        ),
        row=1, col=1
    )
    
    # Bar chart
    sorted_data = sales_by_category.sort_values('TotalSales', ascending=True)
    fig.add_trace(
        go.Bar(
            x=sorted_data['TotalSales'],
            y=sorted_data['CategoryName'],
            orientation='h',
            marker_color='steelblue',
            text=[f'${x:,.0f}' for x in sorted_data['TotalSales']],
            textposition='outside'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title_text='📦 Ventes par catégorie de produits',
        height=500,
        showlegend=False,
        template='plotly_white'
    )
    
    return fig

def create_country_chart(data):
    """Créer le graphique des ventes par pays"""
    sales_by_country = data['Sales_By_Country']
    
    if sales_by_country.empty:
        return go.Figure()
    
    # Top 10 pays
    top_countries = sales_by_country.nlargest(10, 'TotalSales')
    
    fig = px.bar(
        top_countries,
        x='Country',
        y='TotalSales',
        color='TotalSales',
        color_continuous_scale='Viridis',
        title='🌍 Top 10 pays par chiffre d\'affaires',
        labels={'Country': 'Pays', 'TotalSales': 'Ventes ($)'}
    )
    
    fig.update_layout(
        template='plotly_white',
        xaxis_tickangle=-45
    )
    
    return fig

def create_world_map(data):
    """Créer la carte mondiale des ventes"""
    sales_by_country = data['Sales_By_Country']
    
    if sales_by_country.empty:
        return go.Figure()
    
    fig = px.choropleth(
        sales_by_country,
        locations='Country',
        locationmode='country names',
        color='TotalSales',
        color_continuous_scale='Blues',
        title='🗺️ Carte mondiale des ventes',
        labels={'TotalSales': 'Ventes ($)'}
    )
    
    fig.update_layout(template='plotly_white')
    return fig

def create_top_products_chart(data):
    """Créer le graphique des top produits"""
    top_products = data['Top_Products']
    
    if top_products.empty:
        return go.Figure()
    
    sorted_data = top_products.sort_values('TotalAmount', ascending=True)
    
    fig = px.bar(
        sorted_data,
        x='TotalAmount',
        y='ProductName',
        orientation='h',
        color='TotalAmount',
        color_continuous_scale='Greens',
        title='🏆 Top 10 produits par chiffre d\'affaires',
        labels={'TotalAmount': 'Ventes ($)', 'ProductName': 'Produit'}
    )
    
    fig.update_layout(template='plotly_white', height=500)
    return fig

def create_complete_dashboard(data, kpis):
    """Créer le tableau de bord complet"""
    fig = make_subplots(
        rows=4, cols=2,
        specs=[
            [{'type': 'indicator'}, {'type': 'indicator'}],
            [{'type': 'indicator'}, {'type': 'indicator'}],
            [{'type': 'bar', 'colspan': 2}, None],
            [{'type': 'pie'}, {'type': 'bar'}]
        ],
        subplot_titles=(
            '', '', '', '',
            'Évolution des ventes mensuelles',
            'Répartition par catégorie', 'Ventes par catégorie'
        ),
        row_heights=[0.15, 0.15, 0.35, 0.35]
    )
    
    # KPIs
    kpi_list = [
        ('💰 CA Total', kpis.get('total_revenue', 0), '$', ',.0f'),
        ('📋 Commandes', kpis.get('total_orders', 0), '', ','),
        ('💵 Panier moyen', kpis.get('avg_order_value', 0), '$', ',.2f'),
        ('👥 Clients', kpis.get('total_customers', 0), '', ',')
    ]
    
    positions = [(1,1), (1,2), (2,1), (2,2)]
    
    for (title, value, prefix, fmt), (row, col) in zip(kpi_list, positions):
        fig.add_trace(
            go.Indicator(
                mode='number',
                value=value,
                title={'text': title},
                number={'prefix': prefix, 'valueformat': fmt}
            ),
            row=row, col=col
        )
    
    # Evolution mensuelle
    fact_sales = data['Fact_Sales']
    if not fact_sales.empty:
        monthly = fact_sales.groupby(
            fact_sales['OrderDate'].dt.to_period('M')
        )['TotalAmount'].sum().reset_index()
        monthly['OrderDate'] = monthly['OrderDate'].astype(str)
        
        fig.add_trace(
            go.Bar(x=monthly['OrderDate'], y=monthly['TotalAmount'], 
                   marker_color='steelblue'),
            row=3, col=1
        )
    
    # Catégories
    sales_cat = data['Sales_By_Category']
    if not sales_cat.empty:
        fig.add_trace(
            go.Pie(labels=sales_cat['CategoryName'], values=sales_cat['TotalSales'],
                   hole=0.4),
            row=4, col=1
        )
        
        sorted_cat = sales_cat.sort_values('TotalSales', ascending=True)
        fig.add_trace(
            go.Bar(x=sorted_cat['TotalSales'], y=sorted_cat['CategoryName'],
                   orientation='h', marker_color='coral'),
            row=4, col=2
        )
    
    fig.update_layout(
        title_text='📊 TABLEAU DE BORD BI - NORTHWIND',
        height=1200,
        showlegend=False,
        template='plotly_white'
    )
    
    return fig

# =============================================================================
# EXPORT DES GRAPHIQUES
# =============================================================================

def save_figures(data, kpis):
    """Sauvegarder tous les graphiques en images HTML"""
    
    print("\n📊 Génération des graphiques...")
    
    # KPIs
    fig_kpis = create_kpi_cards(kpis)
    fig_kpis.write_html(f'{FIGURES_PATH}kpis.html')
    print("✅ kpis.html sauvegardé")
    
    # Evolution des ventes
    fig_trend = create_sales_trend(data)
    fig_trend.write_html(f'{FIGURES_PATH}sales_trend.html')
    print("✅ sales_trend.html sauvegardé")
    
    # Catégories
    fig_cat = create_category_chart(data)
    fig_cat.write_html(f'{FIGURES_PATH}categories.html')
    print("✅ categories.html sauvegardé")
    
    # Pays
    fig_country = create_country_chart(data)
    fig_country.write_html(f'{FIGURES_PATH}countries.html')
    print("✅ countries.html sauvegardé")
    
    # Carte mondiale
    fig_map = create_world_map(data)
    fig_map.write_html(f'{FIGURES_PATH}world_map.html')
    print("✅ world_map.html sauvegardé")
    
    # Top produits
    fig_products = create_top_products_chart(data)
    fig_products.write_html(f'{FIGURES_PATH}top_products.html')
    print("✅ top_products.html sauvegardé")
    
    # Dashboard complet
    fig_dashboard = create_complete_dashboard(data, kpis)
    fig_dashboard.write_html(f'{FIGURES_PATH}dashboard_complet.html')
    print("✅ dashboard_complet.html sauvegardé")
    
    print(f"\n📁 Tous les graphiques ont été sauvegardés dans {FIGURES_PATH}")

# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║         DASHBOARD BI - NORTHWIND Analytics                    ║
    ║                    Projet BI 2025                             ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Charger les données
    print("📂 Chargement des données...")
    data = load_data()
    
    # Calculer les KPIs
    print("\n📈 Calcul des KPIs...")
    kpis = calculate_kpis(data)
    
    if kpis:
        print(f"\n💰 CA Total: ${kpis['total_revenue']:,.2f}")
        print(f"📋 Commandes: {kpis['total_orders']:,}")
        print(f"💵 Panier moyen: ${kpis['avg_order_value']:,.2f}")
        print(f"👥 Clients: {kpis['total_customers']:,}")
    
    # Générer et sauvegarder les graphiques
    save_figures(data, kpis)
    
    print("\n✅ Dashboard généré avec succès!")
    print("📁 Ouvrez les fichiers HTML dans le dossier 'figures/' pour visualiser")
