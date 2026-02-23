# -*- coding: utf-8 -*-
"""
Processing of Database for SPACES project
"""
import pandas as pd
import sqlite3
import re
import os 
import conversion_exact_to_Yale 
import openpyxl

#Configuration
#Nom du fichier d'entrée
input_db_filename = 'DB_14oct.db'

#Chemin du dossier 
db_localisation = r'G:\SPACES'
#db_localisation = r'/Users/eli/Desktop/CHUM/SPACES'

#Combinaison du chemin de la DB
path_db = os.path.join(db_localisation, input_db_filename)

#Dictionnaires pour chaque niveau 1 d'effets
dict_effects = {
    "[Responsive rate]": [
        ],
    "Consciousness": [
        "Imp Awareness",
        "Imp Responsiveness",
        "Imp awar & resp",
        "Other"
        ],
    "Sensory": [
        "Auditory",
        "Gustatory",
        "Olfactory",
        "Somatosensory",
        "Vestibular",
        "Visual",
        "Body illusion",
        "Other"
        ],
    "Affective": [
        "Anger",
        "Anxiety",
        "Fear",
        "Sadness",
        "Guilt",
        "Mirth",
        "Ecstatic",
        "Mystic",
        "Sexual",
        "Other"
        ],
    "Cognitive" : [
       "Dysphasic",
       "Dysmnesic",
       "Time allusion",
       "Forced thinking",
       "Depersonalisation",
       "Other"
       ],
    "Motor Elementary": [
        "Akinetic",
        "Astatic",
        "Atonic",
        "Paretic",
        "Dystonic",
        "Tonic",
        "Spasms",
        "Myoclonic",
        "Myoclonic-atonic",
        "Tonic-clonic",
        "Eye blinking",
        "Eye & head & dev",
        "Gyration",
        "Other elementary motor"
        ],
    "Motor Complex": [
        "Affect related behav",
        "Axial automatisms",
        "Distal automatisms",
        "Proximal automatisms",
        "Oral automatisms",
        "Verbal automatisms",
        "Wandering",
        "Other complex motor",
        ],
    "Autonomic": [
        "CardioVascular",
        "Cutaneous",
        "GastroIntestinal",
        "Lacrimatory",
        "Pupillary",
        "Respiratory",
        "Urinary",
        "Other"
        ],
}


#--- Définition de fonctions utiles ---
def expand_roi_mask_approx(mask_value):
    """ 
    Fonction qui éclate les intervalles
    Pour approx_from_text ou approx_from_figure
    """
    
    result = []
    
    #Séparation par virgule
    parts = [p.strip() for p in mask_value.split(',')]

    #Regarde le contenu entre les virgules
    for part in parts :
        #Détection des intervalles (début et fin)
        #Prise en compte des espaces par \s* 
        intervalle = re.match(r'^\s*(\d+)\s*-\s*(\d+)\s*$', part)
        
        if intervalle:
            try:
                int1 = int(intervalle.group(1))
                int2 = int(intervalle.group(2))
                
                #On trie pour avoir min-max (pas toujours dans le bon ordre dans la DB)
                start = min(int1, int2)
                end = max(int1, int2)

                #On liste tous les nombres de l'intervalle
                #range(start, end + 1) génère les nombres entre le début et la fin de l'intervalle (inclus)
                result.extend([str(i) for i in range(start, end + 1)])                
            except ValueError :
                result.append(part)
        else:
            #Si pas de tiret, on ajoute la valeur telle quelle
            result.append(part)
            
    return result 

def expand_roi_mask_exact(mask_value):
    """ 
    Fonction qui repère les groupes de parenthèses  (position exacte)
    Lorsque la ROI est indiquée exactement dans l'article
    Distinction des triplets
    Détection des coordonnées Talairach et conservation de l'indice T
    """
    final_masks = []
    
    #Détection de l'indice Talairach
    is_talairach = False
    clean_str = str(mask_value).strip().upper()
    if clean_str.startswith('T'):
        is_talairach = True
    
    #Pour capturer tout ce qui est entre parenthèses (...)
    contents = re.findall(r'\(([^)]+)\)', mask_value)
    
    if contents:
        for content in contents :
            #On enleve les espaces inutiles 
            content = content.strip()
            
            #Cas : Contient déjà des slashs
            if '/' in content:
                #Si plusieurs triplets sont séparés par des virgules 
                #On sépare chaque morceau
                parts = [p.strip() for p in content.split(',')]
                
                for p in parts:
                    if p:
                        #On nettoie les espaces autour des slashs
                        clean_p = re.sub(r'\s*/\s*', '/', p)
                        #On met entre parenthèse le triplet 
                        coord_str = f"({clean_p})"
                        
                        #Si c'est du Talairach, on remet le T
                        if is_talairach:
                            coord_str = "T" + coord_str
                            
                        final_masks.append(coord_str)
          
            #Cas : Pas de slash, utilise probablement des virgules  
            else:
                #On sépare par virgule
                parts = [p.strip() for p in content.split(',')]
                #On rejoint avec des slashs 
                clean_p = '/'.join(parts)
                coord_str = f"({clean_p})"
                
                #Si c'est du Talairach, on remet le T
                if is_talairach:
                    coord_str = "T" + coord_str
                    
                final_masks.append(coord_str)
        
        return final_masks 
                
    else:
        #Si aucune parenthèse trouvée, on garde la valeur d'origine
        return [mask_value]
    
    
