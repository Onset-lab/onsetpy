#!/usr/bin/env python3

"""
This script generates a SurgeryFlow report in PDF format.

The report contains:
    - Page 1: patient information, a global screenshot of the patient's brain
      (all bundles) and a summary table of the bundle volumes.
    - Following pages: each bundle listed in the functions JSON, two bundles per
      page, with its screenshot, its functions and its volume compared to the
      normative volume.

A warning is displayed for a bundle when its volume is lower than
--volume_threshold (default: 20%) of the normative volume, or when the bundle
could not be reconstructed (absent from the patient volumes JSON or volume = 0).

Expected JSON formats:
    bundle_functions: {"AF_L": ["Language", "Repetition"], "CST_R": "Motor", ...}
                      (maximum 3 functions per bundle, extra ones are ignored)
                      (a value can also be {"name": "...", "functions": [...]})
    patient_volumes / normal_volumes:
                      {"AF_L": 12345.6, ...}
                      or {"AF_L": {"volume": 12345.6}, ...}
                      or {"AF_L": {"mean": 12345.6, "std": 789.0}, ...}

    bundle_names (optional, --bundle_names):
                      {"AF": "Arcuate fasciculus", "CST_L": "Left corticospinal tract", ...}

The full name of each bundle is resolved in this order:
    1. "name" key of the bundle in the functions JSON,
    2. --bundle_names JSON (exact abbreviation, then without the _L/_R suffix),
    3. built-in mapping (onsetpy/reporting/bundle_names.py),
    4. the abbreviation itself.
When the lookup is done without the hemisphere suffix, " (left)" or " (right)"
is appended to the full name.

In the PDF, each bundle name of the summary table (page 2) is a link to the
page of that bundle.

Individual bundle screenshots are searched in --bundle_screenshots_dir using
--screenshot_pattern (default: "{bundle}.png").
"""

import argparse
from datetime import datetime
import json
import logging
import os
import re

from onsetpy.io.utils import (
    add_overwrite_arg,
    assert_inputs_exist,
    assert_outputs_exist,
    add_version_arg,
)
from onsetpy.reporting.bundle_names import get_bundle_full_name
from onsetpy.reporting.report import SurgeryflowReport


VOLUME_KEYS = ("volume", "mean", "volume_mean", "avg", "average")
MAX_FUNCTIONS = 3


def _build_arg_parser():
    """Build argparser.

    Returns:
        parser (ArgumentParser): Parser built.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_screenshot",
        help="Path to the .png global screenshot of the patient's brain (all bundles).",
    )
    parser.add_argument(
        "bundle_functions",
        help="Path to the .json file containing the functions of each bundle to display.",
    )
    parser.add_argument(
        "patient_volumes",
        help="Path to the .json file containing the patient's bundle volumes.",
    )
    parser.add_argument(
        "normal_volumes",
        help="Path to the .json file containing the normative bundle volumes.",
    )
    parser.add_argument(
        "output_report", help="Path to the .pdf SurgeryFlow report file."
    )

    parser.add_argument(
        "--bundle_screenshots_dir",
        help="Directory containing one screenshot per bundle.",
    )
    parser.add_argument(
        "--screenshot_pattern",
        default="{bundle}.png",
        help="Filename pattern of the bundle screenshots in --bundle_screenshots_dir. "
        "[%(default)s]",
    )
    parser.add_argument(
        "--bundle_names",
        help="Path to a .json file mapping bundle abbreviations to full names. "
        "Takes precedence over the built-in mapping.",
    )
    parser.add_argument(
        "--volume_threshold",
        type=float,
        default=0.2,
        help="A warning is displayed when patient volume < threshold * normal volume. "
        "[%(default)s]",
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


def _load_json(path):
    with open(path, "r") as file:
        return json.load(file)


def _extract_volume(value):
    """Extract a volume from a JSON value (number, list or dict).

    Returns:
        float or None: The volume, or None if it could not be found.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, list):
        return _extract_volume(value[0]) if value else None
    if isinstance(value, dict):
        for key in VOLUME_KEYS:
            if key in value:
                return _extract_volume(value[key])
    return None


