#!/usr/bin/env python3

"""
Get brain function by label ID in Yale atlas.
"""

import argparse
from datetime import datetime
import json
import os
import questionary
from dict_effects import dict_effects

import pandas as pd
import ast
import numpy as np

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
    # Ajoute l'argument --overwrite
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing output."
    )

def add_version_arg(parser):
    # Ajoute l'argument --version
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")

def assert_inputs_exist(parser, paths):
    # Vérifie que les fichiers d'entrée existent
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

def load_yale_dict():
    yale_dict_path = "https://raw.githubusercontent.com/YaleBrainAtlas/YaleBrainAtlas/refs/heads/master/data/YBA_690parcels/YBA_690_parcel_dict.csv"
    roi_names = {}

    try:
        df_yale_dict = pd.read_csv(yale_dict_path)
        # Détection des colonnes
        col_name = "Long_name"

        # ID correspond au numero de la ligne -1 (car ligne 0 est l'index)
        df_yale_dict["col_id"] = df_yale_dict.index + 1
        df_yale_dict["col_id"] = df_yale_dict["col_id"].astype(int)
        roi_names = dict(zip(df_yale_dict["col_id"], df_yale_dict[col_name]))
    except Exception:
        print("Dictionnaire non chargé.")

    return df_yale_dict, roi_names

#-------------------------------------------------------------------

