 # -*- coding: utf-8 -*-
"""
Visualiser les réponses en parcelles 3D nettes avec yabplot.

Télécharger YBA_690_ITKlabels.txt

Modifier chemin ligne 54
"""
import yabplot as yab
import numpy as np
import pandas as pd
import os
import re


#A LANCER POUR CREER LES FICHIERS NÉCESSAIRES À LA VISUALISATION (À LANCER UNE SEULE FOIS, PAS BESOIN DE RÉPÉTER À CHAQUE FOIS)
"""
# define where your source NIfTI and text files are located
# you can download the same atlas for this tutorial in here:
yba_txt = r"G:\SPACES\YBA690\YBA_690_ITKlabels.txt"
yba_nii = r"G:\SPACES\YBA690\YBA_690.nii"

dir_full_subcortical = r"G:\SPACES\YBA690\YBA_690"

atlas_labels = {}

with open(yba_txt, 'r') as f:
    for line in f:
        # 1. On ignore les lignes vides et les commentaires (qui commencent par #)
        if not line.strip() or line.strip().startswith('#'):
            continue
                
        # 2. On s'assure que la ligne contient bien des guillemets
        if '"' in line:
            # L'IDX est le tout premier élément de la ligne (avant les espaces)
            idx = int(line.split()[0])
                
            # Le LABEL est exactement ce qui se trouve entre les guillemets
            label = line.split('"')[1]
                
            # 3. On n'ajoute au dictionnaire que si IDX >= 1
            if idx >= 1:
                atlas_labels[idx] = label

# --- Test de vérification ---
print(f"Succès : {len(atlas_labels)} régions ajoutées au dictionnaire.")

yab.build_subcortical_atlas(
    nii_path=yba_nii,
    labels_dict=atlas_labels,
    out_dir=dir_full_subcortical,
    smooth_f=0.2,
    smooth_i=20)
"""

def visualize_heatmap_on_yba(dict_visualisation, search_term): 
    
    yba_txt = "G:\SPACES\YBA690\YBA_690_ITKlabels.txt"

    data_pour_yabplot = {}
    with open(yba_txt, 'r') as f:
        for line in f:
            if '"' in line:  # Si c'est bien une ligne avec une région
                idx = int(line.split()[0])
                label = line.split('"')[1]
                
                # Si cet ID fait partie des résultats, on le lie directement à son label
                if idx in dict_visualisation:
                    # On nettoie le label comme yabplot l'a sauvegardé
                    clean_label = label.replace(' ', '_').replace('/', '-')
                    data_pour_yabplot[clean_label] = dict_visualisation[idx]

    print(f"Lancement de yabplot (génération 3D) pour : {search_term}...")

    # 1. On trouve le score le plus haut dans les résultats actuels
    score_max = max(data_pour_yabplot.values())

    # Visualisation
    yab.plot_subcortical(
        atlas='custom',
        custom_atlas_path=r"G:\SPACES\YBA690\YBA_690",
        data=data_pour_yabplot,         
        cmap='jet',                  
        vminmax=[0,score_max],              
        views = ['left_lateral', 'right_lateral'] 
    )
