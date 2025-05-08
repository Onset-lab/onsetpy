#!/usr/bin/env python3

"""
Compare a patient to our database of cortical measures.
"""

import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from onsetpy.io.utils import (
    add_overwrite_arg,
    add_version_arg,
    assert_inputs_exist,
    assert_outputs_exist,
)


def _build_arg_parser():
    """Build argparser."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("aparc_csv", help="Path to the patient aparc CSV file")
    parser.add_argument("aseg_csv", help="Path to the patient aseg CSV file")
    parser.add_argument(
        "output", help="Path to the output CSV or JSON file with asymmetry index"
    )
    parser.add_argument("output_png", help="Path to the output PNG file")
    parser.add_argument(
        "--asymmetry_threshold", type=float, help="Asymmetry threshold", default=10
    )
    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser


def calculate_asymmetry_index(data, roi_column, value_column, side_column, z_threshold):
    """Calculate asymmetry index for given data."""
    roi_columns = data[roi_column].unique()
    asymmetry_index = {}

    for roi in roi_columns:
        left_value = data.loc[
            (data[roi_column] == roi) & (data[side_column] == "left"), value_column
        ].iloc[0]
        right_value = data.loc[
            (data[roi_column] == roi) & (data[side_column] == "right"), value_column
        ].iloc[0]
        asymmetry_index[roi] = (right_value - left_value) / left_value * 100

    df = pd.DataFrame([asymmetry_index]).transpose()
    df.columns = ["asymmetry_index"]
    return df[df["asymmetry_index"].abs() >= z_threshold]


def calculate_aseg_asymmetry_index(data, z_threshold):
    """Calculate asymmetry index for aseg data."""
    rois = [
        roi.replace("Left-", "").replace("Right-", "")
        for roi in data["roi"].unique()
        if "Left" in roi or "Right" in roi
    ]
    rois = list(set(rois))
    asymmetry_index = {}

    for roi in rois:
        left_value = data.loc[data["roi"] == f"Left-{roi}", "volume"].iloc[0]
        right_value = data.loc[data["roi"] == f"Right-{roi}", "volume"].iloc[0]
        asymmetry_index[roi] = (right_value - left_value) / left_value * 100

    df = pd.DataFrame([asymmetry_index]).transpose()
    df.columns = ["asymmetry_index"]
    return df[df["asymmetry_index"].abs() >= z_threshold]


def plot_asymmetry_index(df_combined, aparc_list, roi_mapping, output_path):
    """Plot the asymmetry index."""
    plt.figure(figsize=(10, max(6, len(df_combined) * 0.3)))
    sns.set_style("whitegrid")

    colors = [
        "#FF6B6B" if idx in aparc_list else "#4ECDC4" for idx in df_combined.index
    ]
    df_combined.index = df_combined.index.map(lambda x: roi_mapping.get(x, x))
    ax = sns.barplot(
        data=df_combined,
        y=df_combined.index,
        hue=df_combined.index,
        x="asymmetry_index",
        palette=colors,
    )
    plt.title(
        "Relative Asymmetry Index by ROI\n(Comparison of Right vs Left Hemisphere)",
        pad=20,
        fontsize=14,
        fontweight="bold",
    )
    plt.xlabel("Relative Asymmetry Index (%)", fontsize=10)
    plt.ylabel("ROI", fontsize=10)

    legend_elements = [
        Patch(facecolor="#FF6B6B", label="Cortical (thickness)"),
        Patch(facecolor="#4ECDC4", label="Subcortical (volume)"),
    ]
    ax.legend(handles=legend_elements)

    sns.despine()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    assert_inputs_exist(parser, [args.aparc_csv, args.aseg_csv])
    assert_outputs_exist(parser, args, [args.output_png, args.output])

    if not args.output_png.lower().endswith(".png"):
        parser.error("Output file must be a PNG file.")

    if not args.output.lower().endswith(".csv") and not args.output.lower().endswith(
        ".json"
    ):
        parser.error("Output file must be a CSV or JSON file.")

    aparc = pd.read_csv(args.aparc_csv)
    aseg = pd.read_csv(args.aseg_csv)
    aseg = aseg[aseg["volume"] != 0]

    df_aparc = calculate_asymmetry_index(
        aparc,
        roi_column="roi",
        value_column="thickness",
        side_column="side",
        z_threshold=args.asymmetry_threshold,
    )
    df_aseg = calculate_aseg_asymmetry_index(aseg, z_threshold=args.asymmetry_threshold)

    df_combined = pd.concat([df_aparc, df_aseg]).sort_values(
        by="asymmetry_index", ascending=False
    )

    roi_mapping = {  # Dictionary mapping FreeSurfer ROIs to full anatomical names
        "Lateral-Ventricle": "Lateral ventricle",
        "Inf-Lat-Vent": "Temporal horn of the lateral ventricle",
        "Cerebellum-White-Matter": "White matter of left hemisphere of cerebellum",
        "Cerebellum-Cortex": "Cerebellar cortex",
        "Thalamus": "Thalamus",
        "Caudate": "Caudate nucleus",
        "Putamen": "Putamen",
        "Pallidum": "Globus pallidus",
        "3rd-Ventricle": "Third ventricle",
        "4th-Ventricle": "Fourth ventricle",
        "Brain-Stem": "Brainstem",
        "Hippocampus": "Hippocampus proper",
        "Amygdala": "Amygdala",
        "CSF": "Cerebrospinal fluid",
        "Accumbens-area": "Nucleus accumbens",
        "VentralDC": "Ventral diencephalon",
        "vessel": "Vessel",
        "choroid-plexus": "Choroid plexus",
        "5th-Ventricle": "Fifth ventricle",
        "WM-hypointensities": "White matter hypointensities",
        "non-WM-hypointensities": "Non white matter hypointensities",
        "Optic-Chiasm": "Optic chiasm",
        "CC_Posterior": "Posterior part of the corpus callosum",
        "CC_Mid_Posterior": "Mid posterior part of the corpus callosum",
        "CC_Central": "Central part of the corpus callosum",
        "CC_Mid_Anterior": "Mid anterior part of the corpus callosum",
        "CC_Anterior": "Anterior part of the corpus callosum",
        "G_and_S_frontomargin": "Fronto-marginal gyrus (of Wernicke) and sulcus",
        "G_and_S_occipital_inf": "Inferior occipital gyrus (O3) and sulcus",
        "G_and_S_paracentral": "Paracentral lobule and sulcus",
        "G_and_S_subcentral": "	Subcentral gyrus (central operculum) and sulci",
        "G_and_S_transv_frontopol": "Transverse frontopolar gyri and sulci",
        "G_and_S_cingul-Ant": "Anterior part of the cingulate gyrus and sulcus (ACC)",
        "G_and_S_cingul-Mid-Ant": "Middle-anterior part of the cingulate gyrus and sulcus (aMCC)",
        "G_and_S_cingul-Mid-Post": "Middle-posterior part of the cingulate gyrus and sulcus (pMCC)",
        "G_cingul-Post-dorsal": "Posterior-dorsal part of the cingulate gyrus (dPCC)",
        "G_cingul-Post-ventral": "Posterior-ventral part of the cingulate gyrus (vPCC, isthmus of the cingulate gyrus)",
        "G_cuneus": "Cuneus (O6)",
        "G_front_inf-Opercular": "Opercular part of the inferior frontal gyrus",
        "G_front_inf-Orbital": "Orbital part of the inferior frontal gyrus",
        "G_front_inf-Triangul": "Triangular part of the inferior frontal gyrus",
        "G_front_middle": "Middle frontal gyrus (F2)",
        "G_front_sup": "Superior frontal gyrus (F1)",
        "G_Ins_lg_and_S_cent_ins": "Long insular gyrus and central sulcus of the insula",
        "G_insular_short": "Short insular gyri",
        "G_occipital_middle": "Middle occipital gyrus (O2, lateral occipital gyrus)",
        "G_occipital_sup": "Superior occipital gyrus (O1)",
        "G_oc-temp_lat-fusifor": "Lateral occipito-temporal gyrus (fusiform gyrus, O4-T4)",
        "G_oc-temp_med-Lingual": "Lingual gyrus, ligual part of the medial occipito-temporal gyrus, (O5)",
        "G_oc-temp_med-Parahip": "Parahippocampal gyrus, parahippocampal part of the medial occipito-temporal gyrus, (T5)",
        "G_orbital": "Orbital gyri",
        "G_pariet_inf-Angular": "Angular gyrus",
        "G_pariet_inf-Supramar": "Supramarginal gyrus",
        "G_parietal_sup": "Superior parietal lobule (lateral part of P1)",
        "G_postcentral": "Postcentral gyrus",
        "G_precentral": "Precentral gyrus",
        "G_precuneus": "Precuneus (medial part of P1)",
        "G_rectus": "Straight gyrus, Gyrus rectus",
        "G_subcallosal": "Subcallosal area, subcallosal gyrus",
        "G_temp_sup-G_T_transv": "Anterior transverse temporal gyrus (of Heschl)",
        "G_temp_sup-Lateral": "Lateral aspect of the superior temporal gyrus",
        "G_temp_sup-Plan_polar": "Planum polare of the superior temporal gyrus",
        "G_temp_sup-Plan_tempo": "Planum temporale or temporal plane of the superior temporal gyrus",
        "G_temporal_inf": "Inferior temporal gyrus (T3)",
        "G_temporal_middle": "Middle temporal gyrus (T2)",
        "Lat_Fis-ant-Horizont": "Horizontal ramus of the anterior segment of the lateral sulcus (or fissure)",
        "Lat_Fis-ant-Vertical": "Vertical ramus of the anterior segment of the lateral sulcus (or fissure)",
        "Lat_Fis-post": "Posterior ramus (or segment) of the lateral sulcus (or fissure)",
        "Pole_occipital": "Occipital pole",
        "Pole_temporal": "Temporal pole",
        "S_calcarine": "Calcarine sulcus",
        "S_central": "Central sulcus (Rolando's fissure)",
        "S_cingul-Marginalis": "Marginal branch (or part) of the cingulate sulcus",
        "S_circular_insula_ant": "Anterior segment of the circular sulcus of the insula",
        "S_circular_insula_inf": "Inferior segment of the circular sulcus of the insula",
        "S_circular_insula_sup": "Superior segment of the circular sulcus of the insula",
        "S_collat_transv_ant": "Anterior transverse collateral sulcus",
        "S_collat_transv_post": "Posterior transverse collateral sulcus",
        "S_front_inf": "Inferior frontal sulcus",
        "S_front_middle": "Middle frontal sulcus",
        "S_front_sup": "Superior frontal sulcus",
        "S_interm_prim-Jensen": "Sulcus intermedius primus (of Jensen)",
        "S_intrapariet_and_P_trans": "Intraparietal sulcus (interparietal sulcus) and transverse parietal sulci",
        "S_oc_middle_and_Lunatus": "Middle occipital sulcus and lunatus sulcus",
        "S_oc_sup_and_transversal": "Superior occipital sulcus and transverse occipital sulcus",
        "S_occipital_ant": "Anterior occipital sulcus and preoccipital notch (temporo-occipital incisure)",
        "S_oc-temp_lat": "Lateral occipito-temporal sulcus",
        "S_oc-temp_med_and_Lingual": "Medial occipito-temporal sulcus (collateral sulcus) and lingual sulcus",
        "S_orbital_lateral": "Lateral orbital sulcus",
        "S_orbital_med-olfact": "Medial orbital sulcus (olfactory sulcus)",
        "S_orbital-H_Shaped": "Orbital sulci (H-shaped sulci)",
        "S_parieto_occipital": "Parieto-occipital sulcus (or fissure)",
        "S_pericallosal": "Pericallosal sulcus (S of corpus callosum)",
        "S_postcentral": "Postcentral sulcus",
        "S_precentral-inf-part": "Inferior part of the precentral sulcus",
        "S_precentral-sup-part": "Superior part of the precentral sulcus",
        "S_suborbital": "Suborbital sulcus (sulcus rostrales, supraorbital sulcus)",
        "S_subparietal": "Subparietal sulcus",
        "S_temporal_inf": "Inferior temporal sulcus",
        "S_temporal_sup": "Superior temporal sulcus (parallel sulcus)",
        "S_temporal_transverse": "Transverse temporal sulcus",
    }

    plot_asymmetry_index(df_combined, df_aparc.index, roi_mapping, args.output_png)
    df_combined.index.names = ["roi"]
    df_combined.reset_index(inplace=True)
    if args.output.lower().endswith(".csv"):
        df_combined.to_csv(args.output)
    else:
        df_combined.to_json(args.output, orient="records", indent=4)


if __name__ == "__main__":
    main()
