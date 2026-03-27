#!/usr/bin/env python3
"""
Get label ID in Yale atlas by brain function.
Interactive function search

Note :
Difference entre les deux scores stim total pour Sensory All Descriptors quand on inclut les fonctions exactes (surement probleme de ROI exact non convertit en yale cf Excel)
"""

import argparse
import os
import questionary
import requests
from dict_effects import dict_effects
import pandas as pd
import ast
import matplotlib.cm as cm
import math
import numpy as np

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

def parse_roi_list(val) : 
    #On découpe par virgule et on convertir en str
    id = str(val).split(",")
    #Retrait des doublons
    unique_ids = list(set(id))
    return unique_ids

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
    #Possibilité d'exclure les fonctions exactes : question yes/no
    exclure_exact = questionary.confirm("Voulez-vous exclure les fonctions exactes ?").ask()
    if exclure_exact : 
        #On filtre le tableau : on garde tout sauf les lignes qui ont exact comme méthode de conversion
        df = df[df["roi_mask_conversion_method"] != "exact"]
    
    print("-"*100)

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

    #On met dans le dataframe que ce correspond à la recherche (effet voulu)
    df = df[
        df[search_column].astype(str).str.contains(search_term, case=False, na=False)
    ]

    #Création de la liste de ROI unifiée 
    df["roi_list"] = df["roi_unified"].apply(parse_roi_list)

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

    #Calcul du poids 
    df["weight"] = df["roi_list"].apply(lambda x : 1/len(parse_roi_list(x)))
    df["weighted_occurrence_clinical_effect"] = (df["occurrence_clinical_effect"] * df["weight"])

    #Calcul du nombre total de stimulation pour la fonction
    total_stim_positives_per_function = df["occurrence_clinical_effect"].sum()
    print(f"Nombre total de stimulations positives pour la fonction : {total_stim_positives_per_function}")
    #Calcul du nombre total de stimulation pondérées pour la fonction
    weighted_total_stim_positives_per_function = df["weighted_occurrence_clinical_effect"].sum()

    #On explose par région : 1 ROI par ligne
    df = df.explode("roi_list").dropna(subset=["roi_list"]).reset_index(drop=True)

    #On nettoie et on crée la colonne 'roi_id' propre
    #On garde que des chiffres
    df = df[df["roi_list"].astype(str).str.strip().str.isnumeric()]

    # On crée la colonne roi_id en entier
    df["roi_id"] = df["roi_list"].astype(int)

    #Bloc d'agrégation
    agg = (
        #On rassemble les lignes par région (roi_id)
        df.groupby("roi_id")
        .agg(
            #Calcul de la somme des occurrences cliniques pour chaque région
            total_occurrence_clinical_effect = ("occurrence_clinical_effect", "sum"),
            #Calcul de la somme des occurrences cliniques pondérées pour chaque région
            total_weighted_occurrence_clinical_effect = ("weighted_occurrence_clinical_effect", "sum"),
        )
        .reset_index()
        .assign(
            #Ratio brut = nbre total d'occurrence clinique pour la région / nombre total de stimulations positives pour la fonction
            total_positive_ratio = lambda x: x["total_occurrence_clinical_effect"] / total_stim_positives_per_function,
            #Ratio pondéré (permet d'avoir des résultats sur 100)
            weighted_positive_ratio = lambda x: x["total_weighted_occurrence_clinical_effect"] / total_stim_positives_per_function,
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
    top_n = 10
    final_agg = (
        agg.fillna(0)  # Remplace les valeurs NaN par 0 pour éviter les erreurs
        .sort_values(
            by="weighted_positive_ratio", ascending=False
        )  # Tri par ratio pondéré score décroissant
        .reset_index(drop=True)
    )

    n_show = min(len(final_agg), top_n)

    print(f"\nRégions Yale probables (Top {n_show})")
    print("-" * 110)
    print(
        f"{'Label':<5} {'Région Positive':<30} {'Pondéré (%)':>16} {'Brut (%)':>9} {'Tot occ pond.':>14} {'Tot occ':>7}"
    )
    print("-" * 110)

    labels = []

    for i, row in final_agg.head(n_show).iterrows():
        roi_id_val = row["roi_id"]
        labels.append(roi_id_val)
        label = str(row.get("roi_name", "<inconnu>"))
        weighted_ratio = float(row.get("weighted_positive_ratio", 0.0) or 0.0)
        ratio = float(row.get("total_positive_ratio", 0.0) or 0.0)
        tot_weighted = float(
            row.get("total_weighted_occurrence_clinical_effect", 0.0) or 0.0
        )
        tot = float(row.get("total_occurrence_clinical_effect", 0.0) or 0.0)

        # Coupe le nom du label si trop long
        label_display = (label[:27] + "...") if len(label) > 30 else label

        print(
            f"{roi_id_val:<5} "
            f"{label_display:<30} "
            f"{weighted_ratio * 100:>11.1f} {ratio * 100:>13.1f}"
            f"{tot_weighted:>15.2f} {tot:>14.2f}"
        )
        print("-" * 110)

        """
        # EXPORT POUR VÉRIFICATION MANUELLE
        print("\n--- TABLEAU DÉTAILLÉ POUR CALCUL MANUEL ---")
        
        # On sélectionne uniquement les colonnes utiles pour comprendre le calcul
        colonnes_a_afficher = [
            "id",
            "source_id", 
            "roi_id", 
            "occurrence_clinical_effect", 
            "weight", 
            "weighted_occurrence_clinical_effect"
        ]
        
        # On crée un sous-tableau avec ces colonnes
        df_verif = df[colonnes_a_afficher].copy()
        
        # On affiche tout le tableau dans la console (sans tronquer les lignes)
        print(df_verif.to_string(index=False))
        print("-------------------------------------------\n")

        #On génère un fichier pour l'ouvrir dans Excel
        nom_fichier_verif = f"verification_manuelle_{search_term.replace(' ', '_')}.xlsx"
        df_verif.to_excel(nom_fichier_verif, index=False)
        print(f"Fichier exporté pour Excel : {nom_fichier_verif}\n")    
        """

    #Sécurité : on revérifie le nombre total d'occurrences en enlevant les déduplicant 
    df_dedup = df.drop_duplicates(
        subset=["id"]
    ).copy()

    sum_fonction = df_dedup["occurrence_clinical_effect"].sum()
    print(sum_fonction)

    """Etape de visualisation : Heatmap on Yale Brain Atlas"""
    #dict_visualisation = dict(zip(final_agg["roi_id"], final_agg["weighted_positive_ratio"]*100))

    #from results_visualisation_on_YBA import visualize_heatmap_on_yba 
    #visualize_heatmap_on_yba(dict_visualisation, search_term)

    """Création d'une LUT pour visualisation sur ITK-Snap ou autre"""
    """
    #Charger la Yale LUT et modifier les valeurs RGB sur la base du weighted positive ratio
    lut_url = "https://raw.githubusercontent.com/YaleBrainAtlas/YaleBrainAtlas/refs/heads/master/data/YBA_690parcels/YBA_690_ITKlabels.txt"

    #On télécharge le contenu du fichier texte de la LUT depuis GitHub
    response = requests.get(lut_url)

    #Créer un mapping de roi_id à weighted positive ratio
    score_map = dict(zip(final_agg["roi_id"], final_agg["weighted_positive_ratio"]))
        
    #Modifier la LUT avec les couleurs souhaitées 
    modified_lut = []

    #On traite la LUT ligne par ligne : 
    #si le roi_id est dans notre score_map, on applique la couleur correspondante, 
    #sinon on met une couleur neutre (gris)
    for line in response.text.splitlines():
        #Skip comment lines and headers
        if line.strip().startswith("#") or not line.strip():
            modified_lut.append(line)
            continue

        parts = line.split()
        if len(parts) >= 8:  # IDX R G B A VIS MSH LABEL
            try:
                roi_id = int(parts[0])
                if roi_id in score_map:
                    # Apply color based on weighted positive ratio
                    weighted_ratio = float(score_map[roi_id])
                    r, g, b = score_to_cold_hot(weighted_ratio)
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

    # Write modified LUT file locally
    output_lut = f"YBA_690_ITKlabels_{search_term}_colored.txt"
        
    with open(output_lut, "w", encoding="utf-8") as lut_file:
        lut_file.writelines(modified_lut)

    print(f"\nModified LUT file saved to: {output_lut}")
    """

main()
