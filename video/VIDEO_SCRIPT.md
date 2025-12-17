# Script de Présentation Vidéo

**Durée estimée : 3-5 minutes**

---

## 1. Introduction (Caméra on ou Slide titre)
"Bonjour, je m'appelle [Votre Nom]. Je vous présente aujourd'hui ma solution de Business Intelligence complète basée sur la base de données Northwind."

"L'objectif de ce projet était d'unifier les données provenant de deux sources différentes : une base SQL Server historique et une base Microsoft Access plus récente, pour offrir une vue à 360 degrés de l'activité de l'entreprise."

## 2. Architecture et ETL (Montrer le code VS Code)
"Pour réaliser cela, j'ai mis en place une architecture pipeline en Python."

*(Ouvrir le dossier /scripts)*
"Voici mes scripts ETL. J'utilise Python avec la librairie Pandas pour extraire les données."
- "D'un côté, j'extrais les données historiques de SQL Server."
- "De l'autre, j'intègre les données de la base Access 2012."

*(Montrer le dossier /data)*
"Toutes ces données sont transformées et stockées sous forme de fichiers CSV normalisés ici, dans le dossier Data. C'est ce qu'on appelle une architecture 'Flat File' qui rend la solution très portable."

## 3. Le Tableau de Bord (Montrer le Dashboard dans le navigateur)
*(Basculer sur le navigateur)*
"Voici le résultat final : le tableau de bord analytique."

"Ce que vous voyez ici est une fusion en temps réel des deux bases de données."
- "Nous avons un CA global de 1.35 millions de dollars."
- "Le système gère 120 clients unifiés provenant des deux systèmes."

*(Faire une démo des filtres)*
"Le dashboard est interactif. Je peux filtrer par période, par pays, ou par catégorie de produit. Regardez comment les graphiques s'adaptent instantanément."

*(Montrer les graphiques)*
"J'ai intégré plusieurs types de visualisations :"
- "L'évolution des ventes dans le temps."
- "La répartition par catégorie (graphique en anneau)."
- "Et le top des clients et produits."
- "Tout cela a été réalisé avec la librairie Plotly.js pour une expérience utilisateur fluide."

## 4. Analyse Avancée (Montrer le Notebook ou les Scripts Python)
*(Revenir sur VS Code)*
"En plus du web, j'ai également développé des scripts d'analyse Python pour des besoins plus statistiques, permettant de générer des visualisations statiques pour les rapports mensuels."

## 5. Conclusion
"Pour conclure, ce projet a permis de répondre au besoin critique d'unification des données. Nous avons maintenant une solution robuste, capable de suivre l'activité de l'entreprise quelque soit la source de données d'origine."

"Merci de votre attention."
