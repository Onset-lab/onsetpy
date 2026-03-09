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
import matplotlib.cm as cm
import math

"""
from onsetpy.onsetpy.io.utils import (
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    add_version_arg,
)
"""

# REMPLACEMENT DES FONCTIONS ONSETPY (Utilitaires)


def wilson_score(positives, total, roi_id, confidence=0.95):
    """
    Calcule la borne inférieure de l'intervalle de confiance de Wilson.

    :param positives: Nombre de stimulations positives
    :param total: Nombre total de stimulations
    :param confidence: Niveau de confiance (0.95 par défaut)
    :return: Un score entre 0 et 1
    """
    print(positives, total, roi_id)
    if total == 0:
        return 0.0

    # Valeur critique (z) pour le niveau de confiance
    # 0.95 -> 1.96 | 0.99 -> 2.576 | 0.90 -> 1.645
    z_dict = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_dict.get(confidence, 1.96)

    p = float(positives) / total
    print(p)

    # Formule de Wilson
    denominator = 1 + (z**2 / total)
    centre_adjustment = p + (z**2 / (2 * total))
    # print((p * (1 - p) / total))
    uncertainty = z * math.sqrt((p * (1 - p) / total) + (z**2 / (4 * total**2)))

    return (centre_adjustment - uncertainty) / denominator


def score_to_cold_hot(score):
    """
    Convertit un score (0 à 1) en dégradé Bleu -> Blanc -> Rouge.
    0.0 : Bleu pur (Froid)
    0.5 : Blanc (Neutre)
    1.0 : Rouge pur (Chaud)
    """
    score = max(0, min(1, score))

    if score < 0.5:
        # De Bleu (0,0,255) à Blanc (255,255,255)
        # On augmente le Rouge et le Vert proportionnellement
        factor = score / 0.5
        r = int(255 * factor)
        g = int(255 * factor)
        b = 255
    else:
        # De Blanc (255,255,255) à Rouge (255,0,0)
        # On diminue le Vert et le Bleu proportionnellement
        factor = (score - 0.5) / 0.5
        r = 255
        g = int(255 * (1 - factor))
        b = int(255 * (1 - factor))

    return (r, g, b)


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


