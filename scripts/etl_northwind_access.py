import pyodbc
import pandas as pd
import numpy as np
from datetime import datetime
import os
from pathlib import Path
import logging
import sys
from config import DATA_PATH, REPORTS_PATH, ACCESS_DB_CONFIG

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(REPORTS_PATH / 'etl_access_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ],
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Fixer l'encodage de la console Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace') 

# =============================================================================
# ETL POUR ACCESS DATABASE
# =============================================================================

class NorthwindAccessETL:
    """Classe ETL pour Northwind Access Database"""
    
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.data = {}
        self.output_path = DATA_PATH

    def connect(self):
        """Établir la connexion à Access Database"""
        try:
            db_path = self.config['database_path']
            
            # Vérifier si le fichier existe
            if not os.path.exists(db_path):
                logger.error(f"❌ Fichier Access introuvable: {db_path}")
                logger.info("💡 Veuillez placer votre fichier Northwind.accdb dans le dossier data/")
                return False
            
            # Construire la chaîne de connexion pour Access
            conn_string = (
                f"DRIVER={self.config['driver']};"
                f"DBQ={db_path};"
            )
            
            self.connection = pyodbc.connect(conn_string)
            logger.info(f"✅ Connexion à Access établie: {db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur de connexion Access: {e}")
            logger.info("💡 Assurez-vous que:")
            logger.info("   1. Le driver Microsoft Access est installé")
            logger.info("   2. Le chemin du fichier est correct dans config.py")
            logger.info("   3. Le fichier n'est pas ouvert dans Access")
            return False
    
    def list_tables(self):
        """Lister toutes les tables disponibles dans la base Access"""
        try:
            cursor = self.connection.cursor()
            tables = []
            for table_info in cursor.tables(tableType='TABLE'):
                table_name = table_info.table_name
                # Filtrer les tables système
                if not table_name.startswith('MSys') and not table_name.startswith('~'):
                    tables.append(table_name)
            logger.info(f"📋 Tables trouvées: {', '.join(tables)}")
            return tables
        except Exception as e:
            logger.error(f"❌ Erreur lors de la liste des tables: {e}")
            return []
    
    def extract_table(self, table_name, query=None):
        """Extraire les données d'une table Access"""
        try:
            if query is None:
                query = f"SELECT * FROM [{table_name}]"
            
            df = pd.read_sql(query, self.connection)
            logger.info(f"✅ Table '{table_name}' extraite: {len(df)} lignes")
            return df
        except Exception as e:
            logger.error(f"❌ Erreur extraction '{table_name}': {e}")
            return pd.DataFrame()
    
    def extract_all(self):
        """Extraire toutes les tables principales de Northwind Access"""
        logger.info("=" * 50)
        logger.info("DÉBUT DE L'EXTRACTION (ACCESS)")
        logger.info("=" * 50)
        
        # Lister les tables disponibles
        available_tables = self.list_tables()
        
        # Tables principales de Northwind (noms standards)
        standard_tables = [
            'Categories',
            'Customers',
            'Employees',
            'Orders',
            'Order Details',
            'Products',
            'Shippers',
            'Suppliers',
            'Region',
            'Territories'
        ]
        
        # Extraire chaque table si elle existe
        for table in standard_tables:
            if table in available_tables:
                safe_name = table.replace(' ', '')
                self.data[safe_name] = self.extract_table(table)
            else:
                logger.warning(f"⚠️ Table '{table}' non trouvée dans la base Access")
        
        logger.info(f"✅ Extraction terminée: {len(self.data)} tables")
        return self.data

    # =============================================================================
    # TRANSFORMATION (Identique à la version SQL Server)
    # =============================================================================
    
    def transform(self):
        """Appliquer les transformations aux données"""
        logger.info("=" * 50)
        logger.info("DÉBUT DES TRANSFORMATIONS")
        logger.info("=" * 50)
        
        # 1. Créer la table de faits des ventes
        self.create_fact_sales()
        
        # 2. Créer les dimensions
        self.create_dim_customers()
        self.create_dim_products()
        self.create_dim_employees()
        self.create_dim_time()
        
        # 3. Calculs agrégés
        self.create_sales_summary()
        
        logger.info("✅ Transformations terminées")
    
    def create_fact_sales(self):
        """Créer la table de faits des ventes"""
        logger.info("Création de Fact_Sales...")
        
        orders = self.data.get('Orders', pd.DataFrame())
        order_details = self.data.get('OrderDetails', pd.DataFrame())
        
        if orders.empty or order_details.empty:
            logger.warning("⚠️ Données manquantes pour Fact_Sales")
            return
        
        # Jointure Orders et Order Details
        fact_sales = pd.merge(
            order_details,
            orders,
            on='OrderID',
            how='left'
        )
        
        # Calcul du montant total par ligne
        fact_sales['TotalAmount'] = (
            fact_sales['UnitPrice'] * 
            fact_sales['Quantity'] * 
            (1 - fact_sales['Discount'])
        )
        
        # Arrondir les montants
        fact_sales['TotalAmount'] = fact_sales['TotalAmount'].round(2)
        
        # Conversion des dates
        if 'OrderDate' in fact_sales.columns:
            fact_sales['OrderDate'] = pd.to_datetime(fact_sales['OrderDate'])
            fact_sales['Year'] = fact_sales['OrderDate'].dt.year
            fact_sales['Month'] = fact_sales['OrderDate'].dt.month
            fact_sales['Quarter'] = fact_sales['OrderDate'].dt.quarter
            fact_sales['DayOfWeek'] = fact_sales['OrderDate'].dt.dayofweek
        
        self.data['Fact_Sales'] = fact_sales
        logger.info(f"✅ Fact_Sales créée: {len(fact_sales)} lignes")
    
    def create_dim_customers(self):
        """Créer la dimension Clients"""
        logger.info("Création de Dim_Customers...")
        
        customers = self.data.get('Customers', pd.DataFrame()).copy()
        
        if customers.empty:
            return
        
        # Nettoyage des données
        customers['ContactName'] = customers['ContactName'].fillna('Non spécifié')
        customers['Country'] = customers['Country'].fillna('Non spécifié')
        customers['City'] = customers['City'].fillna('Non spécifié')
        
        # Segmentation des clients par région
        customers['Region_Group'] = customers['Country'].apply(self.categorize_region)
        
        self.data['Dim_Customers'] = customers
        logger.info(f"✅ Dim_Customers créée: {len(customers)} lignes")
    
    def create_dim_products(self):
        """Créer la dimension Produits"""
        logger.info("Création de Dim_Products...")
        
        products = self.data.get('Products', pd.DataFrame()).copy()
        categories = self.data.get('Categories', pd.DataFrame())
        suppliers = self.data.get('Suppliers', pd.DataFrame())
        
        if products.empty:
            return
        
        # Jointure avec Categories
        if not categories.empty:
            products = pd.merge(
                products,
                categories[['CategoryID', 'CategoryName', 'Description']],
                on='CategoryID',
                how='left',
                suffixes=('', '_Category')
            )
        
        # Jointure avec Suppliers
        if not suppliers.empty:
            products = pd.merge(
                products,
                suppliers[['SupplierID', 'CompanyName', 'Country']],
                on='SupplierID',
                how='left',
                suffixes=('', '_Supplier')
            )
            products.rename(columns={
                'CompanyName': 'SupplierName',
                'Country': 'SupplierCountry'
            }, inplace=True)
        
        # Catégorisation par prix
        products['PriceCategory'] = pd.cut(
            products['UnitPrice'],
            bins=[0, 10, 25, 50, 100, float('inf')],
            labels=['Très bas', 'Bas', 'Moyen', 'Élevé', 'Premium']
        )
        
        self.data['Dim_Products'] = products
        logger.info(f"✅ Dim_Products créée: {len(products)} lignes")
    
    def create_dim_employees(self):
        """Créer la dimension Employés"""
        logger.info("Création de Dim_Employees...")
        
        employees = self.data.get('Employees', pd.DataFrame()).copy()
        
        if employees.empty:
            return
        
        # Nom complet
        employees['FullName'] = employees['FirstName'] + ' ' + employees['LastName']
        
        # Calcul de l'ancienneté
        if 'HireDate' in employees.columns:
            employees['HireDate'] = pd.to_datetime(employees['HireDate'])
            employees['YearsOfService'] = (
                (datetime.now() - employees['HireDate']).dt.days / 365
            ).round(1)
        
        self.data['Dim_Employees'] = employees
        logger.info(f"✅ Dim_Employees créée: {len(employees)} lignes")
    
    def create_dim_time(self):
        """Créer la dimension Temps"""
        logger.info("Création de Dim_Time...")
        
        fact_sales = self.data.get('Fact_Sales', pd.DataFrame())
        
        if fact_sales.empty or 'OrderDate' not in fact_sales.columns:
            return
        
        # Créer une table de dates unique
        dates = fact_sales['OrderDate'].drop_duplicates().sort_values()
        
        dim_time = pd.DataFrame({
            'Date': dates,
            'Year': dates.dt.year,
            'Month': dates.dt.month,
            'MonthName': dates.dt.month_name(),
            'Quarter': dates.dt.quarter,
            'DayOfWeek': dates.dt.dayofweek,
            'DayName': dates.dt.day_name(),
            'WeekOfYear': dates.dt.isocalendar().week
        })
        
        self.data['Dim_Time'] = dim_time
        logger.info(f"✅ Dim_Time créée: {len(dim_time)} lignes")
    
    def create_sales_summary(self):
        """Créer des résumés de ventes"""
        logger.info("Création des résumés de ventes...")
        
        fact_sales = self.data.get('Fact_Sales', pd.DataFrame())
        
        if fact_sales.empty:
            return
        
        # Ventes par mois
        sales_by_month = fact_sales.groupby(['Year', 'Month']).agg({
            'TotalAmount': 'sum',
            'OrderID': 'nunique',
            'Quantity': 'sum'
        }).reset_index()
        sales_by_month.columns = ['Year', 'Month', 'TotalSales', 'OrderCount', 'TotalQuantity']
        self.data['Sales_By_Month'] = sales_by_month
        
        # Ventes par catégorie
        products = self.data.get('Dim_Products', pd.DataFrame())
        if not products.empty and 'CategoryName' in products.columns:
            sales_with_category = pd.merge(
                fact_sales,
                products[['ProductID', 'CategoryName']],
                on='ProductID',
                how='left'
            )
            sales_by_category = sales_with_category.groupby('CategoryName').agg({
                'TotalAmount': 'sum',
                'Quantity': 'sum'
            }).reset_index()
            sales_by_category.columns = ['CategoryName', 'TotalSales', 'TotalQuantity']
            self.data['Sales_By_Category'] = sales_by_category
        
        # Ventes par pays client
        customers = self.data.get('Dim_Customers', pd.DataFrame())
        if not customers.empty:
            sales_with_country = pd.merge(
                fact_sales,
                customers[['CustomerID', 'Country']],
                on='CustomerID',
                how='left'
            )
            sales_by_country = sales_with_country.groupby('Country').agg({
                'TotalAmount': 'sum',
                'OrderID': 'nunique'
            }).reset_index()
            sales_by_country.columns = ['Country', 'TotalSales', 'OrderCount']
            self.data['Sales_By_Country'] = sales_by_country
        
        # Top 10 produits
        top_products = fact_sales.groupby('ProductID').agg({
            'TotalAmount': 'sum',
            'Quantity': 'sum'
        }).reset_index()
        top_products = top_products.nlargest(10, 'TotalAmount')
        if not products.empty:
            top_products = pd.merge(
                top_products,
                products[['ProductID', 'ProductName']],
                on='ProductID',
                how='left'
            )
        self.data['Top_Products'] = top_products
        
        logger.info("✅ Résumés de ventes créés")
    
    @staticmethod
    def categorize_region(country):
        """Catégoriser les pays par région"""
        europe = ['Germany', 'UK', 'France', 'Spain', 'Italy', 'Sweden', 
                  'Finland', 'Austria', 'Belgium', 'Denmark', 'Ireland',
                  'Norway', 'Poland', 'Portugal', 'Switzerland']
        north_america = ['USA', 'Canada', 'Mexico']
        south_america = ['Brazil', 'Argentina', 'Venezuela']
        
        if country in europe:
            return 'Europe'
        elif country in north_america:
            return 'Amérique du Nord'
        elif country in south_america:
            return 'Amérique du Sud'
        else:
            return 'Autre'

    # =============================================================================
    # CHARGEMENT
    # =============================================================================
    
    def load(self, output_path=None, prefix='access_'):
        """Charger les données dans des fichiers CSV avec préfixe"""
        logger.info("=" * 50)
        logger.info("DÉBUT DU CHARGEMENT")
        logger.info("=" * 50)
        
        # Use config path if no output_path provided
        if output_path is None:
            output_path = self.output_path
        
        try:
            # Ensure directory exists
            Path(output_path).mkdir(parents=True, exist_ok=True)
            
            # Save all tables with prefix to distinguish from SQL Server data
            for table_name, df in self.data.items():
                if df is not None and not df.empty:
                    file_path = Path(output_path) / f'{prefix}{table_name}.csv'
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
                    logger.info(f"✅ {prefix}{table_name}.csv sauvegardé ({len(df)} lignes)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement: {str(e)}")
            return False
    
    def close(self):
        """Fermer la connexion à Access"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("✅ Connexion Access fermée")
            except Exception as e:
                logger.error(f"❌ Erreur lors de la fermeture: {e}")
    
    def run(self):
        """Exécuter le pipeline ETL complet"""
        try:
            # Connection
            if not self.connect():
                return False
            
            # Extraction
            self.extract_all()
            
            # Transformation
            self.transform()
            
            # Load
            if not self.load():
                return False
            
            logger.info("=" * 50)
            logger.info("ETL ACCESS TERMINÉ AVEC SUCCÈS")
            logger.info("=" * 50)
            logger.info(f"📁 Données sauvegardées dans: {self.output_path}")
            
            self.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur ETL: {str(e)}")
            self.close()
            return False

# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║        ETL NORTHWIND ACCESS - Business Intelligence           ║
    ║                    Projet BI 2025                             ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Créer et exécuter l'ETL
    etl = NorthwindAccessETL(ACCESS_DB_CONFIG)
    success = etl.run()
    
    if success:
        print("\n✅ Pipeline ETL Access exécuté avec succès!")
        print("📁 Les données sont disponibles dans le dossier 'data/' avec le préfixe 'access_'")
    else:
        print("\n❌ Le pipeline ETL Access a rencontré des erreurs.")
        print("📋 Consultez le fichier de log pour plus de détails.")
