import nibabel as nib
import numpy as np
import pandas as pd
import glob
import os
import argparse
import sys

def analyze_mask_overlap(labels_file, masks_folder):
    # Verify files/folders exist
    if not os.path.exists(labels_file):
        print(f"Error: Labels file '{labels_file}' not found.")
        sys.exit(1)
    if not os.path.exists(masks_folder):
        print(f"Error: Masks folder '{masks_folder}' not found.")
        sys.exit(1)

    # Load the labels file
    try:
        labels_img = nib.load(labels_file)
        labels_data = labels_img.get_fdata()
    except Exception as e:
        print(f"Error loading labels file: {e}")
        sys.exit(1)
    
    # Get all mask files from the folder
    mask_files = glob.glob(os.path.join(masks_folder, '*mask.nii*'))
    if not mask_files:
        print(f"No mask files found in {masks_folder}")
        sys.exit(1)
    
    results = []
    
    # Process each mask file
    for mask_file in mask_files:
        # Extract the ROI name from filename
        roi_name = os.path.basename(mask_file).split(' ')[0]
        
        try:
            # Load mask
            mask_img = nib.load(mask_file)
            mask_data = mask_img.get_fdata()
            
            # Get all voxels in the mask
            mask_voxels = labels_data[mask_data > 0]
            
            if len(mask_voxels) == 0:
                print(f"Warning: No overlap found for mask {roi_name}")
                continue
                
            # Count occurrences of each label value
            unique_labels, counts = np.unique(mask_voxels, return_counts=True)
            percentages = counts / len(mask_voxels)
            
            # Find the label with highest percentage
            max_label_idx = np.argmax(percentages)
            dominant_label = unique_labels[max_label_idx]
            
            # Create percentage breakdown string
            breakdown = '+'.join([f"{p:.3f}*{int(l)}" for p, l in zip(percentages, unique_labels)])
            
            results.append({
                'ROI': roi_name,
                'Dominant_Label': int(dominant_label),
                'Percentage_Breakdown': breakdown
            })
        
        except Exception as e:
            print(f"Error processing mask {mask_file}: {e}")
            continue
    
    if not results:
        print("No results generated. Check your input files.")
        sys.exit(1)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(results)
    output_file = 'roi_analysis.csv'
    df.to_csv(output_file, index=False)
    print(f"Analysis complete. Results saved to {output_file}")
    return df

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Analyze ROI mask overlaps with labeled data')
    parser.add_argument('labels_file', help='Path to the labels.nii.gz file')
    parser.add_argument('masks_folder', help='Path to the folder containing mask files')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run analysis
    analyze_mask_overlap(args.labels_file, args.masks_folder)

if __name__ == "__main__":
    main()