def _built_arg_parser():
    parser = argparse.ArgumentParser(
        description="Trouver les régions cérébrales selon l'Atlas de Yale pour une fonction spécifique",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("DB", help="Path to the DB in csv format.")

    parser.add_argument(
        "Yale_LUT", help="Path to the Yale LUT in txt format for ITK Snap."
    )

    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser


def load_yale_dict():
    yale_dict_path = "https://raw.githubusercontent.com/YaleBrainAtlas/YaleBrainAtlas/refs/heads/master/data/YBA_696parcels/YBA_696_parcel_dict.csv"
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


def pre_process_df(df):
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

    # Création de la liste de ROI unifiée, à partir de la colonne unifiée (traitement ligne par ligne)
    df["roi_list"] = df["unified_roi"].apply(_parse_roi_list)

    df.loc[df["roi_side"] == "right", "roi_list"] = df.loc[
        df["roi_side"] == "right", "roi_list"
    ].apply(lambda x: [int(i) + 348 for i in x])

    # Calcul du poids basé sur la colonne de la ROI unifiée
    df["weight"] = df["roi_list"].apply(lambda x: 1 / len(_parse_roi_list(x)))
    df["weighted_occurrence_clinical_effect"] = (
        df["occurrence_clinical_effect"] * df["weight"]
    )

    # On "explose' : 1 ROI par ligne
    df = df.explode("roi_list").dropna(subset=["roi_list"]).reset_index(drop=True)

    # On nettoie et on crée la colonne 'roi_id' proprement
    # On ne garde que les valeurs numériques (pour éviter les erreurs de conversion)
    df = df[df["roi_list"].astype(str).str.strip().str.isnumeric()]

    # On crée la colonne roi_id en entier
    df["roi_id"] = df["roi_list"].astype(int)

    return df


def main():
    parser = _built_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, [args.DB])

    # Chargement de la DB
    with open(args.DB, "r") as file:
        df = pd.read_csv(file)

    # Chargement du dictionnaire Yale
    df_yale_dict, roi_names = load_yale_dict()

    print("-" * 100)
    exclure_exact = questionary.confirm("Exclude exact localization ?").ask()
    if exclure_exact:
        # On filtre le tableau : on garde tout sauf les lignes qui ont "exact" dans la méthode de conversion
        df = df[df["roi_mask_conversion_method"] != "exact"]

    # Pré-traitement
    df = pre_process_df(df)

    # Regle pour contourner le pb de div par 0 (nb stim null)
    # Nombre de stim est au minimum egal au nb d'occurence
    # Comparaison des deux colonnes ligne par ligne et on garde le max
    df["nb_stimulations"] = (
        df[["nb_stimulations", "occurrence_clinical_effect"]].fillna(0).max(axis=1)
    )
    df = df[df["nb_stimulations"] > 0]

    # Calcul du total de stimulations pour chaque région (pour le ratio) avant le filtrage
    # Somme des stimulations pour chaque région (roi_id) sur toute la DB
    # total_stimulations_per_roi = df.groupby('roi_id')['nb_stimulations'].sum().reset_index()
    # total_stimulations_per_roi.rename(columns={'nb_stimulations': 'total_nb_stimulations'}, inplace=True)

    # On colle ce total dans le tableau principal pour chaque ligne correspondante à la région (roi_id)
    # df = pd.merge(df,total_stimulations_per_roi, on='roi_id', how='left')

    print("-" * 100)

    # Choix de la fonction
    # Menu Niveau 1 : Classe
    choix_classe = questionary.select(
        "Choose the effect class",
        choices=list(dict_effects.keys())
        + [questionary.Separator(), "Manually research"],
    ).ask()

    search_term = ""
    search_column = ""
    display_title = ""

    if choix_classe == "Manually research":
        search_term = questionary.text("Entry the term to search : ").ask()
        search_column = "effect_details"
        display_title = f"Research free : '{search_term}'"

    else:
        # Menu Niveau 2
        sous_categories = dict_effects[choix_classe]

        choix_descripteur = questionary.select(
            f"Class {choix_classe} - Choose the descriptor : ",
            # L'utilisateur peut choisir un des effets de niveau 2 ou tous les effets
            choices=sous_categories
            + [questionary.Separator(), f"All descriptors in '{choix_classe}'"],
        ).ask()

        # Si l'utilisateur veut toute la catégorie
        if choix_descripteur.startswith("All descriptors"):
            search_term = choix_classe
            search_column = "effect_class"
        else:
            search_term = choix_descripteur
            search_column = "effect_descriptor"

    # Filtrage des données : on ne garde que les lignes correspondantes
    print(f"Researching {search_term} in database...")

    df = df[
        df[search_column].astype(str).str.contains(search_term, case=False, na=False)
    ]

    if df.empty:
        print("No result found in database.")
        return

    import numpy as np

    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)

    df.loc[
        df.duplicated(subset=["source_id", "nb_stimulations", search_column, "roi_id"]),
        "nb_stimulations",
    ] = np.nan

    df.loc[
        df.duplicated(
            subset=["source_id", "occurrence_clinical_effect", search_column, "roi_id"]
        ),
        "occurrence_clinical_effect",
    ] = np.nan

    df["wilson_score"] = df.apply(
        lambda row: wilson_score(
            row["occurrence_clinical_effect"],
            row["nb_stimulations"],
            row["roi_id"],
        ),
        axis=1,
    )
    print(df[df["roi_id"] == 147])
    # Bloc d'agrégation
    agg = (
        # On rassemble les lignes par région (roi_id)
        df.groupby("roi_id")
        .agg(
            # On additionne les occurrences positives pour chaque region
            total_occurrence_clinical_effect=("occurrence_clinical_effect", "sum"),
            # On additionne les occurrences positives pondérées pour chaque région
            total_weighted_occurrence_clinical_effect=(
                "weighted_occurrence_clinical_effect",
                "sum",
            ),
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
            weighted_positive_ratio=lambda x: x[
                "total_weighted_occurrence_clinical_effect"
            ]
            / x["total_nb_stimulations"]
        )
        .assign(
            wilson_score=lambda x: x.apply(
                lambda row: wilson_score(
                    row["total_occurrence_clinical_effect"],
                    row["total_nb_stimulations"],
                    row["roi_id"],
                ),
                axis=1,
            )
        )
    )

    # Ajout des noms des parcels (Yale dict)
    def trouver_roi_name(row):
        id_courant = int(row["roi_id"])

        # On regarde dans le dictionnaire Yale si on trouve une correspondance
        if id_courant in roi_names:
            return roi_names[id_courant]

    # On applique cette fonction sur chq ligne pour créer la colonne roi_name
    agg["roi_name"] = agg.apply(trouver_roi_name, axis=1)

    # Préparation des données pour l'affichage
    top_n = 696
    final_agg = (
        agg.fillna(0)  # Remplace les valeurs NaN par 0 pour éviter les erreurs
        .sort_values(
            by="wilson_score", ascending=False
        )  # Tri par Wilson score décroissant
        .reset_index(drop=True)
    )

    n_show = min(len(final_agg), top_n)

    print(f"\nRégions Yale probables (Top {n_show})")
    print("-" * 110)
    print(
        f"{'Label':<5} {'Région Positive':<30} {'Wilson':>4} {'Pondéré (%)':>16} {'Brut (%)':>9} {'Nb stim':>8} {'Tot pond.':>14} {'Tot':>7}"
    )
    print("-" * 110)

    labels = []
    for i, row in final_agg.head(n_show).iterrows():
        roi_id_val = row["roi_id"]
        labels.append(roi_id_val)
        label = str(row.get("roi_name", "<inconnu>"))
        wilson = float(row.get("wilson_score", 0.0) or 0.0)
        weighted_ratio = float(row.get("weighted_positive_ratio", 0.0) or 0.0)
        ratio = float(row.get("total_positive_ratio", 0.0) or 0.0)
        nb = int(row.get("total_nb_stimulations", 0.0) or 0.0)
        tot_weighted = float(
            row.get("total_weighted_occurrence_clinical_effect", 0.0) or 0.0
        )
        tot = float(row.get("total_occurrence_clinical_effect", 0.0) or 0.0)

        # Coupe le nom du label si trop long
        label_display = (label[:27] + "...") if len(label) > 30 else label

        print(
            f"{roi_id_val:<5} "
            f"{label_display:<30} "
            f"{wilson:>4.2f} "
            f"{weighted_ratio * 100:>11.1f} {ratio * 100:>13.1f} {nb:>5d} "
            f"{tot_weighted:>15.2f} {tot:>14.2f}"
        )
        print("-" * 110)

    # Load Yale LUT file and modify RGB values based on wilson scores
    if os.path.exists(args.Yale_LUT):
        with open(args.Yale_LUT, "r") as lut_file:
            lut_lines = lut_file.readlines()

            # Create a mapping of roi_id to wilson score
            score_map = dict(zip(final_agg["roi_id"], final_agg["wilson_score"]))

            # Modify LUT file with colors
            modified_lut = []
            for line in lut_lines:
                # Skip comment lines and headers
                if line.strip().startswith("#") or not line.strip():
                    modified_lut.append(line)
                    continue

                parts = line.split()
                if len(parts) >= 8:  # IDX R G B A VIS MSH LABEL
                    try:
                        roi_id = int(parts[0])
                        if roi_id in score_map:
                            # Apply color based on wilson score
                            wilson = float(score_map[roi_id])
                            r, g, b = score_to_cold_hot(wilson)
                            # Preserve visibility, mesh, and label
                            label = " ".join(parts[7:])
                            modified_lut.append(
                                f"{roi_id:5d} {r:3d} {g:3d} {b:3d}        1  1  1    {label}\n"
                            )
                        else:
                            label = " ".join(parts[7:])
                            modified_lut.append(
                                f"{roi_id:5d} 64 64 64        0.1  1  1    {label}\n"
                            )
                    except (ValueError, IndexError):
                        modified_lut.append(line)
                else:
                    modified_lut.append(line)

            # Write modified LUT file
            output_lut = (
                args.Yale_LUT
                if args.overwrite
                else args.Yale_LUT.replace(".txt", f"_{search_term}_colored.txt")
            )
            with open(output_lut, "w") as lut_file:
                lut_file.writelines(modified_lut)

        print(f"\nModified LUT file saved to: {output_lut}")

    total_stimulations = final_agg["total_nb_stimulations"].sum()
    total_occurrences = final_agg["total_occurrence_clinical_effect"].sum()
    print(f"\nTotal stimulations: {int(total_stimulations)}")
    print(f"Total occurrences: {int(total_occurrences)}\n")

    # Group by source_id and sum nb_stimulations, removing duplicates
    df_dedup = df.drop_duplicates(subset=["source_id", "nb_stimulations"]).copy()
    sum_fonction = (
        df_dedup.groupby("source_id", as_index=False)
        .agg(
            {
                col: (
                    "first"
                    if col
                    not in [
                        "nb_stimulations",
                    ]
                    else "sum"
                )
                for col in df.columns
            }
        )["nb_stimulations"]
        .sum()
    )
    print(sum_fonction)

    df_dedup = df.drop_duplicates(
        subset=["source_id", "occurrence_clinical_effect"]
    ).copy()
    sum_fonction = (
        df_dedup.groupby("source_id", as_index=False)
        .agg(
            {
                col: (
                    "first"
                    if col
                    not in [
                        "occurrence_clinical_effect",
                        "weighted_occurrence_clinical_effect",
                    ]
                    else "sum"
                )
                for col in df.columns
            }
        )["occurrence_clinical_effect"]
        .sum()
    )
    print(sum_fonction)


main()