def pre_process_df(df, df_yale_dict, roi_names):
    """
    Prépare le df pour les statistiques
    Sépare les lignes contenant plusieurs ROI (séparés par des virgules) en plusieurs lignes (1 ROI par ligne)
    """

    # Parsing selon ROI (gestion listes et deduplication)
    def _parse_roi_list(val):
        # On découpe par , et on convertit en str
        id = str(val).split(",")
        # Retrait des doublons
        unique_ids = list(set(id))
        return unique_ids

    # Création de la liste de ROI, à partir de la colonne unifiée (traitement ligne par ligne)
    df["roi_list"] = df["roi_unified"].apply(_parse_roi_list)

    #Prise en compte de la right side - Conversion par dictionnaire pour être sur de la corrélation 
    #UNIQUEMENT pour methode différente de exact
        #Avoir le label à partir de la région (ex: 14 : L_PH_A)
    name_to_id = dict(zip(df_yale_dict["Name"], (df_yale_dict["col_id"].index+1).astype(int)))
        #Avoir la region à partir de l'ID (ex: 362 : R_PH_A or +348 ne donne pas la bonne region)
    id_to_name = dict(zip(df_yale_dict["col_id"].index+1, df_yale_dict["Name"]))

    def convert_to_right_id(roi_id):
        #On convertit en entier
        roi_id = int(roi_id)
        #On cherche le nom de la région à partir de l'ID dans le dictionnaire 
        roi_name = id_to_name.get(roi_id)
        #Si la région existe et commence par L 
        if roi_name and roi_name.startswith("L"):
            #On remplace L par R 
            right_roi_name = roi_name.replace("L", "R", 1)
            #On cherche l'ID de la région droite correspondante
            right_roi_id = name_to_id.get(right_roi_name)
            #Si on trouve l'ID de la région droite, on le retourne
            if right_roi_id:
                return right_roi_id
                
    #Condition : Right side et méthode de conversion différente de exact    
    roi_droite_non_exacte = (df["roi_side"] == "right") & (df["roi_mask_conversion_method"] != "exact")
    
    df.loc[roi_droite_non_exacte, "roi_list"] = df.loc[
        roi_droite_non_exacte, "roi_list"
    ].apply(lambda x: [convert_to_right_id(i) for i in x])

    # Calcul du poids basé sur la colonne de la ROI unifiée
    # Poids = 1 / nb de ROI dans la liste (pour chaque ligne)
    df["weight"] = df["roi_list"].apply(lambda x: 1 / len(_parse_roi_list(x)))
    # Poids pondéré de l'occurrence clinique = occurrence_clinical_effect * poids
    df["weighted_occurrence_clinical_effect"] = (df["occurrence_clinical_effect"]*df["weight"])
    
    # On 'explose' : 1 ROI par ligne
    df = df.explode("roi_list").dropna(subset=["roi_list"]).reset_index(drop=True)

    # On nettoie et on crée la colonne 'roi_id' proprement
    # On ne garde que les valeurs numériques (pour éviter les erreurs de conversion)
    df = df[df["roi_list"].astype(str).str.strip().str.isnumeric()]

    # On crée la colonne roi_id en entier
    df["roi_id"] = df["roi_list"].astype(int)

    return df


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()
    assert_inputs_exist(parser, [args.DB])

    # Chargement de la DB
    with open(args.DB, "r") as file:
        df = pd.read_csv(file)

    #Chargement du dictionnaire Yale
    df_yale_dict, roi_names = load_yale_dict()

    #On ajoute la possibilité à l'utilisateur d'exclure les localisations exactes
    exclure_exact = questionary.confirm("Exclude exact localization ?").ask()
    if exclure_exact:
        # On filtre le tableau : on garde tout sauf les lignes qui ont "exact" dans la méthode de conversion
        df = df[df["roi_mask_conversion_method"] != "exact"]

    # Pré-traitement
    df = pre_process_df(df, df_yale_dict, roi_names)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)

    # Filtrage pour ne garder que les lignes correspondant au label demandé
    df = df.loc[df["roi_id"] == args.label_id]

    # Explosion des fonctions selon le type demandé (effect_class, effect_descriptor ou effect_details)
    # Split sur la colonne choisie
    df[args.function_type] = df[args.function_type].str.split(",")
    # On "explose" pour avoir 1 fonction par ligne
    df = df.explode(args.function_type)
    # On retire les lignes où la fonction est vide ou nulle
    df = df.dropna(subset=[args.function_type])

    # Filtrage strict par le dictionnaire
    # Récupération de la liste des fonctions valides pour le type demandé
    mots_autorises = []

    if args.function_type == "effect_class":
        # Pour les classes on prend les clés du dictionnaire
        mots_autorises = list(dict_effects.keys())

    elif args.function_type == "effect_descriptor":
        # Pour les descripteurs on prend la liste de tous les descripteurs du dictionnaire (valeurs de toutes les clés)
        for descripteurs in dict_effects.values():
            mots_autorises.extend(descripteurs)
    
        #Exclusion de Responsive Rate et Motor 
    mots_autorises = [mot for mot in mots_autorises if mot not in ["[Responsive rate]", "Motor"]]

        # On garde uniquement les fonctions valides (dans la liste des mots autorisés)
    df = df[df[args.function_type].isin(mots_autorises)]

    print(df[df["effect_class"] == "Sensory"])
    print(f"Number of rows: {len(df[df['effect_class'] == 'Sensory'])}")

    #Total des stimulations pour le label demandé (dénominateur commun à toutes les fonctions)
    total_nb_stim_positive_per_label = df["occurrence_clinical_effect"].sum()
    total_weighted_nb_stim_positive_per_label = df["weighted_occurrence_clinical_effect"].sum()

    agg = (
        df.groupby(args.function_type)
        .agg(
            #Calcul des totaux pour chaque fonction (numérateur)
            total_occurrence_clinical_effect=("occurrence_clinical_effect", "sum"),
            total_weighted_occurrence_clinical_effect=(
                "weighted_occurrence_clinical_effect",
                "sum",
            ),
        )
        .reset_index()
        .assign(
            #Calcul du ratio brut (Taux de réponse positive brut) = nb occ positive pour la fonction / nb total de stimulations positives pour le label
            total_positive_ratio=lambda x: x["total_occurrence_clinical_effect"]
            / total_nb_stim_positive_per_label
        )
        .assign(
            #Calcul du ratio pondéré (Taux de réponse positive pondéré)
            weighted_positive_ratio=lambda x: x[
                "total_weighted_occurrence_clinical_effect"
            ]
            / total_weighted_nb_stim_positive_per_label
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
        print(f"\nFonctions probables pour le label {args.label_id} (Top {n_show}) pour ", int(total_nb_stim_positive_per_label), " stimulations positives :\n")
        # Print a nicely formatted table similar to the requested output
        # Header
        print(
            f"{'N°':<4} {'Fonction Positive':<30} {'Pondéré (%)':>11} {'Brut (%)':>9} {'Tot occ pond.':>7} {'Tot occ':>7}"
        )
        print("-" * 100)
        for i, row in sorted_agg.head(n_show).iterrows():
            effect = str(row.get(args.function_type, "<inconnu>"))
            ratio = float(row.get("total_positive_ratio", 0.0) or 0.0)
            weighted_ratio = float(row.get("weighted_positive_ratio", 0.0) or 0.0)
            tot_weighted = float(
                row.get("total_weighted_occurrence_clinical_effect", 0.0) or 0.0
            )
            tot = float(row.get("total_occurrence_clinical_effect", 0.0) or 0.0)

            # Effect name truncated to fit column width
            effect_display = (effect[:27] + "...") if len(effect) > 30 else effect

            print(
                f"{i+1:<4d} {effect_display:<30} "
                f"{weighted_ratio * 100:11.1f} {ratio * 100:9.1f} "
                f"{tot_weighted:10.2f} {tot:10.2f}"
            )
        print("-" * 100)

main()
