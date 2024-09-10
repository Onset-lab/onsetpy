import numpy as np
from typing import Union, List


def load_matrix(
    input_names: Union[str, List[str]]
) -> Union[np.ndarray, List[np.ndarray]]:
    """Load one or multiple connectivity matrices.

    Args:
        input_names (Union[str, List[str]]): Connectivity filenames.

    Returns:
        Union[np.ndarray, List[np.ndarray]]: Connectivity matrices.
    """
    if isinstance(input_names, str):
        return np.load(input_names)
    else:
        return [np.load(file) for file in input_names]


def save_matrix(matrix: np.ndarray, output_name: str) -> None:
    """Save connectivity matrix

    Args:
        matrix (np.ndarray): Connectivity matrix
        output_name (str): Output filename
    """
    np.save(output_name, matrix)
