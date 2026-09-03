#!/usr/bin/env python3

"""
Merge several per-subject cortical thickness stats CSVs (Freesurfer aparc
stats) into a single CSV, adding a 'sid' column to identify each subject.

Each input file must be named <sid>__<anything>.csv (e.g. patA__thickness_stats.csv),
the part before the first '__' being used as the subject ID.

The resulting CSV can be fed into onset_prepare_combat_thickness.py.
"""

import argparse
import glob
import os
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
        "thickness_stats",
        nargs="+",
        help="Path(s) to the per-subject thickness stats CSV files. Accepts "
        "multiple paths and/or glob patterns, e.g. "
        "'results/*/CORTICAL_THICKNESS_STATS/*__thickness_stats.csv'.",
    )
    parser.add_argument("output", help="Path to the merged output CSV file.")

    parser.add_argument(
        "--sid_separator",
        default="__",
        help="Separator used to extract the subject ID from each input "
        "filename (the part before the first occurrence). Default: %(default)s.",
    )

    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser


def _expand_paths(paths):
    """Expand any glob patterns among the given paths.

    Args:
        paths (List[str]): Paths and/or glob patterns.

    Returns:
        List[str]: Expanded, sorted, deduplicated list of existing file paths.
    """
    expanded = []
    for path in paths:
        if os.path.isfile(path):
            expanded.append(path)
        else:
            expanded.extend(glob.glob(path))
    return sorted(set(expanded))


def _sid_from_path(path, separator):
    """Extract the subject ID from a thickness stats filename.

    Args:
        path (str): Path to the thickness stats CSV.
        separator (str): Separator between the subject ID and the rest of the filename.

    Returns:
        str: Subject ID.
    """
    basename = os.path.splitext(os.path.basename(path))[0]
    return basename.split(separator)[0]


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    input_files = _expand_paths(args.thickness_stats)
    if not input_files:
        parser.error("No thickness stats file found for the given path(s)/pattern(s).")

    assert_inputs_exist(parser, input_files)
    assert_outputs_exist(parser, args, [args.output])

    sids = [_sid_from_path(path, args.sid_separator) for path in input_files]
    duplicated_sids = {sid for sid in sids if sids.count(sid) > 1}
    if duplicated_sids:
        parser.error(
            f"Multiple input files resolve to the same sid: {', '.join(sorted(duplicated_sids))}."
        )

    frames = []
    for path, sid in zip(input_files, sids):
        df = pd.read_csv(path)
        df.insert(0, "sid", sid)
        frames.append(df)

    merged_df = pd.concat(frames, ignore_index=True)
    merged_df.to_csv(args.output, index=False)

    print(f"Merged {len(frames)} subject(s) ({len(merged_df)} rows) into {args.output}")


if __name__ == "__main__":
    main()
