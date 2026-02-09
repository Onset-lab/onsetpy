#!/usr/bin/env python3

"""
Get brain function by label ID in Yale atlas.
"""

import argparse
from datetime import datetime
import json
import os

import pandas as pd
import ast

from onsetpy.io.utils import (
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    add_version_arg,
)


def _build_arg_parser():
    """Build argparser.

    Returns:
        parser (ArgumentParser): Parser built.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("DB", help="Path to the DB in csv format.")

    parser.add_argument(
        "label_id", type=int, help="Label ID to retrieve brain function."
    )
    parser.add_argument(
        "function_type",
        choices=["effect_class", "effect_descriptor", "effect_details"],
        help="Type of function.",
    )

    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, [args.DB])

    with open(args.DB, "r") as file:
        df = pd.read_csv(file)

    def _parse_roi_mask(val):
        return val.split(",")

    # create a normalized list column, explode it to one row per roi id, keep all other columns
    df["weight"] = df["roi_mask"].apply(lambda x: 1 / len(x.split(",")))
    df["weighted_occurrence_clinical_effect"] = (
        df["occurrence_clinical_effect"] * df["weight"]
    )
    df["roi_list"] = df["roi_mask"].apply(_parse_roi_mask)
    df = df.explode("roi_list").dropna(subset=["roi_list"]).reset_index(drop=True)

    df["roi_list"] = df["roi_list"].apply(lambda x: int(x))

    df = df.rename(columns={"roi_list": "roi_id"})
    df = df.loc[df["roi_id"] == args.label_id]

    # aggregate totals by effect_class (handle both possible column names for stimulations)
    nb_col = "nb_stimulations" if "nb_stimulations" in df.columns else "nb_stimulation"
    agg = (
        df.groupby(args.function_type)
        .agg(
            total_occurrence_clinical_effect=("occurrence_clinical_effect", "sum"),
            total_weighted_occurrence_clinical_effect=(
                "weighted_occurrence_clinical_effect",
                "sum",
            ),
            total_nb_stimulations=(nb_col, "sum"),
        )
        .reset_index()
        # Pour chaque fonction pour un label X: sum(occurence_clinical_effect * (1/nb_regions)) / sum(nb_stimulations)
        .assign(
            total_positive_ratio=lambda x: x["total_occurrence_clinical_effect"]
            / x["total_nb_stimulations"]
        )
        # Pour chaque fonction pour un label X: sum(occurence_clinical_effect * (1/nb_regions)) / sum(nb_stimulations)
        .assign(
            weighted_positive_ratio=lambda x: x[
                "total_weighted_occurrence_clinical_effect"
            ]
            / x["total_nb_stimulations"]
        )
    )
    # Impression "propre" des fonctions les plus probables pour le label demandé
    if agg.empty:
        print(f"Aucune fonction trouvée pour le label {args.label_id}")
    else:
        top_n = 10
        sorted_agg = (
            agg.fillna(0)
            .sort_values(by="weighted_positive_ratio", ascending=False)
            .reset_index(drop=True)
        )
        n_show = min(len(sorted_agg), top_n)
        print(f"\nFonctions probables pour le label {args.label_id} (Top {n_show})")
        # Print a nicely formatted table similar to the requested output
        # Header
        print(
            f"{'N°':<4} {'Fonction Positive':<30} {'Pondéré (%)':>11} {'Brut (%)':>9} {'Nb stim':>8} {'Tot pond.':>10} {'Tot':>7}"
        )
        print("-" * 86)

        for i, row in sorted_agg.head(n_show).iterrows():
            effect = str(row.get(args.function_type, "<inconnu>"))
            weighted_ratio = float(row.get("weighted_positive_ratio", 0.0) or 0.0)
            ratio = float(row.get("total_positive_ratio", 0.0) or 0.0)
            nb = int(row.get("total_nb_stimulations", 0) or 0)
            tot_weighted = float(
                row.get("total_weighted_occurrence_clinical_effect", 0.0) or 0.0
            )
            tot = float(row.get("total_occurrence_clinical_effect", 0.0) or 0.0)

            # Effect name truncated to fit column width
            effect_display = (effect[:27] + "...") if len(effect) > 30 else effect

            print(
                f"{i+1:<4d} {effect_display:<30} "
                f"{weighted_ratio * 100:11.1f} {ratio * 100:9.1f} {nb:8d} "
                f"{tot_weighted:10.2f} {tot:7.2f}"
            )
        print("-" * 86)