def cleaning_row(row_data, dict_effects):
    """
    Cleaning des ROI et des effets
    """    
    #--- Traitement de la ROI --- 
    #Suppression des espaces vides inutiles
    method = row_data['roi_mask_conversion_method']
    original_mask = str(row_data['roi_mask']).strip()
    
    #Correction des erreurs d'insertion (MNI/TAL -> exact)
    if '/' in original_mask or ('(' in original_mask and ',' in original_mask): 
        method = 'exact'
        #Mise à jour de la donnée pour le tableau de sortie
        row_data['roi_mask_conversion_method'] = 'exact'
    
    
    #Condition du traitement des ROI = methode de conversion
    expanded_masks = []
    if method in ['approx_from_text', 'approx_from_figure']:
        #Approx = on éclate les virgules et les intervalles
        expanded_masks = expand_roi_mask_approx(original_mask)
        
    elif method == 'exact':
        #Exact = on éclate par parenthèse 
        expanded_masks = expand_roi_mask_exact(original_mask)
        
    else :
        #Sinon, on garde tel quel
        expanded_masks = [original_mask] #A GARDER OU SUPPRIMER 

    #Filtrage des ROI > 696
    filtered_masks = []
    if method!= 'exact': #On ne filtre pas les coordonnées exactes
        for mask in expanded_masks:
            mask_str = str(mask).strip()
            try:
                val = int(mask_str)
                if 0 < val <= 696:
                    filtered_masks.append(mask_str)
            except ValueError:
                pass #Si ca plante on ignore  
    #Si méthode exact, on garde les coordonnées sans y toucher
    else:
        filtered_masks = expanded_masks
            
    #Regroupement par , de la ROI
    row_data['roi_mask'] = ",".join([x for x in filtered_masks])

    #--- TRAITEMENT DES EFFETS ---
    #Lecture des contenus des colonnes
    raw_desc = str(row_data['effect_descriptor']) if row_data['effect_descriptor'] else ""
        
    
    #Liste des descripteurs bruts, prise en compte des séparations par , ; / et \
    descriptors = [d.strip() for d in re.split(r'[;,\n\r/\\]', raw_desc)]
   
    found_classes = set() 
    
    valid_descriptors = []
    seen_valid_descriptors = set()
    
    orphelins = []
    seen_orphelins = set() 
    
    #Recherche des descripteurs
    for desc in descriptors:
        desc_clean = desc.strip(' ,.')
        found_match = False
        
        #On regarde dans le dictionnaire des classes d'effects si le descripteur est présent 
        for classe_ref, liste_mots_ref in dict_effects.items():
            liste = [m for m in liste_mots_ref]
            #Si le descripteur appartient à une classe : on l'ajoute aux classes trouvées 
            if desc_clean in liste:
                found_classes.add(classe_ref)
                found_match = True
        
        #Si le descripteur appartient à une classe : on le garde
        if found_match:
            if desc not in seen_valid_descriptors:
                valid_descriptors.append(desc_clean)
                seen_valid_descriptors.add(desc_clean)
        #Le descripteur n'appartient pas à une classe = orphelin
        else:
            if desc not in seen_orphelins:
                orphelins.append(desc_clean)
                seen_orphelins.add(desc_clean)
    
    #Mise à jour des Classes
    #Résolution du problème : descripteur sans classe mais classe présente dans le dictionnaire
    if found_classes and not row_data['effect_class']:
        #Classe trouvée via le dictionnaire à partir du descripteur
        #On ajoute la classe à la ligne (on ecrase et reforme la ligne)
        existing_classes = [c.strip() for c in str(row_data['effect_class']).split(',')]
        for c in existing_classes:
            found_classes.add(c)
        row_data['effect_class'] = ",".join(sorted(list(found_classes)))
     
    #Mise à jour des descripteurs 
    #Suppression des orphelins des descripteurs
    row_data['effect_descriptor'] = ",".join(valid_descriptors)
    
    #Mise à jour des Détails avec les orphelins
    #---Ajout des orphelins au detail ---            
    if orphelins:
        orphelins_liste = ",".join(orphelins)
        original_details = str(row_data['effect_details']) if pd.notna(row_data['effect_details']) else ""
        
        if orphelins_liste not in original_details:
            #On ajoute les orphelins à la suite
            if original_details == "":
                row_data['effect_details'] = orphelins_liste
            else:
                row_data['effect_details'] = original_details.strip() + "," + orphelins_liste
    
    
    #Nettoyage final
    #Remplacement des ; par , pour les 3 colonnes des effets
    cols_to_replace = ['effect_class', 'effect_descriptor', 'effect_details']
    
    for col in cols_to_replace:
        if row_data[col]:
            clean_data = str(row_data[col]).replace(';',',')
            
            #Suppression des espaces avant/après la virgule dans Details
            if col == "effect_details":
                #Fonction qui donne mot1,mot2 
                clean_data = re.sub(r'\s*,\s*', ',', clean_data)
            row_data[col] = clean_data
        
    return row_data
         
       
