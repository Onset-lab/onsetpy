#!/usr/bin/env python3

"""
Compute z-score matrices from base matrices using mean and std connectivity matrices.
"""

import argparse
import logging
import numpy as np
from typing import List

from onsetpy.io.matrix import save_matrix, load_matrix
from onsetpy.io.utils import (
    add_verbose_arg,
    add_overwrite_arg,
    assert_inputs_exist,
    assert_matrices_compatible,
    assert_outputs_exist,
)


def calculate_z_scores(
    mean_matrix: np.ndarray, std_matrix: np.ndarray, base_matrices: List[np.ndarray]
) -> List[np.ndarray]:
    """Compute z-score matrices for each base matrix.

    Args:
        mean_matrix (np.ndarray): Mean connectivity matrix.
        std_matrix (np.ndarray): Standard deviation connectivity matrix.
        base_matrices (List[np.ndarray]): List of base connectivity matrices.

    Returns:
        List[np.ndarray]: List of z-score matrices.
    """
    z_score_matrices = []
    for base_matrix in base_matrices:
        z_score_matrix = (base_matrix - mean_matrix) / std_matrix
        z_score_matrices.append(z_score_matrix)
    return z_score_matrices


def _build_arg_parser():
    """Build argparser.

    Returns:
        parser (ArgumentParser): Parser built.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--mean", required=True, help="Path to the mean connectivity matrix in .npy format"
    )
    parser.add_argument(
        "--std",
        required=True,
        help="Path to the standard deviation connectivity matrix in .npy format",
    )
    parser.add_argument(
        "base_matrices", nargs="+", help="Paths to the base connectivity matrices in .npy format"
    )
    parser.add_argument(
        "--out_prefix",
        default="z_score_matrix",
        help="Prefix for the output z-score matrices [%(default)s].",
    )

    add_verbose_arg(parser)
    add_overwrite_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()
    logging.getLogger().setLevel(logging.getLevelName(args.verbose))

    assert_inputs_exist(parser, [args.mean, args.std] + args.base_matrices)

    mean_matrix = load_matrix(args.mean)
    std_matrix = load_matrix(args.std)
    base_matrices = load_matrix(args.base_matrices)

    assert_matrices_compatible(parser, [mean_matrix, std_matrix] + base_matrices)

    z_score_matrices = calculate_z_scores(mean_matrix, std_matrix, base_matrices)

    output_files = [f"{args.out_prefix}_{i+1}.npy" for i in range(len(z_score_matrices))]
    assert_outputs_exist(parser, args, output_files)

    for i, z_score_matrix in enumerate(z_score_matrices):
        save_matrix(z_score_matrix, output_files[i])

    logging.info(f"Number of base matrices processed: {len(base_matrices)}")
    logging.info(f"Shape of z-score matrices: {z_score_matrices[0].shape}")
    logging.info(f"Results saved with prefix: {args.out_prefix}")


if __name__ == "__main__":
    main()
