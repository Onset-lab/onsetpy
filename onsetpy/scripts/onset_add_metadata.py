#!/usr/bin/env python3

"""
Add metadata to CSV file based on a SID.

The sex is converted to a binary (1 for male and 2 for female).
"""

import argparse
import pandas as pd
from onsetpy.io.utils import (
    add_overwrite_arg,
    add_version_arg,
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
        "input",
        help="Path to the input CSV or JSON file",
    )
    parser.add_argument(
        "metadata_csv",
        help="Path to the metadata CSV file",
    )
    parser.add_argument("output", help="Path to the output CSV file")

    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, [args.input, args.metadata_csv])
    assert_outputs_exist(parser, args, [args.output])

    if not args.output.lower().endswith(".csv"):
        parser.error("Output file must be a CSV file.")

    df_meta = pd.read_csv(args.metadata_csv)

    if args.input.lower().endswith(".csv"):
        df = pd.read_csv(args.input)
    else:
        df = pd.read_json(args.input)
    df["sid"] = df["sid"].str.replace("sub-", "")

    df = pd.merge(df, df_meta[["sid", "age", "sex"]], on="sid", how="outer")
    # df = df.dropna()

    df = df[
        [
            "sid",
            "age",
            "sex",
            "roi",
            "side",
            "volume",
            "thickness",
        ]
    ]
    df["sex"] = df["sex"].replace("FEMALE", "2")
    df["sex"] = df["sex"].str.replace("MALE", "1")
    df["sex"] = df["sex"].astype(int)
    df.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
