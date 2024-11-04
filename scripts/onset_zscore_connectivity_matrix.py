#!/usr/bin/env python3

"""
Compute z-score matrix from a base matrix using mean and std connectivity matrices.
"""

import argparse
import logging
import numpy as np
from onsetpy.io.matrix import save_matrix, load_matrix
from onsetpy.io.utils import (
    add_verbose_arg,
    add_overwrite_arg,
    assert_inputs_exist,
    assert_matrices_compatible,
    assert_outputs_exist,
)
from onsetpy.io.stats import calculate_z_scores  # Updated import path


def _build_arg_parser():
    """Build argparser.

    Returns:
        parser (ArgumentParser): Parser built.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "mean", help="Path to the mean connectivity matrix in .npy format"
    )
    parser.add_argument(
        "std", help="Path to the standard deviation connectivity matrix in .npy format"
    )
    parser.add_argument(
        "base_matrix", help="Path to the base connectivity matrix in .npy format"
    )
    parser.add_argument(
        "out", help="Output path for the z-score matrix in .npy format"
    )

    add_verbose_arg(parser)
    add_overwrite_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()
    logging.getLogger().setLevel(logging.getLevelName(args.verbose))

    assert_inputs_exist(parser, [args.mean, args.std, args.base_matrix])

    mean_matrix, std_matrix = load_matrix([args.mean, args.std])
    base_matrix = load_matrix(args.base_matrix)

    assert_matrices_compatible(parser, [mean_matrix, std_matrix, base_matrix])

    z_score_matrices = calculate_z_scores(mean_matrix, std_matrix, [base_matrix])
    z_score_matrix = z_score_matrices[0]  # We only have one matrix

    assert_outputs_exist(parser, args, [args.out])
    save_matrix(z_score_matrix, args.out)

    logging.info(f"Shape of z-score matrix: {z_score_matrix.shape}")
    logging.info(f"Results saved as: {args.out}")


if __name__ == "__main__":
    main()
