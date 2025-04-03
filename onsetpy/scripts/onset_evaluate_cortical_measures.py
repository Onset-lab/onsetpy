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
    parser.add_argument("output", help="Path to the output PNG file")
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
        print(roi, left_value, right_value, asymmetry_index[roi])

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
    print(df_combined)
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
    assert_outputs_exist(parser, args, [args.output])

    if not args.output.lower().endswith(".png"):
        parser.error("Output file must be a PNG file.")

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
        "Lateral-Ventricle": "Lateral Ventricle",
        "Inf-Lat-Vent": "Inferior Lateral Ventricle",
        "Cerebellum-White-Matter": "Cerebellar White Matter",
        "Cerebellum-Cortex": "Cerebellar Cortex",
        "Thalamus": "Thalamus",
        "Caudate": "Caudate Nucleus",
        "Putamen": "Putamen",
        "Pallidum": "Globus Pallidus",
        "3rd-Ventricle": "Third Ventricle",
        "4th-Ventricle": "Fourth Ventricle",
        "Brain-Stem": "Brainstem",
        "Hippocampus": "Hippocampus",
        "Amygdala": "Amygdala",
        "CSF": "Cerebrospinal Fluid",
        "Accumbens-area": "Nucleus Accumbens",
        "VentralDC": "Ventral Diencephalon",
        "vessel": "Vessel",
        "choroid-plexus": "Choroid Plexus",
        "5th-Ventricle": "Fifth Ventricle",
        "WM-hypointensities": "White Matter Hypointensities",
        "non-WM-hypointensities": "Non White Matter Hypointensities",
        "Optic-Chiasm": "Optic Chiasm",
        "CC_Posterior": "Corpus Callosum Posterior",
        "CC_Mid_Posterior": "Corpus Callosum Mid Posterior",
        "CC_Central": "Corpus Callosum Central",
        "CC_Mid_Anterior": "Corpus Callosum Mid Anterior",
        "CC_Anterior": "Corpus Callosum Anterior",
        "G_and_S_frontomargin": "Frontomarginal Gyrus and Sulcus",
        "G_and_S_occipital_inf": "Inferior Occipital Gyrus and Sulcus",
        "G_and_S_paracentral": "Paracentral Gyrus and Sulcus",
        "G_and_S_subcentral": "Subcentral Gyrus and Sulcus",
        "G_and_S_transv_frontopol": "Transverse Frontopolar Gyrus and Sulcus",
        "G_and_S_cingul-Ant": "Anterior Cingulate Gyrus and Sulcus",
        "G_and_S_cingul-Mid-Ant": "Middle Anterior Cingulate Gyrus and Sulcus",
        "G_and_S_cingul-Mid-Post": "Middle Posterior Cingulate Gyrus and Sulcus",
        "G_cingul-Post-dorsal": "Posterior Dorsal Cingulate Gyrus",
        "G_cingul-Post-ventral": "Posterior Ventral Cingulate Gyrus",
        "G_cuneus": "Cuneus Gyrus",
        "G_front_inf-Opercular": "Inferior Frontal Gyrus Opercular Part",
        "G_front_inf-Orbital": "Inferior Frontal Gyrus Orbital Part",
        "G_front_inf-Triangul": "Inferior Frontal Gyrus Triangular Part",
        "G_front_middle": "Middle Frontal Gyrus",
        "G_front_sup": "Superior Frontal Gyrus",
        "G_Ins_lg_and_S_cent_ins": "Long Insular Gyrus and Central Insular Sulcus",
        "G_insular_short": "Short Insular Gyri",
        "G_occipital_middle": "Middle Occipital Gyrus",
        "G_occipital_sup": "Superior Occipital Gyrus",
        "G_oc-temp_lat-fusifor": "Lateral Occipitotemporal Fusiform Gyrus",
        "G_oc-temp_med-Lingual": "Medial Occipitotemporal Lingual Gyrus",
        "G_oc-temp_med-Parahip": "Medial Occipitotemporal Parahippocampal Gyrus",
        "G_orbital": "Orbital Gyrus",
        "G_pariet_inf-Angular": "Inferior Parietal Angular Gyrus",
        "G_pariet_inf-Supramar": "Inferior Parietal Supramarginal Gyrus",
        "G_parietal_sup": "Superior Parietal Gyrus",
        "G_postcentral": "Postcentral Gyrus",
        "G_precentral": "Precentral Gyrus",
        "G_precuneus": "Precuneus Gyrus",
        "G_rectus": "Rectus Gyrus",
        "G_subcallosal": "Subcallosal Gyrus",
        "G_temp_sup-G_T_transv": "Superior Temporal Gyrus Transversal",
        "G_temp_sup-Lateral": "Superior Temporal Gyrus Lateral",
        "G_temp_sup-Plan_polar": "Superior Temporal Gyrus Planum Polare",
        "G_temp_sup-Plan_tempo": "Superior Temporal Gyrus Planum Temporale",
        "G_temporal_inf": "Inferior Temporal Gyrus",
        "G_temporal_middle": "Middle Temporal Gyrus",
        "Lat_Fis-ant-Horizont": "Anterior Horizontal Lateral Fissure",
        "Lat_Fis-ant-Vertical": "Anterior Vertical Lateral Fissure",
        "Lat_Fis-post": "Posterior Lateral Fissure",
        "Pole_occipital": "Occipital Pole",
        "Pole_temporal": "Temporal Pole",
        "S_calcarine": "Calcarine Sulcus",
        "S_central": "Central Sulcus",
        "S_cingul-Marginalis": "Cingulate Sulcus Marginalis",
        "S_circular_insula_ant": "Anterior Circular Insular Sulcus",
        "S_circular_insula_inf": "Inferior Circular Insular Sulcus",
        "S_circular_insula_sup": "Superior Circular Insular Sulcus",
        "S_collat_transv_ant": "Anterior Transverse Collateral Sulcus",
        "S_collat_transv_post": "Posterior Transverse Collateral Sulcus",
        "S_front_inf": "Inferior Frontal Sulcus",
        "S_front_middle": "Middle Frontal Sulcus",
        "S_front_sup": "Superior Frontal Sulcus",
        "S_interm_prim-Jensen": "Intermedius Primus Sulcus (Jensen)",
        "S_intrapariet_and_P_trans": "Intrapariet and P Trans Sulcus",
        "S_oc_middle_and_Lunatus": "Middle Occipital and Lunatus Sulcus",
        "S_oc_sup_and_transversal": "Superior Occipital and Transversal Sulcus",
        "S_occipital_ant": "Anterior Occipital Sulcus",
        "S_oc-temp_lat": "Lateral Occipitotemporal Sulcus",
        "S_oc-temp_med_and_Lingual": "Medial Occipitotemporal and Lingual Sulcus",
        "S_orbital_lateral": "Lateral Orbital Sulcus",
        "S_orbital_med-olfact": "Medial Orbital Olfactory Sulcus",
        "S_orbital-H_Shaped": "H-Shaped Orbital Sulcus",
        "S_parieto_occipital": "Parieto Occipital Sulcus",
        "S_pericallosal": "Pericallosal Sulcus",
        "S_postcentral": "Postcentral Sulcus",
        "S_precentral-inf-part": "Inferior Part of Precentral Sulcus",
        "S_precentral-sup-part": "Superior Part of Precentral Sulcus",
        "S_suborbital": "Suborbital Sulcus",
        "S_subparietal": "Subparietal Sulcus",
        "S_temporal_inf": "Inferior Temporal Sulcus",
        "S_temporal_sup": "Superior Temporal Sulcus",
        "S_temporal_transverse": "Transverse Temporal Sulcus",
    }

    plot_asymmetry_index(df_combined, df_aparc.index, roi_mapping, args.output)


if __name__ == "__main__":
    main()
