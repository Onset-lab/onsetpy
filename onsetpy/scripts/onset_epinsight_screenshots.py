"""
This script generates axial, coronal, and sagittal slices from T1 and Bernarsconi images
and visualizes them with crosshairs based on coordinates. The script
supports multiple images, allowing users to specify titles and colormaps for each image.
"""

import argparse
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt

from onsetpy.io.utils import (
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    add_version_arg,
)


def get_slices(
    image: np.ndarray, coords: tuple
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extracts axial, coronal, and sagittal slices from a 3D image based on the given coordinates.

    Parameters:
        image (numpy.ndarray): A 3D array representing the image volume.
        coords (tuple): A tuple of three integers (x, y, z) representing the coordinates
                        for slicing along the sagittal, coronal, and axial planes respectively.

    Returns:
        tuple: A tuple containing three 2D arrays:
               - axial (numpy.ndarray): The slice along the axial plane (z-axis).
               - coronal (numpy.ndarray): The slice along the coronal plane (y-axis).
               - sagittal (numpy.ndarray): The slice along the sagittal plane (x-axis).
    """

    x, y, z = coords
    axial = image[:, :, z]
    coronal = image[:, y, :]
    sagittal = image[x, :, :]
    return axial, coronal, sagittal


def plot_slices(
    axial: np.ndarray,
    coronal: np.ndarray,
    sagittal: np.ndarray,
    coords: tuple[int, int, int],
    title: str,
    axes: np.ndarray,
    row: int,
    cmap: str = "gray",
    vmin: float = None,
    vmax: float = None,
) -> None:
    """
    Plots axial, coronal, and sagittal slices of 3D medical imaging data with crosshairs
    and optional intensity range.
    Parameters:
        axial (ndarray): 2D array representing the axial slice.
        coronal (ndarray): 2D array representing the coronal slice.
        sagittal (ndarray): 2D array representing the sagittal slice.
        coords (tuple): Tuple of (x, y, z) coordinates for the crosshairs.
        title (str): Title for the row of plots.
        axes (ndarray): 2D array of matplotlib Axes objects for plotting.
        row (int): Row index in the axes array where the slices will be plotted.
        cmap (str, optional): Colormap for the slices. Default is "gray".
        vmin (float, optional): Minimum intensity value for the colormap. Default is None.
        vmax (float, optional): Maximum intensity value for the colormap. Default is None.
    Notes:
        - The function adds crosshairs at the specified coordinates on each slice.
        - Labels for left (L), right (R), posterior (P), and anterior (A) are added
          to the slices for orientation.
        - Axes ticks are hidden for a cleaner visualization.
    Returns:
        None
    """
    x, y, z = coords

    args = [
        [0, axial, y, x, "Axial", "R", "L"],
        [1, coronal, z, x, "Coronal", "R", "L"],
        [2, sagittal, z, y, "Sagittal", "P", "A"],
    ]
    for i, slice_data, line1, line2, title, left_label, right_label in args:
        axes[row, i].imshow(
            slice_data.T, cmap=cmap, origin="lower", vmin=vmin, vmax=vmax
        )
        axes[row, i].axhline(y=line1, color="blue", linestyle="--")
        axes[row, i].axvline(x=line2, color="blue", linestyle="--")
        axes[row, i].set_title(f"{title} - {title}")
        axes[row, i].set_xticks([])
        axes[row, i].set_yticks([])
        axes[row, i].text(
            5,
            slice_data.shape[1] - 5,
            left_label,
            color="white",
            fontsize=12,
            ha="left",
            va="top",
        )
        axes[row, i].text(
            slice_data.shape[0] - 5,
            slice_data.shape[1] - 5,
            right_label,
            color="white",
            fontsize=12,
            ha="right",
            va="top",
        )


def _build_arg_parser():
    """Build argparser.

    Returns:
        parser (ArgumentParser): Parser built.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--image_paths",
        nargs="+",
        required=True,
        help="Paths to the NIfTI images.",
    )
    parser.add_argument(
        "--titles",
        nargs="+",
        required=True,
        help="Titles for each image.",
    )
    parser.add_argument(
        "--cmaps",
        nargs="+",
        required=True,
        help="Colormaps for each image.",
    )
    parser.add_argument(
        "--coord",
        type=int,
        nargs=3,
        required=True,
        help="Coordinates (x, y, z) for the slices.",
    )
    parser.add_argument(
        "--output_path",
        required=True,
        help="Path to save the output figure.",
    )
    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()
    assert_inputs_exist(parser, args.image_paths)
    assert_outputs_exist(parser, args, args.output_path)

    # Check if the number of images matches the number of titles and colormaps
    if len(args.image_paths) != len(args.titles) or len(args.image_paths) != len(
        args.cmaps
    ):
        parser.error(
            "The number of images must match the number of titles and colormaps."
        )

    num_images = len(args.image_paths)
    _, axes = plt.subplots(num_images, 3, figsize=(15, 5 * num_images))

    if num_images == 1:
        axes = np.expand_dims(axes, axis=0)

    for i, image_path in enumerate(args.image_paths):
        image = nib.load(image_path).get_fdata()
        axial, coronal, sagittal = get_slices(image, tuple(args.coord))

        vmins = vmaxs = []
        for axis in [axial, coronal, sagittal]:
            values = np.percentile(axis[axis != 0], [20, 100])
            vmins.append(values[0])
            vmaxs.append(values[1])
        vmin = max(vmins)
        vmax = min(vmaxs)
        print(f"vmin: {vmin}, vmax: {vmax}")
        print(vmins, vmaxs)

        plot_slices(
            axial,
            coronal,
            sagittal,
            tuple(args.coord),
            f"{args.titles[i]}",
            axes,
            i,
            args.cmaps[i],
            vmin,
            vmax,
        )

    plt.tight_layout()
    plt.savefig(args.output_path)
    plt.close()
