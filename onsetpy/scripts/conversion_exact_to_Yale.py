"""
Conversion des coordonnées exactes en numéro de parcel Yale 
"""

import pandas as pd 
from scipy.spatial import cKDTree #Algortihme mathématique optimisé 
import numpy as np  
import re

    
def mapping_yale(df_db):
    
    #Fichiers des coordonnées Yale (X,Y,Z, nom de la parcel)
    coords_parcels = "https://raw.githubusercontent.com/YaleBrainAtlas/YaleBrainAtlas/refs/heads/master/data/YBA_690parcels/YBA_690_whole_positions.csv"
    
    #Noms des colonnes des fichiers de coordonnées 
    COL_COORD_X = 'x'
    COL_COORD_Y = 'y'
    COL_COORD_Z = 'z'
    COL_COORD_KEY = 'parcel'
    
    #Fichier dictionnaire qui permet d'assigner une valeur au nom de parcel 
    dict_file_path = "https://raw.githubusercontent.com/YaleBrainAtlas/YaleBrainAtlas/refs/heads/master/data/YBA_690parcels/YBA_690_parcel_dict.csv"
    
    #Noms des colonnes dans le dictionnaire 
    COL_DICT_KEY = 'Name'
    COL_DICT_LONGNAME = 'Long_name'
    
    
    #--- FONCTIONS UTILES ---
    #Conversion TALAIRACH to MNI (Lancaster Transform, 2007)
    def talairach_to_mni(xyz_list):
        """
        Traduction en Python du script Matlab 'tal2icbm_spm' (GingerALE)
        Utilise la transformation non affine de Lancaster (2007)
        Convertit une coordonnée de l'espace Talairach vers MNI
        """
        #Définition de la matrice fournie par Lancaster 
        #ICBM to TAL 
        
        icbm_pooled = np.array([
            [0.9357, 0.0029, -0.0072, -1.0423],
            [-0.0065, 0.9396, -0.0726, -1.3940],
            [0.0103, 0.0752, 0.8967, 3.6475],
            [0.0000, 0.0000, 0.0000, 1.0000]
        ])
        
        #Inversion de la matrice pour avoir TAL -> ICBM/MNI
        icbm_pooled_inv = np.linalg.inv(icbm_pooled)
        
        #Préparation du vecteur coordonnée [x, y, z, 1]
        #1 permet la multiplication matricielle 4x4
        point_tal = np.array(xyz_list + [1])
        
        #Application de la transformation (produit matriciel)
        point_mni = np.dot(icbm_pooled_inv, point_tal)
        
        #On retourne x, y, z dans la liste xyz et on enlève le 1 de fin
        return point_mni[:3].tolist()
    
    
    #Fonction pour convertir les coordonnées en floats 
    def conversion_coord(coord_str):
        
        #On prend chaque groupe de coordonnées (séparés par ,)
        groups = coord_str.split(',')
        list_coord_nb = []
        
        for group in groups:
            #Extraction de tous les nombres (entiers ou décimaux, positifs ou négatifs)
            #Nombres sont sous forme de string 
            numbers = re.findall(r'-?\d+\.?\d*', group)
            #Quand il a les trois coordonnées X Y Z
            if len(numbers) == 3:
                try:
                    #Conversion des coordonnées X Y Z en float 
                    xyz = [float(n) for n in numbers]
                    #Ajout des coordonnées à la liste finale des résultats
                    list_coord_nb.append(xyz)
                    #Si erreur : passer 
                except ValueError: pass 
        
        return list_coord_nb
            
    #--- EXECUTION ---
    print("1. Chargement des coordonnées de l'Atlas")
    df_coords = pd.read_csv(coords_parcels)
    
    #Arbre spatial avec les coordonnées de l'Atlas
    atlas_points = df_coords[[COL_COORD_X, COL_COORD_Y, COL_COORD_Z]].values
    tree = cKDTree(atlas_points)  
    #Permettra d'identifier rapidement quel point est le voisin le plus proche
    
    print("2. Chargement du dictionnaire avec le numéro des labels")
    df_dict = pd.read_csv(dict_file_path)
    
    #Dictionnaire 1 : Clé (Nom court) -> Num parcel 
    #zip permet d'assembler paire par paire l'élément A avec l'élément B
    #On met ca dans un dictionnaire pour une recherche + rapide 
    COL_DICT_VALUE = df_dict.index + 1 #Numéro de label = index + 1 (car index commence à 0)
    mapping_label = dict(zip(df_dict[COL_DICT_KEY], COL_DICT_VALUE))         
    
    #Dictionnaire 2 : Clé (Nom court) -> Long Name 
    mapping_names = dict(zip(df_dict[COL_DICT_KEY], df_dict[COL_DICT_LONGNAME]))    
    
    print("3. Traitement de la base de données : Conversion en label Yale")
    df_db = df_db.copy() #On travaille sur une copie du dataframe d'entrée pour éviter de modifier l'original

    final_label_list = []
    final_longname_list = []
    final_name_list = []
    dist_list = []
    
    #Passage en revue de toutes les lignes du fichier d'entrée (DB cleaned)
    for idx, row in df_db.iterrows():
        method = str(row.get('roi_mask_conversion_method', '')).lower()
        raw_coords = row.get('roi_mask', '')
        
        #Si la localiastion est exacte et que les coordonnées sont pas vides
        if 'exact' in method and len(raw_coords) > 0:
            
            #Détection Talairach 
            need_conversion = False
            if raw_coords[0] == 'T':
                need_conversion = True
            
            coords_patient_db = conversion_coord(str(raw_coords))
            
            row_labels = []
            row_longnames = []
            row_names = []
            row_dists = []
            
            for pt_xyz in coords_patient_db:
                #Conversion si Talairach
                current_pt = pt_xyz
                if need_conversion:
                    current_pt = talairach_to_mni(pt_xyz)
                
                #1. Recherche de voisin : on donne les coordonnées xyz 
                #On récupère le point le plus proche et sa distance
                dist, index = tree.query(current_pt)
                
                #2. Récupération de la clé (short name) 
                #Placement à la ligne de l'index (pt le plus proche) 
                #Récupèration du short name (key) de la parcelle
                found_key = df_coords.iloc[index][COL_COORD_KEY]
                
                #3. Recherche de la clé dans le Dictionnaire pour avoir le num_vertex (label value)
                #On regarde dans les dictionnaires la valeur de label et le long name pour la key 
                found_label = mapping_label.get(found_key)
                found_longname = mapping_names.get(found_key)
                
                row_labels.append(str(found_label))
                row_names.append(str(found_key)) #KEY
                row_dists.append(f"{dist:.1f}")
                row_longnames.append(str(found_longname))
            
            #On colle tous les résultats ensembles avec des virgules    
            final_label_list.append(",".join(row_labels))
            final_name_list.append(",".join(row_names)) #KEY
            dist_list.append(",".join(row_dists)) 
            final_longname_list.append(",".join(row_longnames))
            
        else:
            final_label_list.append("")
            final_name_list.append("")
            dist_list.append("")
            final_longname_list.append("")
    
    #Sauvegarde
    df_db['yale_long_name'] = final_longname_list
    df_db['yale_label'] = final_label_list
    df_db['yale_distance_mm'] = dist_list
    
    return df_db

