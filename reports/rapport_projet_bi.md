# Rapport du Projet Business Intelligence Northwind

## 1. Objectif du Projet
L'objectif principal de ce projet était de concevoir et réaliser une solution BI complète unifiant les données de deux sources distinctes : une base **SQL Server** et une base **Microsoft Access**, toutes deux basées sur le schéma "Northwind". La solution permet une analyse centralisée des ventes, des clients et des stocks via un tableau de bord web interactif et des analyses Python approfondies.

## 2. Architecture de la Solution

L'architecture mise en place est une architecture "Lakehouse" légère et portable :

1.  **Sources de Données** :
    *   **SQL Server (Northwind)** : Données principales (Ventes historiques, Clients).
    *   **Access (Northwind 2012)** : Données complémentaires (Commandes récentes, Stocks, Achats).

2.  **ETL (Extract, Transform, Load)** :
    *   Scripts Python (`etl_northwind.py`, `etl_access_simple.py`) pour l'extraction.
    *   Transformation et normalisation des données (hétérogénéité des schémas).
    *   Stockage en fichiers **CSV** dans le dossier `/data`.

3.  **Visualisation & Analyse** :
    *   **Tableau de Bord Web** (`dashboard.html` + `dashboard.js`) : Interface opérationnelle interactive pour le suivi des KPI en temps réel.
    *   **Scripts Python** (`scripts/visualization.py`) : Analyses statistiques et génération de graphiques statiques dans `/figures`.

## 3. Processus ETL et Intégration des Données

### Extraction
L'extraction est assurée par deux scripts Python utilisant la librairie `pyodbc` :
*   `etl_northwind.py` : Connecte à SQL Server et extrait les tables de faits et dimensions.
*   `etl_access_simple.py` : Connecte à Access via le pilote ODBC Microsoft Access et extrait les tables brutes.

### Transformation et Fusion
Le défi majeur résidait dans l'intégration de deux schémas différents :
*   **Normalisation des colonnes** : Mapping des noms de colonnes (ex: `CustomerID` vs `ID`, `CompanyName` vs `Company`).
*   **Gestion des Conflits d'ID** : Les ID d'Access ont été préfixés par `ACC_` (ex: `ACC_10248`) pour éviter les doublons avec les ID SQL Server.
*   **Logique de Fusion (JavaScript)** : Le tableau de bord charge les deux jeux de fichiers CSV et les fusionne dynamiquement en mémoire au chargement (`loadAllData()`), créant une vue unifiée "Fact Sales".

## 4. Tableau de Bord Analytique

Le tableau de bord HTML5/JS a été conçu pour être léger et performant (Client-side processing).

### Indicateurs Clés (KPI)
*   **Revenu Total** : Consolidation du CA global.
*   **Nombre de Commandes** : Volume total (SQL + Access).
*   **Nombre de Clients** : Base client unifiée (120 clients).
*   **Panier Moyen** : Analyse de la valeur des commandes.

### Visualisations 2D
*   **Graphiques en barres** : Top 10 Clients, Top 10 Produits, Revenu par Pays.
*   **Graphique Donut** : Répartition par Catégorie.
*   **Graphique Combiné** : Évolution mensuelle (Ventes vs Nombre de commandes).

### Technologies Utilisées
*   **Plotly.js** : Pour des graphiques interactifs et esthétiques.
*   **PapaParse** : Pour le parsing rapide des fichiers CSV côté client.
*   **Vanilla JS/CSS** : Pour une dépendance minimale et une exécution rapide sans framework lourd.

## 5. Justification des Choix Techniques

*   **Pourquoi Python pour l'ETL ?** : Pandas et PyODBC offrent une flexibilité totale pour se connecter à n'importe quelle source JDBC/ODBC et manipuler les données avant le chargement.
*   **Pourquoi CSV ?** : Format universel, facile à déboguer, et ne nécessitant pas de serveur de base de données dédié pour la couche de présentation (portabilité maximale du projet).
*   **Pourquoi une architecture Web (HTML/JS) ?** : Permet de partager le tableau de bord facilement (simple navigateur requis) sans nécessiter l'installation d'un environnement Python/Streamlit chez l'utilisateur final.

## 6. Conclusion
Ce projet démontre la capacité à intégrer des systèmes hétérogènes (SQL Server et Access) en une solution BI cohérente, couvrant toute la chaîne de valeur de la donnée, de l'extraction brute à la visualisation décisionnelle.
