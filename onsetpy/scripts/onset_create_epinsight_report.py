#!/usr/bin/env python3

"""
This script generates a SurgeryFlow report in PDF format.

The script takes in 2 input files: a bundles screenshot and a file containing the missing bundles.
It then generates a SurgeryFlow report in PDF format, including patient information if provided.
"""

import argparse
from datetime import datetime
import json
import os

from onsetpy.io.utils import (
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    add_version_arg,
)
from onsetpy.reporting.report import EpinsightReport


def _build_arg_parser():
    """Build argparser.

    Returns:
        parser (ArgumentParser): Parser built.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "output_report", help="Path to the .pdf SurgeryFlow report file."
    )

    parser.add_argument(
        "--asymmetry_figure", help="Path to the .png image of the asymmetry figure."
    )
    parser.add_argument(
        "--asymmetry_index",
        help="Path to the .json file containing the asymmetry indexes.",
    )
    parser.add_argument(
        "--map18_figures",
        nargs="+",
        help="Path to the .png files containing the map18 figures.",
    )
    parser.add_argument(
        "--brain_screenshot",
        help="Path to the .png image of the brain screenshot.",
    )

    parser.add_argument(
        "--patient_name",
        help="Patient name. Write the name between quotes.",
        default="Not available",
    )
    parser.add_argument("--patient_id", help="Patient ID.", default="Not available")

    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, [args.asymmetry_figure, args.asymmetry_index])
    assert_outputs_exist(parser, args, args.output_report)

    with open(args.asymmetry_index, "r") as file:
        asymmetry_index = json.load(file)

    report = EpinsightReport(
        args.patient_name, args.patient_id, datetime.now().strftime("%d-%m-%Y")
    )

    report.render(
        asymmetry_index,
        os.path.abspath(args.asymmetry_figure),
        [os.path.abspath(figure) for figure in (args.map18_figures or [])],
        os.path.abspath(args.brain_screenshot),
    )
    report.to_pdf(args.output_report)
