#!/usr/bin/env python3

"""
Flip the matrix to invert the left and right hemispheres.
The goal is to compare the left and right hemispheres.

WARNING: This script only works for the Brainnetome atlas and the matrix must be symmetric.
"""

import argparse
import numpy as np

from onsetpy.io.matrix import save_matrix, load_matrix
from onsetpy.io.utils import (
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
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
        "input", help="Path to the Brainnetome connectivity matrix in .npy format"
    )
    parser.add_argument(
        "output",
        help="Path to the output flipped Brainnetome connectivity matrix.",
    )

    add_overwrite_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, args.input)
    assert_outputs_exist(parser, args, args.output)

    i_matrix = load_matrix(args.input)
    f_matrix = np.flip(i_matrix, axis=1)

    save_matrix(f_matrix, args.output)


if __name__ == "__main__":
    main()