#--- EXECUTION --- 
    
#Connexion à la base de données 
connexion = sqlite3.connect(path_db)

#Sélection des colonnes souhaitées 
query = """SELECT id, source_id, roi_side, roi_description, roi_mask, roi_mask_conversion_method, effect_class, effect_descriptor, effect_details, occurrence_clinical_effect, nb_stimulations FROM Results"""

df = pd.read_sql_query(query, connexion)

connexion.close()

#Traitement des données
final_rows = []
deleted_id = [] #Liste pour stocker les IDs supprimés
  
#Boucle pour chaque ligne de la base de données
for idx, row in df.iterrows():

    #Nettoyage des lignes où la ROI est vide
    raw_mask = row['roi_mask']
    
    #On enleve les espaces vides inutiles et on vérifie si la ROI est vide ou nulle
    if str(raw_mask).strip() == "" or pd.isna(raw_mask):
        #Si vide : on note l'ID et on passe à la ligne suivante 
        deleted_id.append(row['id'])
        continue 
        
    #On met la ligne dans un dictionnaire pour le traitement 
    row_dict = row.to_dict()

    #On applique le cleaning des lignes 
    processed_row = cleaning_row(row_dict, dict_effects)

    #Check : si c'est devenu vide après le nettoyage, on supprime la ligne
    if str(processed_row['roi_mask']).strip() == "" or pd.isna(processed_row['roi_mask']):
        deleted_id.append(row['id'])
    else:
        #Si c'est pas vide on garde 
        final_rows.append(processed_row)
                           
#Création du nouveau tableau
processed_df = pd.DataFrame(final_rows)

print(f"Lignes supprimées car ROI vide : {len(deleted_id)}")
if deleted_id:
    print(f"IDs supprimés : {deleted_id}")

print("Lancement de la conversion des coordonnées exacts en labels Yale...")

#Appel de la fonction qui convertie la position exacte en label Yale
df_final = conversion_exact_to_Yale.mapping_yale(processed_df)

print("Création de la colonne 'unified_roi_mask' qui regroupe les ROI Yale et les ROI exactes...")
"""Choix de la colonne ROI selon méthode de conversion : 
        - si method "exact" : prendre dans 'yale_label'
        - si method "approx" : prendre dans 'roi_mask'
"""
#Sélection de la colonne ROI
def select_roi_source(row):
    method = str(row.get('roi_mask_conversion_method', ''))
        
    #Si méthode de conversion exact -> on prend la colonne yale_label
    if method == 'exact':
        val = row.get('yale_label', '')
    else:
        val = row.get('roi_mask', '')
        
    return str(val)
        
#On met dans une nouvelle colonne les ROI Yale (traitement de la df ligne par ligne)
df_final['unified_roi'] = df_final.apply(select_roi_source, axis=1)



#Export vers CSV
base_name = os.path.splitext(input_db_filename)[0]
output_csv_filename = f"processed_{base_name}.csv"
output_path = os.path.join(db_localisation, output_csv_filename)
df_final.to_csv(output_path, index=False)

#Export vers Excel
output_excel_filename = f"processed_{base_name}.xlsx"
output_path = os.path.join(db_localisation, output_excel_filename)
df_final.to_excel(output_path, index=False)

print(f"TERMINÉ ! Fichier : {output_excel_filename} et {output_csv_filename} créés dans {db_localisation}")










