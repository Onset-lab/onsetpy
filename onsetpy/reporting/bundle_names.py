"""Mapping between white matter bundle abbreviations and their full names."""

import re

# Full names of the bundles, without hemisphere. The hemisphere is added
# automatically from the suffix of the abbreviation (e.g. AF_L, CST_R).
BUNDLE_FULL_NAMES = {
    # Association
    "AF": "Arcuate fasciculus",
    "AF_ant": "Arcuate fasciculus (anterior segment)",
    "AF_long": "Arcuate fasciculus (long segment)",
    "AF_post": "Arcuate fasciculus (posterior segment)",
    "CG": "Cingulum",
    "EMC": "Extreme capsule",
    "FAT": "Frontal aslant tract",
    "IFO": "Inferior fronto-occipital fasciculus",
    "IFOF": "Inferior fronto-occipital fasciculus",
    "ILF": "Inferior longitudinal fasciculus",
    "MdLF": "Middle longitudinal fasciculus",
    "MLF": "Middle longitudinal fasciculus",
    "SLF": "Superior longitudinal fasciculus",
    "SLF_I": "Superior longitudinal fasciculus I",
    "SLF_II": "Superior longitudinal fasciculus II",
    "SLF_III": "Superior longitudinal fasciculus III",
    "UF": "Uncinate fasciculus",
    "VOF": "Vertical occipital fasciculus",
    "PAT": "Parietal aslant tract",
    # Projection
    "AR": "Acoustic radiation",
    "ATR": "Anterior thalamic radiation",
    "CST": "Corticospinal tract",
    "FPT": "Fronto-pontine tract",
    "FX": "Fornix",
    "Fx": "Fornix",
    "ML": "Medial lemniscus",
    "OR": "Optic radiation",
    "OR_ML": "Optic radiation & Meyer's loop",
    "PYT": "Pyramidal tract",
    "OPT": "Optic radiation",
    "POPT": "Parieto-occipital pontine tract",
    "PPT": "Parieto-pontine tract",
    "STR": "Superior thalamic radiation",
    "OT": "Optic tract",
    # Commissural
    "AC": "Anterior commissure",
    "PC": "Posterior commissure",
    "CC": "Corpus callosum",
    "CC_1": "Corpus callosum - Rostrum",
    "CC_2": "Corpus callosum - Genu",
    "CC_3": "Corpus callosum - Rostral body (premotor)",
    "CC_4": "Corpus callosum - Anterior midbody (primary motor)",
    "CC_5": "Corpus callosum - Posterior midbody (primary somatosensory)",
    "CC_6": "Corpus callosum - Isthmus",
    "CC_7": "Corpus callosum - Splenium",
    "CCMid": "Corpus callosum - Midbody",
    "CC_Fr_1": "Corpus callosum - Frontal 1",
    "CC_Fr_2": "Corpus callosum - Frontal 2",
    "CC_Oc": "Corpus callosum - Occipital",
    "CC_Pa": "Corpus callosum - Parietal",
    "CC_Pr_Po": "Corpus callosum - Precentral/Postcentral",
    "CC_Te": "Corpus callosum - Temporal",
    # Cerebellar
    "ICP": "Inferior cerebellar peduncle",
    "MCP": "Middle cerebellar peduncle",
    "SCP": "Superior cerebellar peduncle",
    "CTT": "Cortico-thalamic tract",
    "V": "Vermis",
    # Striatal / thalamic sub-projections (TractSeg)
    "ST_FO": "Striato-fronto-orbital",
    "ST_OCC": "Striato-occipital",
    "ST_PAR": "Striato-parietal",
    "ST_POSTC": "Striato-postcentral",
    "ST_PREC": "Striato-precentral",
    "ST_PREF": "Striato-prefrontal",
    "ST_PREM": "Striato-premotor",
    "T_OCC": "Thalamo-occipital",
    "T_PAR": "Thalamo-parietal",
    "T_POSTC": "Thalamo-postcentral",
    "T_PREC": "Thalamo-precentral",
    "T_PREF": "Thalamo-prefrontal",
    "T_PREM": "Thalamo-premotor",
}

HEMISPHERE_SUFFIXES = {
    "L": "left",
    "R": "right",
    "LEFT": "left",
    "RIGHT": "right",
    "LH": "left",
    "RH": "right",
}


def _split_hemisphere(abbreviation):
    """Split an abbreviation into its base and hemisphere.

    Returns:
        tuple: (base, "left" | "right" | None)
    """
    match = re.match(r"^(.+?)[_\-\.](L|R|left|right|lh|rh)$", abbreviation, re.I)
    if match:
        return match.group(1), HEMISPHERE_SUFFIXES[match.group(2).upper()]
    return abbreviation, None


def get_bundle_full_name(abbreviation, custom_names=None):
    """Get the full name of a bundle from its abbreviation.

    The lookup is done first on the full abbreviation, then on the abbreviation
    without its hemisphere suffix (the hemisphere is then appended).

    Args:
        abbreviation (str): Bundle abbreviation (e.g. "AF_L").
        custom_names (dict, optional): Custom mapping that takes precedence over
            the built-in mapping.

    Returns:
        str or None: The full name, or None if the abbreviation is unknown.
    """
    mappings = [custom_names or {}, BUNDLE_FULL_NAMES]

    for mapping in mappings:
        if abbreviation in mapping:
            return mapping[abbreviation]

    base, hemisphere = _split_hemisphere(abbreviation)
    if hemisphere is None:
        return None
    for mapping in mappings:
        if base in mapping:
            return f"{mapping[base]} ({hemisphere})"
    return None
