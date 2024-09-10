#!/usr/bin/env python3

"""
Calculate mean and std connectivity matrices from multiple connectivity matrices.
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


def calculate_stats(matrices: List[np.ndarray]) -> List[np.ndarray, np.ndarray]:
    """Compute mean and std connectivity matrices.

    Args:
        matrices (List[np.ndarray]): Connectivity matrices.

    Returns:
        List[np.ndarray, np.ndarray]: Mean and std connectivity matrices.
    """
    mean_matrix = np.mean(matrices, axis=0)
    std_matrix = np.std(matrices, axis=0, ddof=1)
    return mean_matrix, std_matrix


def _build_arg_parser():
    """Build argparser.

    Returns:
        parser (ArgumentParser): Parser built.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input", nargs="+", help="Path to the connectivity matrices in .npy format"
    )
    parser.add_argument(
        "--out_mean",
        default="mean_matrix.npy",
        help="Path to the output mean connectivity matrix [%(default)s].",
    )
    parser.add_argument(
        "--out_std",
        default="std_matrix.npy",
        help="Path to the output std connectivity matrix [%(default)s].",
    )

    add_verbose_arg(parser)
    add_overwrite_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()
    logging.getLogger().setLevel(logging.getLevelName(args.verbose))

    assert_inputs_exist(parser, args.input)
    assert_outputs_exist(parser, args, [args.out_mean, args.out_std])

    control_matrices = load_matrix(args.input)
    assert_matrices_compatible(parser, control_matrices)

    mean_matrix, std_matrix = calculate_stats(control_matrices)
    save_matrix(mean_matrix, args.out_mean)
    save_matrix(std_matrix, args.out_std)

    logging.info(
        f"Numberssssssssssssssss of connectivity matrices processed: {len(control_matrices)}"
    )
    logging.info(f"Shape of mean and std matrices: {mean_matrix.shape}")
    logging.info(f"Results saved in: {args.out_mean} and {args.out_std}")


if __name__ == "__main__":
    main()
