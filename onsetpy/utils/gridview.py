from typing import Union
import re


def parse_gridview_file(txt_path: str) -> Union[dict, list, list]:
    """
    Parses a gridview file to extract electrode information, image cube size, and resolution.
    Args:
        txt_path (str): The path to the gridview text file.
    Returns:
        tuple: A tuple containing:
            - electrodes (dict): A dictionary where keys are group names and values are lists of
              dictionaries
              with electrode information (name, coordinates, annotation).
            - shape (list): A list of integers representing the image cube size.
            - voxel_size (list): A list of floats representing the image cube resolution.
    """

    with open(txt_path, "r") as f:
        lines = f.readlines()

    electrodes = {}
    current_group = None
    shape = None
    voxel_size = None

    for line in lines:
        line = line.strip()
        if line.startswith("Image cube size"):
            shape = [int(x) for x in line.split(":")[1].strip().split("\t")]
        elif line.startswith("Image cube resolution"):
            voxel_size = [float(x) for x in line.split(":")[1].strip().split("\t")]
        elif line.startswith("Group:"):
            current_group = line.split(":")[1].strip()
            electrodes[current_group] = []
        elif current_group and re.match(r"^[A-Z]+[0-9]+:", line):
            parts = line.split(":")[1].strip().split("\t")
            if len(parts) >= 3:
                coords = [int(x) for x in parts[:3]]
                name = line.split(":")[0].strip()
                annotation = parts[3] if len(parts) > 3 else ""
                electrodes[current_group].append(
                    {"name": name, "coordinates": coords, "annotation": annotation}
                )

    return electrodes, shape, voxel_size


def transform_gridview_coordinates(
    coords: list[int],
    scaling_factors: list[float],
    vox_factors: list[float],
    ref_dims: list[int],
) -> list[int]:
    """
    Transforms a set of coordinates by applying scaling factors, voxel factors,
    and flipping the X and Y axes based on reference dimensions.
    Args:
        coords (list[int]): The original coordinates as a list of integers [x, y, z].
        scaling_factors (list[float]): The scaling factors to apply to each coordinate [sx, sy, sz].
        vox_factors (list[float]): The voxel factors to add to each coordinate after
        scaling [vx, vy, vz].
        ref_dims (list[int]): The reference dimensions used to flip the X and
        Y axes [ref_x, ref_y, ref_z].
    Returns:
        list[int]: The transformed coordinates as a list of integers [new_x, new_y, new_z].
    """
    # First apply scaling
    scaled_coords = [
        int(round((c * s) + v)) for c, s, v in zip(coords, scaling_factors, vox_factors)
    ]

    # Then flip X and Y axes
    transformed_coords = [
        ref_dims[0] - scaled_coords[0],  # Flip X
        ref_dims[1] - scaled_coords[1],  # Flip Y
        scaled_coords[2],  # Z stays the same
    ]

    return transformed_coords
