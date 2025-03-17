#!/usr/bin/env python3

"""
Compare a patient to our database of cortical measures.
"""

import argparse
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch
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
        "aparc_csv",
        help="Path to the patient aparc CSV file",
    )

    parser.add_argument(
        "aseg_csv",
        help="Path to the patient aseg CSV file",
    )

    # parser.add_argument("patient_age", help="Patient age.", type=float)
    # parser.add_argument("patient_sex", help="Patient sex.", choices=[1, 2], type=int)
    # parser.add_argument(
    #     "database_csv",
    #     help="Path to the database CSV file",
    # )
    parser.add_argument("output", help="Path to the output PNG file")

    parser.add_argument(
        "--age_window",
        type=int,
        help="Age window for filtering. For example, if the patient is 30 years old, with a window of 5, the controls between 28 and 32 will be used.",
        default=5,
    )

    parser.add_argument(
        "--z_threshold", type=float, help="Z-score threshold", default=2
    )

    add_overwrite_arg(parser)
    add_version_arg(parser)
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    # assert_inputs_exist(parser, [args.aparc_csv, args.aseg_csv, args.database_csv])
    # assert_outputs_exist(parser, args, [args.output])

    # if not args.output.lower().endswith(".csv"):
    #     parser.error("Output file must be a CSV file.")

    # df_db = pd.read_csv(args.database_csv)
    aparc = pd.read_csv(args.aparc_csv)

    # Filter for females (sex=2) and age between 20-25
    # min_age = args.patient_age - args.age_window / 2
    # max_age = args.patient_age + args.age_window / 2
    # filtered_df = df_db[
    #     (df_db["sex"] == args.patient_sex) & (df_db["age"].between(min_age, max_age))
    # ]

    # Get all ROI columns (excluding non-ROI columns like 'age' and 'sex')
    roi_columns = aparc["roi"].unique()

    # Calculate z-scores for each ROI
    # z_scores = {}
    # for side in aparc["side"].unique():
    #     for roi in roi_columns:
    #         roi_mean = filtered_df.loc[
    #             (filtered_df["roi"] == roi) & (filtered_df["side"] == side), "thickness"
    #         ].mean()
    #         roi_std = filtered_df.loc[
    #             (filtered_df["roi"] == roi) & (filtered_df["side"] == side), "thickness"
    #         ].std()
    #         patient_value = aparc.loc[
    #             (aparc["roi"] == roi) & (aparc["side"] == side), "thickness"
    #         ].iloc[0]
    #         z_scores[roi] = (patient_value - roi_mean) / roi_std
    #         if abs(z_scores[roi]) > args.z_threshold:
    #             print(
    #                 f"Warning: {side} {roi} z-score is greater than {args.z_threshold} ({z_scores[roi]})"

    aparc_asymetry_index = {}
    for roi in roi_columns:
        patient_value_left = aparc.loc[
            (aparc["roi"] == roi) & (aparc["side"] == "left"), "thickness"
        ].iloc[0]
        patient_value_right = aparc.loc[
            (aparc["roi"] == roi) & (aparc["side"] == "right"), "thickness"
        ].iloc[0]
        aparc_asymetry_index[roi] = (
            (patient_value_right - patient_value_left) / patient_value_left * 100
        )
    df_ai = pd.DataFrame([aparc_asymetry_index]).transpose()
    df_ai.columns = ["asymmetry_index"]
    df_ai = df_ai[df_ai["asymmetry_index"].abs() >= args.z_threshold]

    # Dictionary mapping FreeSurfer ROIs to full anatomical names
    roi_mapping = {
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

    # Convert to DataFrame for easier handling
    # z_score_df = pd.DataFrame([z_scores])
    # print(z_scores)
    # print(df_db)
    aseg = pd.read_csv(args.aseg_csv)
    aseg = aseg[aseg["volume"] != 0]
    rois = [
        roi.replace("Left-", "").replace("Right-", "")
        for roi in aseg["roi"].unique()
        if "Left" in roi or "Right" in roi
    ]
    rois = list(set(rois))

    aseg_asymetry_index = {}
    for roi in rois:
        patient_value_left = aseg.loc[(aseg["roi"] == "Left-" + roi), "volume"].iloc[0]
        patient_value_right = aseg.loc[(aseg["roi"] == "Right-" + roi), "volume"].iloc[
            0
        ]

        aseg_asymetry_index[roi] = (
            (patient_value_right - patient_value_left) / patient_value_left * 100
        )

    df_ai_aseg = pd.DataFrame([aseg_asymetry_index]).transpose()
    df_ai_aseg.columns = ["asymmetry_index"]
    df_ai_aseg = df_ai_aseg[df_ai_aseg["asymmetry_index"].abs() >= args.z_threshold]
    # Concatenate both dataframes and sort by asymmetry index
    df_combined = pd.concat([df_ai, df_ai_aseg])
    df_combined = df_combined.sort_values(by="asymmetry_index", ascending=False)

    # Create combined visualization

    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, max(6, len(df_combined) * 0.3)))
    sns.set_style("whitegrid")

    # Create color list based on index source (aparc or aseg)
    colors = [
        "#FF6B6B" if idx in df_ai.index else "#4ECDC4" for idx in df_combined.index
    ]
    df_combined.index = df_combined.index.map(lambda x: roi_mapping.get(x, x))
    ax = sns.barplot(
        data=df_combined, y=df_combined.index, x="asymmetry_index", palette=colors
    )
    plt.title(
        "ROI Relative Asymmetry Index (right compared to left)", pad=20, fontsize=12
    )
    plt.xlabel("Relative Asymmetry Index (%)", fontsize=10)
    plt.ylabel("ROI", fontsize=10)

    # Add legend
    legend_elements = [
        Patch(facecolor="#FF6B6B", label="Cortical (thickness)"),
        Patch(facecolor="#4ECDC4", label="Subcortical (volume)"),
    ]
    ax.legend(handles=legend_elements)

    sns.despine()
    plt.tight_layout()
    # plt.show()
    plt.savefig(args.output, dpi=300)


if __name__ == "__main__":
    main()
