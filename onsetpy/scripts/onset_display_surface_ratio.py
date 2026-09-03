#!/usr/bin/env python3

"""
Display a NIfTI volume (e.g. weighted_positive_ratio per Yale parcel) on the
brain surface using yabplot.
"""

import argparse
import os
import tempfile

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import yabplot as yab
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter, grey_dilation

from onsetpy.io.utils import (
    add_overwrite_arg,
    add_version_arg,
    assert_inputs_exist,
    assert_outputs_exist,
)

# Vivid yellow -> orange -> red, more saturated than matplotlib's built-in
# YlOrRd (which stays pale through the yellow/orange range).
YELLOW_ORANGE_RED = LinearSegmentedColormap.from_list(
    "yellow_orange_red", ["#FFFF00", "#FF8C00", "#FF0000"]
)
_CUSTOM_CMAPS = {"yellow_orange_red": YELLOW_ORANGE_RED}


def _resolve_cmap(name):
    return _CUSTOM_CMAPS.get(name, name)


def _build_arg_parser():
    """Build argparser.

    Returns:
        parser (ArgumentParser): Parser built.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "nifti",
        help="Path to the NIfTI volume to project on the surface "
        "(e.g. weighted_positive_ratio_<function>.nii.gz).",
    )
    parser.add_argument(
        "output",
        help="Path to the output image (e.g. .png).",
    )
    parser.add_argument(
        "--bmesh",
        default="midthickness",
        choices=["midthickness", "white", "pial", "inflated"],
        help="Brain mesh surface to project the volume on. [%(default)s]",
    )
    parser.add_argument(
        "--views",
        nargs="+",
        default=["left_lateral", "right_lateral"],
        help="Surface views to display. [%(default)s]",
    )
    parser.add_argument(
        "--cmap",
        default="yellow_orange_red",
        help="Colormap for the surface plot: 'yellow_orange_red' (custom, "
        "vivid) or any matplotlib colormap name. [%(default)s]",
    )
    parser.add_argument(
        "--vmin",
        type=float,
        help="Minimum value for the colormap. Defaults to the volume's min.",
    )
    parser.add_argument(
        "--vmax",
        type=float,
        help="Maximum value for the colormap. Defaults to the volume's max.",
    )
    parser.add_argument(
        "--colorbar_label",
        default="Weighted positive ratio",
        help="Label for the shared colorbar. [%(default)s]",
    )
    parser.add_argument(
        "--no_colorbar",
        action="store_true",
        help="Do not draw the colorbar.",
    )
    parser.add_argument(
        "--title",
        help="Title for the figure.",
    )
    parser.add_argument(
        "--background_value",
        type=float,
        default=0.0,
        help="Value in the input volume meaning 'no data' (e.g. parcels "
        "outside the studied ROI set). Masked to NaN before projection so "
        "it renders as background instead of the coldest colormap color. "
        "[%(default)s]",
    )
    parser.add_argument(
        "--dilate_voxels",
        type=int,
        default=2,
        help="Grow each parcel by this many voxels before projecting onto "
        "the surface. The cortical ribbon is thin, so small misalignments "
        "between this volume and yabplot's surface mesh make "
        "nearest-neighbor sampling miss it in places, producing a speckled "
        "look; dilating compensates for that. Set to 0 to disable. "
        "[%(default)s]",
    )
    parser.add_argument(
        "--gaussian_sigma",
        type=float,
        default=1.0,
        help="Sigma (in voxels) of the Gaussian filter applied to the volume "
        "before projection, to smooth transitions between parcels. Set to "
        "0 to disable. [%(default)s]",
    )

    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, [args.nifti])
    assert_outputs_exist(parser, args, [args.output])

    img = nib.load(args.nifti)
    data = img.get_fdata().astype(np.float32)

    if args.dilate_voxels > 0:
        data = grey_dilation(data, size=(2 * args.dilate_voxels + 1,) * 3)

    if args.gaussian_sigma > 0:
        data = gaussian_filter(data, sigma=args.gaussian_sigma)

    # mask 'no data' voxels to NaN so they render as background instead of
    # being colored as the coldest (or any) value on the colormap
    data[data == args.background_value] = np.nan
    masked_img = nib.Nifti1Image(data, img.affine)

    with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        nib.save(masked_img, tmp_path)

        # nearest-neighbor interpolation: the volume holds discrete
        # per-parcel values (like an atlas), so trilinear interpolation
        # (the default) would blur/smooth the parcel boundaries
        lh_data, rh_data = yab.project_vol2surf(
            tmp_path, bmesh=args.bmesh, interpolation="nearest"
        )
    finally:
        os.remove(tmp_path)

    # make vertex-wise brain meshes with the injected data
    b_lh_path, b_rh_path = yab.data.get_surface_paths(args.bmesh, "bmesh")
    lh_mesh, rh_mesh = yab.load_vertexwise_mesh(b_lh_path, b_rh_path, lh_data, rh_data)

    # project_vol2surf also masks the medial wall to NaN; use nanmin/nanmax
    # so NaNs (background + medial wall) don't collapse vmin/vmax to NaN,
    # which would render the whole surface as a single (blue) color.
    combined_data = np.concatenate([lh_data, rh_data])
    vmin = args.vmin if args.vmin is not None else float(np.nanmin(combined_data))
    vmax = args.vmax if args.vmax is not None else float(np.nanmax(combined_data))

    cmap = _resolve_cmap(args.cmap)

    fig, ax = plt.subplots(figsize=(10, 4))
    yab.plot_vertexwise(
        lh_mesh,
        rh_mesh,
        cmap=cmap,
        vminmax=[vmin, vmax],
        nan_color=(0.7, 0.7, 0.7),
        ax=ax,
        views=args.views,
        style="sculpted"
    )
    # yab adds its own colorbar axis; drop it, a labeled one is added below
    if len(fig.axes) > 1:
        fig.axes[-1].remove()

    if args.title:
        fig.suptitle(args.title, fontsize=14)

    if not args.no_colorbar:
        cbar = fig.colorbar(
            plt.cm.ScalarMappable(norm=plt.Normalize(vmin=vmin, vmax=vmax), cmap=cmap),
            ax=ax,
            orientation="horizontal",
            fraction=0.05,
            pad=0.05,
        )
        cbar.set_label(args.colorbar_label)

    fig.savefig(args.output, bbox_inches="tight", dpi=300, transparent=True)
    plt.close(fig)

    print(f"Surface plot saved to: {args.output}")


if __name__ == "__main__":
    main()