def _extract_functions(value):
    """Extract a display name and a list of functions from a JSON value.

    Returns:
        tuple: (display_name or None, list of str)
    """
    if isinstance(value, dict):
        name = value.get("name") or value.get("full_name")
        return name, _extract_functions(value.get("functions", []))[1]
    if isinstance(value, str):
        return None, [value]
    if isinstance(value, list):
        return None, [str(function) for function in value]
    return None, []


def build_bundles_info(
    bundle_functions,
    patient_volumes,
    normal_volumes,
    volume_threshold,
    screenshots_dir=None,
    screenshot_pattern="{bundle}.png",
    bundle_names=None,
):
    """Build the list of bundles to display in the report.

    Returns:
        list of dict: One dict per bundle, in the order of the functions JSON.
    """
    bundles = []
    for bundle, value in bundle_functions.items():
        display_name, functions = _extract_functions(value)
        display_name = display_name or get_bundle_full_name(bundle, bundle_names)
        if len(functions) > MAX_FUNCTIONS:
            logging.warning(
                f"Bundle {bundle} has {len(functions)} functions, only the first "
                f"{MAX_FUNCTIONS} are displayed."
            )
            functions = functions[:MAX_FUNCTIONS]
        patient_volume = _extract_volume(patient_volumes.get(bundle))
        normal_volume = _extract_volume(normal_volumes.get(bundle))

        reconstructed = patient_volume is not None and patient_volume > 0
        ratio = None
        if reconstructed and normal_volume:
            ratio = patient_volume / normal_volume

        if not reconstructed:
            status = "missing"
            warning = "Bundle could not be reconstructed."
        elif ratio is not None and ratio < volume_threshold:
            status = "low"
            warning = (
                f"Bundle volume is {ratio:.0%} of the normative volume "
                f"(below the {volume_threshold:.0%} threshold)."
            )
        else:
            status = "ok"
            warning = None

        if normal_volume is None:
            logging.warning(f"No normative volume found for bundle {bundle}.")

        screenshot = None
        if screenshots_dir:
            path = os.path.join(
                screenshots_dir, screenshot_pattern.format(bundle=bundle)
            )
            if os.path.isfile(path):
                screenshot = os.path.abspath(path)
            elif reconstructed:
                logging.warning(f"Screenshot not found for bundle {bundle}: {path}")

        bundles.append(
            {
                "name": bundle,
                "display_name": display_name or bundle,
                "anchor": "bundle-" + re.sub(r"[^A-Za-z0-9_-]", "-", bundle),
                "functions": functions,
                "patient_volume": patient_volume,
                "normal_volume": normal_volume,
                "ratio": ratio,
                "reconstructed": reconstructed,
                "status": status,
                "warning": warning,
                "screenshot": screenshot,
            }
        )
    return bundles


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(
        parser,
        [
            args.input_screenshot,
            args.bundle_functions,
            args.patient_volumes,
            args.normal_volumes,
        ],
        optional=args.bundle_names,
    )
    assert_outputs_exist(parser, args, args.output_report)

    if args.bundle_screenshots_dir and not os.path.isdir(args.bundle_screenshots_dir):
        parser.error(f"{args.bundle_screenshots_dir} is not a directory.")
    if not 0 < args.volume_threshold <= 1:
        parser.error("--volume_threshold must be in ]0, 1].")

    bundles = build_bundles_info(
        _load_json(args.bundle_functions),
        _load_json(args.patient_volumes),
        _load_json(args.normal_volumes),
        args.volume_threshold,
        args.bundle_screenshots_dir,
        args.screenshot_pattern,
        _load_json(args.bundle_names) if args.bundle_names else None,
    )

    report = SurgeryflowReport(
        args.patient_name, args.patient_id, datetime.now().strftime("%d-%m-%Y")
    )
    report.render(
        bundles, os.path.abspath(args.input_screenshot), args.volume_threshold
    )
    report.to_pdf(args.output_report)


if __name__ == "__main__":
    main()
