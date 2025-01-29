#!/usr/bin/env python3

"""
Convert JSON file to multiple NPY files.
"""

import argparse
import json
import logging
import numpy as np
import os
from onsetpy.io.utils import (
    add_verbose_arg,
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    add_version_arg,
)


def json_to_npy(json_file: str, output_dir: str):
    """Convert JSON file to multiple NPY files.

    Args:
        json_file (str): Path to the JSON file.
        output_dir (str): Directory to save the NPY files.
    """
    # Load JSON data
    with open(json_file, "r") as f:
        data = json.load(f)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Save each key's data to a separate NPY file
    for key, value in data.items():
        npy_file = os.path.join(output_dir, f"{key}.npy")
        np.save(npy_file, np.array(value))
        logging.info(f"Saved {key} to {npy_file}")


def _build_arg_parser():
    """Build argparser.

    Returns:
        parser (ArgumentParser): Parser built.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("json_file", help="Path to the JSON file")
    parser.add_argument("output_dir", help="Directory to save the NPY files")

    add_verbose_arg(parser)
    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()
    logging.getLogger().setLevel(logging.getLevelName(args.verbose))

    assert_inputs_exist(parser, args.json_file)
    assert_outputs_exist(parser, args, [args.output_dir])

    json_to_npy(args.json_file, args.output_dir)


if __name__ == "__main__":
    main()
