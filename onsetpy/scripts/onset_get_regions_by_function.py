#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get label ID in Yale atlas by brain function.
Interactive function search 

"""

import argparse
from datetime import datetime
import json
import os
import questionary
from dict_effects import dict_effects

import pandas as pd
import ast

"""
from onsetpy.onsetpy.io.utils import (
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    add_version_arg,
)
"""

# REMPLACEMENT DES FONCTIONS ONSETPY (Utilitaires)

def add_overwrite_arg(parser):
    #Ajoute l'argument --overwrite
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output.")

def add_version_arg(parser):
    #Ajoute l'argument --version
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")

def assert_inputs_exist(parser, paths):
    #Vérifie que les fichiers d'entrée existent
    for path in paths:
        if not os.path.exists(path):
            parser.error(f"Le fichier d'entrée n'existe pas : {path}")
                

def _built_arg_parser():
    parser = argparse.ArgumentParser(
        description = "Trouver les régions cérébrales selon l'Atlas de Yale pour une fonction spécifique",
        formatter_class = argparse.RawTextHelpFormatter
        )
    
    parser.add_argument("DB", help="Path to the DB in csv format.")
    
    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser
     

def load_yale_dict():
    yale_dict_path = "https://raw.githubusercontent.com/YaleBrainAtlas/YaleBrainAtlas/refs/heads/master/data/YBA_696parcels/YBA_696_parcel_dict.csv"
    roi_names = {}
        
    try :        
        df_yale_dict = pd.read_csv(yale_dict_path)
        #Détection des colonnes
        col_name = 'Long_name'

        #ID correspond au numero de la ligne -1 (car ligne 0 est l'index)
        df_yale_dict['col_id'] = df_yale_dict.index + 1
        df_yale_dict['col_id'] = df_yale_dict['col_id'].astype(int)
        roi_names = dict(zip(df_yale_dict['col_id'],df_yale_dict[col_name]))
    except Exception:
        print("Dictionnaire non chargé.")
    
    return df_yale_dict, roi_names 


def pre_process_df(df):
    """
    Prépare le df pour les statistiques 
    Sépare les lignes contenant plusieurs ROI (séparés par des virgules) en plusieurs lignes (1 ROI par ligne)
    """
    
    #Parsing selon ROI (gestion listes et deduplication)
    def _parse_roi_list(val):
        #On découpe par , et on convertit en str
        id = str(val).split(',')
        #Retrait des doublons 
        unique_ids = list(set(id))  
        return unique_ids
    
    #Création de la liste de ROI unifiée, à partir de la colonne unifiée (traitement ligne par ligne)
    df['roi_list'] = df['unified_roi'].apply(_parse_roi_list)

    #Calcul du poids basé sur la colonne de la ROI unifiée  
    df['weight'] = df['roi_list'].apply(lambda x: 1/len(_parse_roi_list(x)))    
    df["weighted_occurrence_clinical_effect"] = (df["occurrence_clinical_effect"] * df["weight"])

        
    #On "explose' : 1 ROI par ligne 
    df = df.explode('roi_list').dropna(subset=['roi_list']).reset_index(drop=True)
    
    # On nettoie et on crée la colonne 'roi_id' proprement
        # On ne garde que les valeurs numériques (pour éviter les erreurs de conversion)
    df = df[df['roi_list'].astype(str).str.strip().str.isnumeric()]
    
        # On crée la colonne roi_id en entier
    df['roi_id'] = df['roi_list'].astype(int)

    return df


def main():
    parser = _built_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, [args.DB])
    
    #Chargement de la DB 
    with open(args.DB, "r") as file:
        df = pd.read_csv(file)
        
    #Chargement du dictionnaire Yale 
    df_yale_dict, roi_names = load_yale_dict()

    print("-"*100)
    exclure_exact = questionary.confirm("Exclude exact localization ?").ask()
    if exclure_exact:
        #On filtre le tableau : on ne garde que les lignes qui n'ont pas "exact" dans la méthode de conversion
        df = df[df['roi_mask_conversion_method'] != 'exact']

    #Pré-traitement 
    df = pre_process_df(df)

    #Regle pour contourner le pb de div par 0 (nb stim null)
    #Nombre de stim est au minimum egal au nb d'occurence 
    #Comparaison des deux colonnes ligne par ligne et on garde le max 
    df['nb_stimulations'] = df[['nb_stimulations', "occurrence_clinical_effect"]].max(axis=1)

    #Calcul du total de stimulations pour chaque région (pour le ratio) avant le filtrage
    #Somme des stimulations pour chaque région (roi_id) sur toute la DB
    #total_stimulations_per_roi = df.groupby('roi_id')['nb_stimulations'].sum().reset_index()
    #total_stimulations_per_roi.rename(columns={'nb_stimulations': 'total_nb_stimulations'}, inplace=True)

    #On colle ce total dans le tableau principal pour chaque ligne correspondante à la région (roi_id)
    #df = pd.merge(df,total_stimulations_per_roi, on='roi_id', how='left')

    print("-"*100)
        
    #Choix de la fonction 
    #Menu Niveau 1 : Classe
    choix_classe = questionary.select(
        "Choose the effect class",
        choices=list(dict_effects.keys()) +
        [questionary.Separator(),
        "Manually research"]
        ).ask()
        
    search_term = ""
    search_column = ""
    display_title = ""
        
    if choix_classe == "Manually research":
        search_term = questionary.text("Entry the term to search : ").ask()
        search_column = "effect_details"
        display_title = f"Research free : '{search_term}'"
        
    else:
        #Menu Niveau 2 
        sous_categories = dict_effects[choix_classe]
            
        choix_descripteur = questionary.select(
            f"Class {choix_classe} - Choose the descriptor : ",
            #L'utilisateur peut choisir un des effets de niveau 2 ou tous les effets 
            choices = sous_categories + [questionary.Separator(), f"All descriptors in '{choix_classe}'"]
        ).ask()
            
        #Si l'utilisateur veut toute la catégorie 
        if choix_descripteur.startswith("All descriptors"):
            search_term = choix_classe
            search_column = 'effect_class'
        else:
            search_term = choix_descripteur
            search_column = 'effect_descriptor'
                
                
    #Filtrage des données : on ne garde que les lignes correspondantes 
    print(f"Researching {search_term} in database...")
        
    df = df[df[search_column].astype(str).str.contains(search_term, case=False, na=False)]
        
    if df.empty:
        print("No result found in database.") 
        return


    #Bloc d'agrégation    
    agg = (
        #On rassemble les lignes par région (roi_id)
        df.groupby('roi_id') 
        .agg(
            #On additionne les occurrences positives pour chaque region
            total_occurrence_clinical_effect=("occurrence_clinical_effect", "sum"),
            #On additionne les occurrences positives pondérées pour chaque région
            total_weighted_occurrence_clinical_effect=("weighted_occurrence_clinical_effect", "sum"),
            total_nb_stimulations=("nb_stimulations", "sum"), 
        )
        .reset_index()
            
        # Pour chaque régions
        # Ratio brut : sum(occurrence_clinical_effect * (1/nb_regions)) / nb_stimulations_total
        .assign(
            total_positive_ratio=lambda x: x["total_occurrence_clinical_effect"]
            / x["total_nb_stimulations"]
        )
        # Ratio pondéré : sum(weighted_occurrence_clinical_effect * (1/nb_regions)) / nb_stimulations_total
        .assign(
            weighted_positive_ratio=lambda x: x["total_weighted_occurrence_clinical_effect"]
            / x["total_nb_stimulations"]
        )
    )
        
    #Ajout des noms des parcels (Yale dict)
    def trouver_roi_name(row):
        id_courant = int(row['roi_id'])

        #On regarde dans le dictionnaire Yale si on trouve une correspondance
        if id_courant in roi_names:
            return roi_names[id_courant]

    #On applique cette fonction sur chq ligne pour créer la colonne roi_name    
    agg['roi_name'] = agg.apply(trouver_roi_name, axis=1)
                
            
    #Préparation des données pour l'affichage
    top_n = 696
    final_agg = (
        agg.fillna(0) #Remplace les valeurs NaN par 0 pour éviter les erreurs
        .sort_values(by="weighted_positive_ratio", ascending=False) #Tri croissant 
        .reset_index(drop=True)
        )
        
    n_show = min(len(final_agg), top_n)
        
    print(f"\nRégions Yale probables (Top {n_show})")
    print("-"*100)
    print(f"{'Label Yale':<4} {'Région Positive':<37} {'Pondéré (%)':>11} {'Brut (%)':>9} {'Nb stim':>8} {'Tot pond.':>14} {'Tot':>1}")
    print("-" *100)
    
    for i, row in final_agg.head(n_show).iterrows():
        roi_id_val = row['roi_id']
        label = str(row.get('roi_name', "<inconnu>"))
        weighted_ratio = float(row.get("weighted_positive_ratio", 0.0) or 0.0)
        ratio = float(row.get("total_positive_ratio", 0.0) or 0.0)
        nb = int(row.get("total_nb_stimulations", 0.0) or 0.0)
        tot_weighted = float(row.get("total_weighted_occurrence_clinical_effect", 0.0) or 0.0)
        tot = float(row.get("total_occurrence_clinical_effect", 0.0) or 0.0)
    
        #Coupe le nom du label si trop long
        label_display = (label[:27] + "...") if len(label) > 30 else label
    
        print(
            f"{roi_id_val:<10} " #Affiche l'ID et complete avec des espaces pour que ca prenne 10 caracteres (aligné à gauche)
            f"{label_display:<30} "
            f"{weighted_ratio * 100:15.1f} {ratio * 100:9.1f} {nb:8d} " 
            #Affiche un chiffre avec 1 decimal sur une largeur de 11 caracteres
            f"{tot_weighted:14.2f} {tot:7.2f}"
        )
        print("-" *100)

main() 
    