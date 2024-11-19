#!/usr/bin/env python3

"""
Match electrodes to masks and create labels mask from gridview txt file.

In the output directory, a labels mask and masks of each electrode will be saved as NIfTI files.
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
    parser.add_argument("masks", nargs="+", help="Path to masks NIfTI file")
    parser.add_argument("output_dir", help="Output directory for masks")

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
    log_path = os.path.join(args.output_dir, "coordinate_match.txt")

    with open(log_path, "w") as log:
        log.write("Electrode Match Transformations\n")
        log.write("===============================\n\n")
        log.write(f"{'Contact':<10} {'Mask Name':<20} {'Coordinate':<20} {'ID':<20}\n")
        log.write("-" * 70 + "\n")

        # Process each electrode
        for mask_file in args.masks:
            mask_name = os.path.basename(mask_file).split(".")[0]
            mask_img = nib.load(mask_file)
            mask_data = mask_img.get_fdata()
            mask_matched = False
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
                    sphere_mask = create_sphere_mask(
                        ref_dims, transformed_coords, radius=2
                    )
                    overlap = np.logical_and(sphere_mask, mask_data)

                    if np.count_nonzero(overlap):
                        labels[mask_data == 1] = electrode_id
                        lut_dict[electrode_id] = contact["name"]
                        log.write(
                            f"{contact['name']:<10} {mask_name:<20} {str(transformed_coords):<20} {electrode_id:<20}\n"
                        )

                        mask_img = nib.Nifti1Image(mask_data, ref_img.affine)
                        output_file = f"{args.output_dir}/{contact['name']}.nii.gz"
                        nib.save(mask_img, output_file)
                        mask_matched = True
                        break
                if mask_matched:
                    break
            if not mask_matched:
                logging.warning(f"Mask {mask_name} does not match any electrode")

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
