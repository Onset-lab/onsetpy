"""
Statistical operations for connectivity matrices.
"""

import numpy as np
from typing import List


def calculate_z_scores(
    mean_matrix: np.ndarray, std_matrix: np.ndarray, base_matrices: List[np.ndarray]
) -> List[np.ndarray]:
    """Compute z-score matrices for each base matrix.

    For each base matrix, calculates (base - mean) / std to get z-scores.

    Args:
        mean_matrix (np.ndarray): Mean connectivity matrix.
        std_matrix (np.ndarray): Standard deviation connectivity matrix.
        base_matrices (List[np.ndarray]): List of base connectivity matrices.

    Returns:
        List[np.ndarray]: List of z-score matrices corresponding to each input base matrix.

    Raises:
        ValueError: If matrices have incompatible shapes or if std contains zeros.
    """
    if not all(isinstance(m, np.ndarray) for m in [mean_matrix, std_matrix] + base_matrices):
        raise TypeError("All inputs must be numpy arrays")
    
    if not all(m.shape == mean_matrix.shape for m in [std_matrix] + base_matrices):
        raise ValueError("All matrices must have the same shape")
        
    if np.any(std_matrix == 0):
        raise ValueError("Standard deviation matrix contains zeros")

    z_score_matrices = []
    for base_matrix in base_matrices:
        z_score_matrix = (base_matrix - mean_matrix) / std_matrix
        z_score_matrices.append(z_score_matrix)
    return z_score_matrices
