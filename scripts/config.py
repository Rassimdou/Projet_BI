
import os
from pathlib import Path

# =============================================================================
# CHEMINS DU PROJET
# =============================================================================

# Racine du projet
PROJECT_ROOT = Path(__file__).parent.parent

# Dossiers du projet
DATA_PATH = PROJECT_ROOT / 'data'
SCRIPTS_PATH = PROJECT_ROOT / 'scripts'
REPORTS_PATH = PROJECT_ROOT / 'reports'
FIGURES_PATH = PROJECT_ROOT / 'figures'
NOTEBOOKS_PATH = PROJECT_ROOT / 'notebooks'

# Créer les dossiers s'ils n'existent pas
for path in [DATA_PATH, SCRIPTS_PATH, REPORTS_PATH, FIGURES_PATH, NOTEBOOKS_PATH]:
    path.mkdir(exist_ok=True)

# =============================================================================
# CONFIGURATION SQL SERVER
# =============================================================================

SQL_SERVER_CONFIG = {
    'server': 'localhost',  # Modifier selon votre configuration
    # Exemples: 'localhost', 'localhost\\SQLEXPRESS', '127.0.0.1'
    'database': 'Northwind',
    'driver': '{ODBC Driver 17 for SQL Server}',
    # Pour l'authentification Windows
    'trusted_connection': 'yes',
    # Pour l'authentification SQL Server (laisser vide si Windows Auth)
    'username': '',
    'password': ''
}

# =============================================================================
# CONFIGURATION ACCESS DATABASE
# =============================================================================

ACCESS_DB_CONFIG = {
    'database_path': r'D:\Projet_Bi\data\Northwind 2012.accdb',  # Modifier selon l'emplacement de votre fichier Access
    # Alternatives possibles:
    # - Pour Access 2007-2019: .accdb
    # - Pour Access 97-2003: .mdb
    'driver': '{Microsoft Access Driver (*.mdb, *.accdb)}',
    # Si le driver ci-dessus ne fonctionne pas, essayez:
    # '{Microsoft Access Driver (*.mdb)}' pour les anciens fichiers
}

# =============================================================================
# CONFIGURATION VISUALISATION
# =============================================================================

# Palette de couleurs pour les graphiques
COLOR_PALETTE = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'success': '#F18F01',
    'info': '#C73E1D',
    'warning': '#3B1F2B',
    'colors': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B', 
               '#5C946E', '#80C4B7', '#E8D5B7', '#0E7C7B', '#D64933']
}

# Configuration des graphiques
CHART_CONFIG = {
    'figure_size': (12, 6),
    'dpi': 100,
    'style': 'seaborn-v0_8-whitegrid',
    'font_size': 10,
    'title_size': 14
}

# =============================================================================
# CONFIGURATION DES FICHIERS DE SORTIE
# =============================================================================

OUTPUT_FILES = {
    'csv_encoding': 'utf-8-sig',
    'excel_engine': 'openpyxl',
    'date_format': '%Y-%m-%d'
}

# =============================================================================
# INDICATEURS CLÉS (KPIs)
# =============================================================================

KPI_DEFINITIONS = {
    'total_revenue': 'Chiffre d\'affaires total',
    'total_orders': 'Nombre total de commandes',
    'avg_order_value': 'Valeur moyenne des commandes',
    'total_customers': 'Nombre de clients',
    'total_products': 'Nombre de produits',
    'top_country': 'Pays avec le plus de ventes'
}
