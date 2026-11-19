#!/usr/bin/env python3

"""
Prepare a cortical thickness stats CSV (Freesurfer aparc stats, mean value per
label, multiple subjects identified by a 'sid' column) as a long-format input
CSV for clinical-ComBAT harmonization
(https://github.com/scil-vital/clinical-ComBAT).

Each subject's covariates (site, age, sex, handedness, disease) are looked up
in a separate covariates CSV, matched on subject ID.
"""

import argparse
import pandas as pd
from onsetpy.io.utils import (
    add_overwrite_arg,
    add_version_arg,
    assert_inputs_exist,
    assert_outputs_exist,
)

COMBAT_COVARIATE_COLUMNS = ["sid", "site", "age", "sex", "handedness", "disease"]
COMBAT_OUTPUT_COLUMNS = [
    "sid",
    "site",
    "bundle",
    "metric",
    "mean",
    "age",
    "sex",
    "handedness",
    "disease",
]


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
        help="Path to the cortical thickness stats CSV, with one row per "
        "subject per label (columns: sid, Label, Mean, Sigma, ...).",
    )
    parser.add_argument(
        "covariates",
        help="Path to the covariates CSV, with one row per subject and "
        f"columns: <id_column>, {', '.join(COMBAT_COVARIATE_COLUMNS)}.",
    )
    parser.add_argument("output", help="Path to the output CSV file.")

    parser.add_argument(
        "--sid_column",
        default="sid",
        help="Column in the thickness stats CSV identifying the subject. Default: %(default)s.",
    )
    parser.add_argument(
        "--id_column",
        default="patient_id",
        help="Column in the covariates CSV used to match --sid_column. Default: %(default)s.",
    )
    parser.add_argument(
        "--metric",
        default="thickness",
        help="Value written in the 'metric' column of the output CSV. Default: %(default)s.",
    )

    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, [args.thickness_stats, args.covariates])
    assert_outputs_exist(parser, args, [args.output])

    stats_df = pd.read_csv(args.thickness_stats)
    missing_stats_columns = [
        col
        for col in [args.sid_column, "Label", "Mean"]
        if col not in stats_df.columns
    ]
    if missing_stats_columns:
        parser.error(
            f"Thickness stats CSV is missing column(s): {', '.join(missing_stats_columns)}."
        )

    covariates_df = pd.read_csv(args.covariates)
    print(covariates_df.columns)
    missing_columns = [
        col
        for col in COMBAT_COVARIATE_COLUMNS
        if col not in covariates_df.columns
    ]
    if missing_columns:
        parser.error(
            f"Covariates CSV is missing column(s): {', '.join(missing_columns)}."
        )
    if covariates_df["sid"].duplicated().any():
        duplicated_ids = covariates_df[
            covariates_df["sid"].duplicated()
        ]["sid"].unique()
        parser.error(
            f"Covariates CSV has duplicate {', '.join(map(str, duplicated_ids))}."
        )

    merged_df = stats_df.merge(
        covariates_df,
        left_on=args.sid_column,
        right_on="sid",
        how="left",
    )

    unmatched_mask = merged_df[COMBAT_COVARIATE_COLUMNS].isna().any(axis=1)
    if unmatched_mask.any():
        unmatched_sids = merged_df.loc[unmatched_mask, args.sid_column].unique()
        print(
            f"WARNING: {len(unmatched_sids)} subject(s) not found in {args.covariates}, "
            f"skipped: {', '.join(map(str, unmatched_sids))}"
        )
        merged_df = merged_df[~unmatched_mask]

    if merged_df.empty:
        parser.error("No subject had matching covariates; nothing to write.")

    output_df = pd.DataFrame(
        {
            "sid": merged_df[args.sid_column],
            "site": merged_df["site"],
            "bundle": merged_df["Label"].astype(str),
            "metric": args.metric,
            "mean": merged_df["Mean"],
            "age": merged_df["age"].astype(int),
            "sex": merged_df["sex"].astype(int),
            "handedness": merged_df["handedness"].astype(int),
            "disease": merged_df["disease"],
        }
    )
    output_df.to_csv(args.output, index=False)

    n_subjects = output_df["sid"].nunique()
    print(f"Wrote {n_subjects} subject(s) ({len(output_df)} rows) to {args.output}")


if __name__ == "__main__":
    main()
