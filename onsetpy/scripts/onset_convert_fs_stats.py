#!/usr/bin/env python3

"""
Convert Freesurfer cortical thickness statistics to CSV format.
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
        "lh_fs_stats",
        help="Path to the left hemisphere Freesurfer cortical thickness statistics files",
    )
    parser.add_argument(
        "rh_fs_stats",
        help="Path to the right hemisphere Freesurfer cortical thickness statistics files",
    )
    parser.add_argument(
        "aseg_fs_stats",
        help="Path to the Freesurfer aseg statistics files",
    )
    parser.add_argument(
        "output_aparc", help="Path to the output aparc CSV file or JSON file"
    )
    parser.add_argument(
        "output_aseg", help="Path to the output aseg CSV file or JSON file"
    )

    parser.add_argument("--sid", help="Subject ID")

    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, [args.lh_fs_stats, args.rh_fs_stats])
    assert_outputs_exist(parser, args, [args.output_aparc, args.output_aseg])

    names = [
        "StructName",
        "NumVert",
        "SurfArea",
        "GrayVol",
        "ThickAvg",
        "ThickStd",
        "MeanCurv",
        "GausCurv",
        "FoldInd",
        "CurvInd",
    ]

    df_list = []
    for stat, side in zip([args.lh_fs_stats, args.rh_fs_stats], ["left", "right"]):
        curr_df = pd.read_csv(
            stat,
            sep="\s+",
            comment="#",
            header=None,
            names=names,
        )
        curr_df["side"] = side
        df_list.append(curr_df)

    df = pd.concat(df_list, ignore_index=True)

    df.rename(
        columns={"StructName": "roi", "GrayVol": "volume", "ThickAvg": "thickness"},
        inplace=True,
    )
    df["sid"] = args.sid
    df = df[["sid", "roi", "side", "volume", "thickness"]]

    if args.output_aparc.endswith(".csv"):
        df.to_csv(args.output_aparc, index=False)
    else:
        df.to_json(args.output_aparc, orient="records", index=False, indent=4)

    names = [
        "Index",
        "SegId",
        "NVoxels",
        "Volume_mm3",
        "StructName",
        "normMean",
        "normStdDev",
        "normMin",
        "normMax",
        "normRange",
    ]
    aseg_df = pd.read_csv(
        args.aseg_fs_stats,
        sep="\s+",
        comment="#",
        header=None,
        names=names,
    )
    aseg_df.rename(
        columns={"StructName": "roi", "Volume_mm3": "volume"},
        inplace=True,
    )
    aseg_df["sid"] = args.sid
    aseg_df = aseg_df[["sid", "roi", "volume"]]

    if args.output_aseg.endswith(".csv"):
        aseg_df.to_csv(args.output_aseg, index=False)
    else:
        aseg_df.to_json(args.output_aseg, orient="records", index=False, indent=4)


if __name__ == "__main__":
    main()
