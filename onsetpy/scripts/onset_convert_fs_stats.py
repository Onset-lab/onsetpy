#!/usr/bin/env python3

"""
Convert Freesurfer cortical thickness statistics to CSV format.
"""

import argparse
import pandas as pd
from onsetpy.io.utils import (
    add_verbose_arg,
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
        "fs_stats",
        nargs="+",
        help="Path to the Freesurfer cortical thickness statistics files",
    )
    parser.add_argument("output", help="Path to the output CSV file or JSON file")

    parser.add_argument("--sid", help="Subject ID")

    add_verbose_arg(parser)
    add_overwrite_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, args.fs_stats)
    assert_outputs_exist(parser, args, [args.output])

    if not args.output.lower().endswith(".csv") and not args.output.lower().endswith(
        ".json"
    ):
        parser.error("Output file must be a CSV or JSON file")

    names = [
        "Index",
        "SegId",
        "NVoxels",
        "Volume_mm3",
        "StructName",
        "Mean",
        "StdDev",
        "Min",
        "Max",
        "Range",
    ]

    df_list = []
    for i in args.fs_stats:
        curr_df = pd.read_csv(
            i,
            sep="\s+",
            comment="#",
            header=None,
            names=names,
        )
        df_list.append(curr_df)

    df = pd.concat(df_list, ignore_index=True)
    df = (
        df.loc[df.groupby("SegId")["Mean"].idxmax()]
        .query("SegId != 0")
        .sort_values(by="SegId")
    )
    df.rename(columns={"SegId": "roi", "Mean": "mean"}, inplace=True)
    df["sid"] = args.sid
    df = df[["sid", "roi", "mean"]]

    if args.output.endswith(".csv"):
        df.to_csv(args.output, index=False)
    else:
        df.to_json(args.output, orient="records", index=False, indent=4)


if __name__ == "__main__":
    main()
