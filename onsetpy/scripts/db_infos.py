# -*- coding: utf-8 -*-
"""
Data informations for grants
"""

import pandas as pd
import sqlite3
from dict_effects import dict_effects


#Configuration
#Nom du fichier d'entrée
path_db = 'G:\SPACES\DB_14oct.db'

path_processed_db = "G:\SPACES\processed_DB_14oct.csv"

def get_db_infos(path_db, path_processed_db):
    """ Fonction qui permet de récupérer les informations de la DB
    pour la demande de bourse IRSC
    - Nombre d'articles
    - Nombre de points de stim total
    - Nombre de fonctions évaluées par niveau
    - Nombre de patients """

    #Connexion à la DB
    conn = sqlite3.connect(path_db)

    #Calcul du nombre de patients et d'articles à partir de la DB
    query_patients = "SELECT SUM(cohort) FROM SOURCES"
    query_articles = "SELECT MAX(id) FROM SOURCES"

    nb_patients = pd.read_sql_query(query_patients, conn).iloc[0,0]
    nb_articles = pd.read_sql_query(query_articles, conn).iloc[0,0]

    print(f"Nombre d'articles : {nb_articles}")
    print(f"Nombre de patients : {nb_patients}")
    

    #Fermeture de la connexion à la DB
    conn.close()

    processed_db = pd.read_csv(path_processed_db)

    #Calcul du nombre de points de stim total
    nb_regions_stim = set() #pour eviter les doublons 

        #Pour chaque case de la colonne unified_roi on ajoute les regions stim
    for case in processed_db['unified_roi']:
        #Séparation des roi par virgule et ajout à l'ensemble
        regions = str(case).split(',')
        
        #Pour chaque region trouvée dans la case, on l'ajoute à l'ensemble des régions stimulées
        for region in regions:
            nb_regions_stim.add(region.strip())

    nb_total_regions_stim = len(nb_regions_stim)

    print(f"Nombre de régions stimulées : {nb_total_regions_stim}")

    #Calcul du nombre de fonctions évaluées par niveau 
    print("Nombre de fonctions évaluées par niveau :")
    
    #On récupère tous les descripteurs de la DB
    descripteurs_db = (processed_db['effect_descriptor']
        .dropna() #Suppression des cases vides
        .astype(str) #Conversion en str
        .str.split(',') #Séparation des descripteurs par virgule
        .explode() #On met chaque descripteur sur une ligne différente
        .str.strip() #Suppression des espaces avant et après les descripteurs
        .unique() #On garde que les descripteurs uniques
        )   

    #On croise avec le dictionnaire
    for classe, liste_descripteurs in dict_effects.items():
        descripteurs_in_DB = [d for d in descripteurs_db if d in liste_descripteurs and d != 'Other']

        if len(descripteurs_in_DB) > 0:
            print(f"    Nombre de fonctions évaluées pour la classe {classe} : {len(descripteurs_in_DB)}")
            print("    Détails :")
            print(f"        Les descripteurs sont {', '.join(descripteurs_in_DB)}")
                            

    #Statistiques globales
    print(" \n --- Statistiques globales : ---")
    niveaux = ['effect_class', 'effect_descriptor', 'effect_details']

    for niveau in niveaux:
        nb_fonctions = (processed_db[niveau]
                        .dropna()
                        .astype(str)
                        .str.split(',')
                        .explode()
                        .str.strip()
                        .replace('Other', '') #On ne compte pas other comme des fonctions evaluees
                        .replace('', pd.NA) #On remplace les cases vides par NA pour ne pas les compter
                        .dropna() #Suppression des cases vides
                        .nunique() 
        )

        if niveau == 'effect_class':
            print(f"Nombre de fonctions évaluées au niveau {niveau} (dont Responsive Rate): {nb_fonctions}")
        else:
            print(f"Nombre de fonctions évaluées au niveau {niveau} : {nb_fonctions}")

get_db_infos(path_db, path_processed_db)

