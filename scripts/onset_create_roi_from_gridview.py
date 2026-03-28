#!/usr/bin/env python3

"""
Transform electrode coordinates and create masks from gridview txt file.

In the output directory, a labels mask and masks of each electrode will be saved as NIfTI files.
The electrode names and IDs will be saved in a lookup table.
"""

import argparse
import logging
import nibabel as nib
import numpy as np
import os

from onsetpy.image.mask import create_sphere_mask
from onsetpy.io.utils import (
    add_verbose_arg,
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
)
from onsetpy.utils.gridview import parse_gridview_file, transform_gridview_coordinates


def _build_arg_parser():
    """Build argparser.

    Returns:
        parser (ArgumentParser): Parser built.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("txt_file", help="Path to GridView txt file")
    parser.add_argument("reference", help="Path to reference NIfTI file")
    parser.add_argument("output_dir", help="Output directory for masks")
    parser.add_argument("--radius", type=int, default=2, help="Radius of the mask")

    add_verbose_arg(parser)
    add_overwrite_arg(parser)

    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()
    logging.getLogger().setLevel(logging.getLevelName(args.verbose))

    assert_inputs_exist(parser, [args.txt_file, args.reference])
    assert_outputs_exist(parser, args, args.output_dir, output_is_dir=True)

    # Load ref image
    logging.info("Loading ref image...")
    ref_img = nib.load(args.reference)
    ref_dims = ref_img.shape

    # Parse and transform electrodes
    logging.info("Parsing electrode coordinates...")
    electrodes, gridview_dims, voxel_size = parse_gridview_file(args.txt_file)

    # Get scaling factors from the image dimensions
    # Scaling factors are calculated by dividing the reference image dimensions by the gridview
    # dimensions
    scaling_factors = [t / g for t, g in zip(ref_dims, gridview_dims)]
    # Calculate the difference between the reference image voxel size and the gridview voxel size
    vox_factors = [t - g for t, g in zip(ref_img.header.get_zooms(), voxel_size)]

    os.makedirs(args.output_dir, exist_ok=True)
    logging.info(f"Created output directory: {args.output_dir}")

    # Create coordinate conversion log file
    lut_dict = {}
    labels = np.zeros(ref_dims)
    log_path = os.path.join(args.output_dir, "coordinate_conversions.txt")

    with open(log_path, "w") as log:
        log.write("Electrode Coordinate Transformations\n")
        log.write("====================================\n\n")
        log.write(f"{'Contact':<10} {'Original':<20} {'Transformed':<20} {'ID':<20}\n")
        log.write("-" * 70 + "\n")

        # Process each electrode
        for group, contacts in electrodes.items():
            for contact in contacts:
                gid = str(ord(group[0]))
                eid = contact["name"][1:]
                electrode_id = int(gid + eid)
                # Transform coordinates
                original_coords = contact["coordinates"]
                # Transform coordinates from gridview space to reference image space
                transformed_coords = transform_gridview_coordinates(
                    original_coords, scaling_factors, vox_factors, ref_dims
                )
                # Create mask for the electrode at the transformed coordinates
                mask = create_sphere_mask(
                    ref_dims, transformed_coords, radius=args.radius
                )
                labels[mask == 1] = electrode_id
                lut_dict[electrode_id] = contact["name"]
                # Save mask as NIfTI
                nib.save(
                    nib.Nifti1Image(mask, ref_img.affine),
                    os.path.join(args.output_dir, f"{contact['name']}.nii.gz"),
                )

                # Log the transformation
                log.write(
                    f"{contact['name']:<10} {str(original_coords):<20} "
                    f"{str(transformed_coords):<20} {electrode_id:<20}\n"
                )

    # Save labels and LUT
    nib.save(
        nib.Nifti1Image(labels, ref_img.affine),
        os.path.join(args.output_dir, "labels.nii.gz"),
    )
    lut_dict = dict(sorted(lut_dict.items()))
    lut_path = os.path.join(args.output_dir, "electrode_lut.txt")
    with open(lut_path, "w") as lut:
        for electrode_id, name in lut_dict.items():
            lut.write(f"{name} {electrode_id}\n")

    logging.info(f"Complete! Masks saved in {args.output_dir}")
    logging.info(f"Coordinate transformations logged in {log_path}")


if __name__ == "__main__":
    main()
