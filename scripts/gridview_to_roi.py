import nibabel as nib
import numpy as np
import argparse
from pathlib import Path
import re
from scipy.ndimage import generate_binary_structure, binary_dilation

def parse_electrodes(txt_path):
    """Extract electrode coordinates from GridView txt file"""
    with open(txt_path, 'r') as f:
        lines = f.readlines()
    
    electrodes = {}
    current_group = None
    
    for line in lines:
        line = line.strip()
        if line.startswith("Group:"):
            current_group = line.split(':')[1].strip()
            electrodes[current_group] = []
        elif current_group and re.match(r'^[A-Z]+[0-9]+:', line):
            parts = line.split(':')[1].strip().split('\t')
            if len(parts) >= 3:
                coords = [int(x) for x in parts[:3]]
                name = line.split(':')[0].strip()
                annotation = parts[3] if len(parts) > 3 else ''
                electrodes[current_group].append({
                    'name': name,
                    'coordinates': coords,
                    'annotation': annotation
                })
    
    return electrodes

def transform_coordinates(coords, scaling_factors, t1_dims):
    """Transform coordinates from GridView to T1 space"""
    # First apply scaling
    scaled_coords = [int(round(c * s)) for c, s in zip(coords, scaling_factors)]
    
    # Then flip X and Y axes
    transformed_coords = [
        t1_dims[0] - scaled_coords[0],  # Flip X
        t1_dims[1] - scaled_coords[1],  # Flip Y
        scaled_coords[2]                 # Z stays the same
    ]
    
    return transformed_coords

def create_sphere_mask(shape, center, radius=2):
    """Create a spherical mask centered at the given coordinates"""
    mask = np.zeros(shape, dtype=bool)
    
    # Ensure coordinates are within bounds
    x, y, z = [int(round(c)) for c in center]
    x = max(radius, min(x, shape[0]-radius-1))
    y = max(radius, min(y, shape[1]-radius-1))
    z = max(radius, min(z, shape[2]-radius-1))
    
    mask[x, y, z] = True
    
    # Create spherical structure
    struct = generate_binary_structure(3, 1)
    # Dilate to create sphere
    for _ in range(radius):
        mask = binary_dilation(mask, structure=struct)
    
    return mask.astype(np.int16)

def main():
    parser = argparse.ArgumentParser(description='Transform electrode coordinates and create masks')
    parser.add_argument('txt_file', help='Path to GridView txt file')
    parser.add_argument('nifti_file', help='Path to T1 NIfTI file')
    
    args = parser.parse_args()
    
    # Load T1 image
    print("Loading T1 image...")
    t1_img = nib.load(args.nifti_file)
    t1_dims = t1_img.shape
    
    # Get scaling factors from the image dimensions
    gridview_dims = [256, 256, 176]  # From the txt file
    scaling_factors = [t/g for t, g in zip(t1_dims, gridview_dims)]
    
    # Create output directory
    output_dir = Path(args.txt_file).stem + '_masks'
    Path(output_dir).mkdir(exist_ok=True)
    print(f"Created output directory: {output_dir}")
    
    # Parse and transform electrodes
    print("Parsing electrode coordinates...")
    electrodes = parse_electrodes(args.txt_file)
    
    # Create coordinate conversion log file
    log_path = Path(output_dir) / "coordinate_conversions.txt"
    with open(log_path, 'w') as log:
        log.write("Electrode Coordinate Transformations\n")
        log.write("==================================\n\n")
        log.write(f"{'Contact':<10} {'Original':<20} {'Transformed':<20}\n")
        log.write("-" * 50 + "\n")
        
        # Process each electrode
        for group, contacts in electrodes.items():
            for contact in contacts:
                if all(x != '' for x in map(str, contact['coordinates'])):  # Check if coordinates exist
                    # Transform coordinates
                    original_coords = contact['coordinates']
                    transformed_coords = transform_coordinates(
                        original_coords,
                        scaling_factors,
                        t1_dims
                    )
                    
                    # Create mask
                    mask = create_sphere_mask(t1_dims, transformed_coords)
                    
                    # Save mask as NIfTI
                    mask_img = nib.Nifti1Image(mask, t1_img.affine)
                    output_file = Path(output_dir) / f"{contact['name']}.nii.gz"
                    nib.save(mask_img, output_file)
                    
                    # Log the transformation
                    log.write(f"{contact['name']:<10} {str(original_coords):<20} {str(transformed_coords):<20}\n")
                    
                    print(f"Created mask for {contact['name']}")
    
    print(f"\nComplete! Masks saved in {output_dir}")
    print(f"Coordinate transformations logged in {log_path}")

if __name__ == "__main__":
    main()