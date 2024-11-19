import numpy as np
from scipy.ndimage import generate_binary_structure, binary_dilation


def create_sphere_mask(shape, center, radius=2):
    """Create a spherical mask centered at the given coordinates"""
    mask = np.zeros(shape, dtype=bool)

    # Ensure coordinates are within bounds
    x, y, z = [int(round(c)) for c in center]
    x = max(radius, min(x, shape[0] - radius - 1))
    y = max(radius, min(y, shape[1] - radius - 1))
    z = max(radius, min(z, shape[2] - radius - 1))

    mask[x, y, z] = True

    # Create spherical structure
    struct = generate_binary_structure(3, 1)
    # Dilate to create sphere
    for _ in range(radius):
        mask = binary_dilation(mask, structure=struct)

    return mask.astype(np.int16)
