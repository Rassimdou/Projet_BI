import pyodbc
import pandas as pd
from pathlib import Path
import logging
import sys
from config import DATA_PATH, REPORTS_PATH, ACCESS_DB_CONFIG

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(REPORTS_PATH / 'etl_access_simple_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ],
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Fixer l'encodage de la console Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace') 

# =============================================================================
# ETL SIMPLIFIÉ POUR ACCESS DATABASE
# =============================================================================

class SimpleAccessETL:
    """ETL simplifié - extraction brute sans transformation complexe"""
    
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.data = {}
        self.output_path = DATA_PATH

    def connect(self):
        """Établir la connexion à Access Database"""
        try:
            db_path = self.config['database_path']
            
            if not Path(db_path).exists():
                logger.error(f"❌ Fichier Access introuvable: {db_path}")
                return False
            
            conn_string = (
                f"DRIVER={self.config['driver']};"
                f"DBQ={db_path};"
            )
            
            self.connection = pyodbc.connect(conn_string)
            logger.info(f"✅ Connexion à Access établie: {db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur de connexion Access: {e}")
            return False
    
    def list_tables(self):
        """Lister toutes les tables disponibles"""
        try:
            cursor = self.connection.cursor()
            tables = []
            for table_info in cursor.tables(tableType='TABLE'):
                table_name = table_info.table_name
                # Filtrer les tables système
                if not table_name.startswith('MSys') and not table_name.startswith('~'):
                    tables.append(table_name)
            logger.info(f"📋 Tables trouvées ({len(tables)}): {', '.join(tables)}")
            return tables
        except Exception as e:
            logger.error(f"❌ Erreur lors de la liste des tables: {e}")
            return []
    
    def extract_table(self, table_name):
        """Extraire les données d'une table Access"""
        try:
            query = f"SELECT * FROM [{table_name}]"
            df = pd.read_sql(query, self.connection)
            logger.info(f"✅ Table '{table_name}' extraite: {len(df)} lignes, {len(df.columns)} colonnes")
            return df
        except Exception as e:
            logger.error(f"❌ Erreur extraction '{table_name}': {e}")
            return pd.DataFrame()
    
    def extract_all(self):
        """Extraire toutes les tables"""
        logger.info("=" * 50)
        logger.info("DÉBUT DE L'EXTRACTION (ACCESS - SIMPLE)")
        logger.info("=" * 50)
        
        available_tables = self.list_tables()
        
        for table in available_tables:
            # Créer un nom de fichier sûr
            safe_name = table.replace(' ', '_').replace('-', '_')
            self.data[safe_name] = self.extract_table(table)
        
        logger.info(f"✅ Extraction terminée: {len(self.data)} tables")
        return self.data
    
    def load(self, prefix='access_'):
        """Charger les données dans des fichiers CSV"""
        logger.info("=" * 50)
        logger.info("DÉBUT DU CHARGEMENT")
        logger.info("=" * 50)
        
        try:
            Path(self.output_path).mkdir(parents=True, exist_ok=True)
            
            saved_count = 0
            for table_name, df in self.data.items():
                if df is not None and not df.empty:
                    file_path = Path(self.output_path) / f'{prefix}{table_name}.csv'
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
                    logger.info(f"✅ {prefix}{table_name}.csv sauvegardé ({len(df)} lignes)")
                    saved_count += 1
            
            logger.info(f"✅ Total: {saved_count} fichiers sauvegardés")
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
    ║     ETL NORTHWIND ACCESS (SIMPLE) - Business Intelligence     ║
    ║                    Projet BI 2025                             ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Créer et exécuter l'ETL
    etl = SimpleAccessETL(ACCESS_DB_CONFIG)
    success = etl.run()
    
    if success:
        print("\n✅ Pipeline ETL Access exécuté avec succès!")
        print("📁 Les données sont disponibles dans le dossier 'data/' avec le préfixe 'access_'")
        print("\n💡 Note: Les tables sont extraites telles quelles, sans transformation.")
        print("   Vous pouvez les utiliser directement dans votre dashboard.")
    else:
        print("\n❌ Le pipeline ETL Access a rencontré des erreurs.")
        print("📋 Consultez le fichier de log pour plus de détails.")
