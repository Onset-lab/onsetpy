#!/usr/bin/env python3

"""
Get brain function by label ID in Yale atlas.
"""

import argparse
from datetime import datetime
import json
import os
import questionary

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


def _build_arg_parser():
    """Build argparser.

    Returns:
        parser (ArgumentParser): Parser built.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("DB", help="Path to the DB in csv format.")

    parser.add_argument(
        "label_id", type=int, help="Label ID to retrieve brain function."
    )
    parser.add_argument(
        "function_type",
        choices=["effect_class", "effect_descriptor", "effect_details"],
        help="Type of function.",
    )

    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser

def pre_process_df(df):
    """
    Prépare le df pour les statistiques 
    Choix de la colonne ROI selon méthode de conversion : 
        - si method "exact" : prendre dans 'yale_label'
        - si method "approx" : prendre dans 'roi_mask'
    Sépare les lignes contenant plusieurs ROI (séparés par des virgules) en plusieurs lignes (1 ROI par ligne)
    """
    
    
    #1. Parsing selon ROI (gestion listes et deduplication)
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
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, [args.DB])

    #Chargement de la DB 
    with open(args.DB, "r") as file:
        df = pd.read_csv(file)

    #Pré-traitement 
    df = pre_process_df(df)

    #Filtrage pour ne garder que les lignes correspondant au label demandé
    df = df.loc[df["roi_id"] == args.label_id]

    #Explosion des fonctions selon le type demandé (effect_class, effect_descriptor ou effect_details)
        #Split sur la colonne choisie
    df[args.function_type] = df[args.function_type].str.split(',')
        #On "explose" pour avoir 1 fonction par ligne
    df = df.explode(args.function_type)
        #On retire les lignes où la fonction est vide ou nulle
    df = df.dropna(subset=[args.function_type])


    # aggregate totals by effect_class (handle both possible column names for stimulations)
    nb_col = "nb_stimulations" if "nb_stimulations" in df.columns else "nb_stimulation"
    
    agg = (
        df.groupby(args.function_type)
        .agg(
            total_occurrence_clinical_effect=("occurrence_clinical_effect", "sum"),
            total_weighted_occurrence_clinical_effect=(
                "weighted_occurrence_clinical_effect",
                "sum",
            ),
            total_nb_stimulations=(nb_col, "sum"),
        )
        .reset_index()
        # Pour chaque fonction pour un label X: sum(occurence_clinical_effect * (1/nb_regions)) / sum(nb_stimulations)
        .assign(
            total_positive_ratio=lambda x: x["total_occurrence_clinical_effect"]
            / x["total_nb_stimulations"]
        )
        # Pour chaque fonction pour un label X: sum(occurence_clinical_effect * (1/nb_regions)) / sum(nb_stimulations)
        .assign(
            weighted_positive_ratio=lambda x: x[
                "total_weighted_occurrence_clinical_effect"
            ]
            / x["total_nb_stimulations"]
        )
    )
    # Impression "propre" des fonctions les plus probables pour le label demandé
    if agg.empty:
        print(f"Aucune fonction trouvée pour le label {args.label_id}")
    else:
        top_n = 10
        sorted_agg = (
            agg.fillna(0)
            .sort_values(by="weighted_positive_ratio", ascending=False)
            .reset_index(drop=True)
        )
        n_show = min(len(sorted_agg), top_n)
        print(f"\nFonctions probables pour le label {args.label_id} (Top {n_show})")
        # Print a nicely formatted table similar to the requested output
        # Header
        print(
            f"{'N°':<4} {'Fonction Positive':<30} {'Pondéré (%)':>11} {'Brut (%)':>9} {'Nb stim':>8} {'Tot pond.':>10} {'Tot':>7}"
        )
        print("-" * 86)

        for i, row in sorted_agg.head(n_show).iterrows():
            effect = str(row.get(args.function_type, "<inconnu>"))
            weighted_ratio = float(row.get("weighted_positive_ratio", 0.0) or 0.0)
            ratio = float(row.get("total_positive_ratio", 0.0) or 0.0)
            nb = int(row.get("total_nb_stimulations", 0) or 0)
            tot_weighted = float(
                row.get("total_weighted_occurrence_clinical_effect", 0.0) or 0.0
            )
            tot = float(row.get("total_occurrence_clinical_effect", 0.0) or 0.0)

            # Effect name truncated to fit column width
            effect_display = (effect[:27] + "...") if len(effect) > 30 else effect

            print(
                f"{i+1:<4d} {effect_display:<30} "
                f"{weighted_ratio * 100:11.1f} {ratio * 100:9.1f} {nb:8d} "
                f"{tot_weighted:10.2f} {tot:7.2f}"
            )
        print("-" * 86)

main()