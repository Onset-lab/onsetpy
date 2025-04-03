#!/usr/bin/env python3

"""
This script generates a SurgeryFlow report in PDF format.

The script takes in 2 input files: a bundles screenshot and a file containing the missing bundles.
It then generates a SurgeryFlow report in PDF format, including patient information if provided.
"""

import argparse
from datetime import datetime

from onsetpy.io.utils import (
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    add_version_arg,
)
from onsetpy.reporting.report import SurgeryflowReport


def _build_arg_parser():
    """Build argparser.

    Returns:
        parser (ArgumentParser): Parser built.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_screenshot", help="Path to the .png image of the bundles screenshots."
    )
    parser.add_argument(
        "missing_bundles", help="Path to the .txt file containing the missing bundles."
    )
    parser.add_argument(
        "output_report", help="Path to the .pdf SurgeryFlow report file."
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

    assert_inputs_exist(parser, [args.input_screenshot, args.missing_bundles])
    assert_outputs_exist(parser, args, args.output_report)

    with open(args.missing_bundles, "r") as file:
        missing_bundles = file.readlines()
    missing_bundles = [bundle.strip() for bundle in missing_bundles]

    report = SurgeryflowReport(
        args.patient_name, args.patient_id, datetime.now().strftime("%d-%m-%Y")
    )
    import os

    report.render(missing_bundles, os.path.abspath(args.input_screenshot))
    report.to_pdf(args.output_report)
