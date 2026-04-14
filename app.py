import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Cover Crop Decision Support Tool",
    layout="wide",
)


DATA_CANDIDATES = [
    "cover_crop_scoring_model_table.csv",
    "final_cover_crop_master_table.csv",
    "final_cover_crop_master_table.xlsx",
]


COLUMN_ALIASES = {
    "crop_name": [
        "Common name",
        "Common Name",
        "common_name",
        "crop_name",
        "Crop",
    ],
    "scientific_name": [
        "Scientific name",
        "Scientific Name",
        "scientific_name",
    ],
    "season": [
        "Season",
        "season",
        "Region of growth",
        "Region of growth (cool/warm)",
        "Region",
    ],
    "life_cycle": [
        "Life cycle",
        "Life Cycle",
        "life_cycle",
    ],
    "functional_uses": [
        "Functional uses",
        "Functional use",
        "Function",
        "Uses",
    ],
    "warnings": [
        "Warnings / negative effects",
        "Warnings",
        "Warnings/negative effects",
        "Risk notes",
    ],
    "plant_structure": [
        "Plant structure",
        "Plant Structure",
        "plant_structure",
    ],
    "root_type": [
        "Root type",
        "Root Type",
        "root_type",
    ],
    "crude_protein": [
        "Crude protein (%)",
        "Crude Protein (%)",
        "Crude protein",
        "crude_protein",
    ],
    "prohibitive_soil": [
        "Prohibitive soil",
        "Prohibitive Soil",
        "prohibitive_soil",
    ],
    "cn_ratio": [
        "C:N ratio",
        "CN_Ratio",
        "C:N Ratio",
        "cn_ratio",
    ],
    "nitrogen_fixation_score": [
        "Nitrogen fixation score",
        "nitrogen_fixation_score",
        "nitrogen_fixation",
        "Nitrogen Fixation Score",
    ],
    "erosion_control_score": [
        "Erosion control score",
        "erosion_control_score",
        "erosion_control",
        "Erosion Control Score",
    ],
    "weed_suppression_score": [
        "Weed suppression score",
        "weed_suppression_score",
        "weed_suppression",
        "Weed Suppression Score",
    ],
    "root_depth_score": [
        "Root depth score",
        "root_depth_score",
        "root_depth",
        "Root Depth Score",
    ],
    "forage_value_score": [
        "Forage value score",
        "forage_value_score",
        "forage_value",
        "Forage Value Score",
    ],
    "soil_adaptability_score": [
        "Soil adaptability score",
        "soil_adaptability_score",
        "soil_adaptability",
        "Soil Adaptability Score",
    ],
    "cost_level_score": [
        "Cost level score",
        "cost_level_score",
        "cost_level",
        "Cost Level Score",
    ],
    "risk_factor_score": [
        "Risk factor score",
        "risk_factor_score",
        "risk_factor",
        "Risk Factor Score",
    ],
}


PRIORITY_FIELDS = [
    "nitrogen_fixation_score",
    "erosion_control_score",
    "weed_suppression_score",
    "root_depth_score",
    "forage_value_score",
    "soil_adaptability_score",
    "cost_level_score",
    "risk_factor_score",
]


def find_existing_column(df: pd.DataFrame, names: list[str]) -> str | None:
    for name in names:
        if name in df.columns:
            return name
    return None


@st.cache_data
def load_data() -> tuple[pd.DataFrame, str]:
    for file_name in DATA_CANDIDATES:
        path = Path(file_name)
        if path.exists():
            if path.suffix.lower() == ".csv":
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            return df, file_name
    raise FileNotFoundError(
        "No data file found. Place one of these files in the same folder as app.py: "
        + ", ".join(DATA_CANDIDATES)
    )


def parse_first_numeric(value) -> float | None:
    if pd.isna(value):
        return None
    text = str(value)
    matches = re.findall(r"\d+(?:\.\d+)?", text)
    if not matches:
        return None
    nums = [float(x) for x in matches]
    return float(sum(nums) / len(nums))


def standardize_base_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {}
    for standard_name, aliases in COLUMN_ALIASES.items():
        existing = find_existing_column(df, aliases)
        if existing:
            renamed[existing] = standard_name
    out = df.rename(columns=renamed).copy()

    for col in [
        "crop_name",
        "scientific_name",
        "season",
        "life_cycle",
        "functional_uses",
        "warnings",
        "plant_structure",
        "root_type",
        "crude_protein",
        "prohibitive_soil",
        "cn_ratio",
    ]:
        if col not in out.columns:
            out[col] = ""

    text_cols = [
        "crop_name",
        "scientific_name",
        "season",
        "life_cycle",
        "functional_uses",
        "warnings",
        "plant_structure",
        "root_type",
        "crude_protein",
        "prohibitive_soil",
        "cn_ratio",
    ]
    for col in text_cols:
        out[col] = out[col].fillna("").astype(str).str.strip()

    out["season"] = out["season"].str.title()
    out["life_cycle"] = out["life_cycle"].str.title()
    return out


def score_from_text(df: pd.DataFrame) -> pd.DataFrame:
    uses = df["functional_uses"].str.lower()
    warnings = df["warnings"].str.lower()
    roots = df["root_type"].str.lower()
    soils = df["prohibitive_soil"].str.lower()
    protein = df["crude_protein"].apply(parse_first_numeric)
    cn = df["cn_ratio"].apply(parse_first_numeric)

    if "nitrogen_fixation_score" not in df.columns:
        df["nitrogen_fixation_score"] = np.select(
            [
                uses.str.contains("nitrogen fix"),
                uses.str.contains("legume|nitrogen scaveng"),
            ],
            [5, 3],
            default=1,
        )

    if "erosion_control_score" not in df.columns:
        df["erosion_control_score"] = np.select(
            [
                uses.str.contains("erosion"),
                uses.str.contains("soil builder|compaction|cover"),
            ],
            [5, 3],
            default=2,
        )

    if "weed_suppression_score" not in df.columns:
        df["weed_suppression_score"] = np.select(
            [
                uses.str.contains("weed suppress|weed control|control of annual weed"),
                warnings.str.contains("weak weed competitor"),
            ],
            [5, 1],
            default=2,
        )

    if "root_depth_score" not in df.columns:
        df["root_depth_score"] = np.select(
            [
                roots.str.contains("deep|taproot|tap root|deep-rooting"),
                roots.str.contains("fibrous|lateral"),
            ],
            [5, 3],
            default=2,
        )

    if "forage_value_score" not in df.columns:
        forage = np.select(
            [
                uses.str.contains("forage|feed|graz"),
                protein.fillna(0) >= 20,
                protein.fillna(0) >= 10,
            ],
            [5, 4, 3],
            default=2,
        )
        df["forage_value_score"] = forage

    if "soil_adaptability_score" not in df.columns:
        soil_penalty = soils.str.count(";") + soils.replace("", np.nan).notna().astype(int)
        adaptability = 5 - soil_penalty.clip(upper=4)
        df["soil_adaptability_score"] = adaptability.fillna(3).clip(lower=1, upper=5)

    if "cost_level_score" not in df.columns:
        df["cost_level_score"] = np.select(
            [
                df["life_cycle"].str.contains("Perennial", case=False),
                uses.str.contains("quick grower|easy|annual"),
            ],
            [2, 4],
            default=3,
        )

    if "risk_factor_score" not in df.columns:
        risk_hits = (
            warnings.str.count("disease|susceptible|tox|bloat|invasive|difficult|poison|host")
        )
        risk = 5 - risk_hits.clip(upper=4)
        risk = risk.where(warnings.ne(""), 4)
        df["risk_factor_score"] = risk.clip(lower=1, upper=5)

    for col in PRIORITY_FIELDS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(3).clip(lower=1, upper=5)

    df["_protein_value"] = protein
    df["_cn_value"] = cn
    return df


def compute_weighted_scores(df: pd.DataFrame, weights: dict[str, int]) -> tuple[pd.DataFrame, dict[str, float]]:
    total = sum(weights.values())
    if total == 0:
        normalized = {k: 0 for k in weights}
    else:
        normalized = {k: v / total for k, v in weights.items()}

    result = df.copy()
    result["cost_preference_score"] = 6 - result["cost_level_score"]
    result["risk_preference_score"] = 6 - result["risk_factor_score"]

    result["score"] = (
        result["nitrogen_fixation_score"] * normalized["nitrogen_fixation_score"]
        + result["erosion_control_score"] * normalized["erosion_control_score"]
        + result["weed_suppression_score"] * normalized["weed_suppression_score"]
        + result["root_depth_score"] * normalized["root_depth_score"]
        + result["forage_value_score"] * normalized["forage_value_score"]
        + result["soil_adaptability_score"] * normalized["soil_adaptability_score"]
        + result["cost_preference_score"] * normalized["cost_level_score"]
        + result["risk_preference_score"] * normalized["risk_factor_score"]
    )

    result = result.sort_values("score", ascending=False).reset_index(drop=True)
    return result, normalized


try:
    raw_df, loaded_file = load_data()
except Exception as e:
    st.error(str(e))
    st.stop()

df = standardize_base_columns(raw_df)
df = score_from_text(df)

st.title("Cover Crop Decision Support Tool")
st.markdown(
    """
This tool ranks cover crop options using a weighted recommendation model based on
user-defined priorities such as nitrogen fixation, erosion control, weed suppression,
root depth, forage value, soil adaptability, cost, and risk.

Adjust the inputs in the sidebar to generate recommendations.
"""
)

st.sidebar.title("Input Parameters")

season_options = ["Any"] + sorted([x for x in df["season"].dropna().unique() if x])
life_cycle_options = ["Any"] + sorted([x for x in df["life_cycle"].dropna().unique() if x])

selected_season = st.sidebar.selectbox("Season / Region", season_options)
selected_life_cycle = st.sidebar.selectbox("Life Cycle", life_cycle_options)
num_recommendations = st.sidebar.slider("Number of Recommendations", 1, 10, 3)

st.sidebar.markdown("---")
st.sidebar.subheader("Priority Weights")

weights = {
    "nitrogen_fixation_score": st.sidebar.slider(
        "Nitrogen Fixation",
        0,
        50,
        50,
        help="Higher values prioritize crops with greater nitrogen fixation.",
    ),
    "erosion_control_score": st.sidebar.slider(
        "Erosion Control",
        0,
        50,
        50,
        help="Higher values prioritize crops that protect soil from erosion.",
    ),
    "weed_suppression_score": st.sidebar.slider(
        "Weed Suppression",
        0,
        50,
        50,
        help="Higher values prioritize crops with stronger weed suppression.",
    ),
    "root_depth_score": st.sidebar.slider(
        "Root Depth",
        0,
        50,
        20,
        help="Higher values prioritize crops with deeper or stronger root systems.",
    ),
    "forage_value_score": st.sidebar.slider(
        "Forage Value",
        0,
        50,
        20,
        help="Higher values prioritize crops useful for forage or feed.",
    ),
    "soil_adaptability_score": st.sidebar.slider(
        "Soil Adaptability",
        0,
        50,
        20,
        help="Higher values prioritize crops with fewer soil restrictions.",
    ),
    "cost_level_score": st.sidebar.slider(
        "Cost Importance",
        0,
        50,
        0,
        help="Higher values favor lower-cost crop options.",
    ),
    "risk_factor_score": st.sidebar.slider(
        "Risk Avoidance",
        0,
        50,
        40,
        help="Higher values favor more reliable and lower-risk crop options.",
    ),
}

filtered = df.copy()
if selected_season != "Any":
    filtered = filtered[filtered["season"].str.lower() == selected_season.lower()]
if selected_life_cycle != "Any":
    filtered = filtered[filtered["life_cycle"].str.lower() == selected_life_cycle.lower()]

if filtered.empty:
    st.warning("No crops match the selected filters. Please adjust the inputs.")
    st.stop()

results, normalized_weights = compute_weighted_scores(filtered, weights)
top_results = results.head(num_recommendations).copy()

col1, col2 = st.columns([1.8, 1])

with col1:
    st.subheader("Top Recommendations")
    display_table = top_results[
        [
            "crop_name",
            "scientific_name",
            "season",
            "life_cycle",
            "score",
        ]
    ].rename(
        columns={
            "crop_name": "Common Name",
            "scientific_name": "Scientific Name",
            "season": "Season / Region",
            "life_cycle": "Life Cycle",
            "score": "Recommendation Score",
        }
    )
    display_table["Recommendation Score"] = display_table["Recommendation Score"].round(2)
    st.dataframe(display_table, use_container_width=True, hide_index=True)

with col2:
    st.subheader("Weight Distribution")
    weights_df = pd.DataFrame(
        {
            "Priority": [
                "Nitrogen fixation",
                "Erosion control",
                "Weed suppression",
                "Root depth",
                "Forage value",
                "Soil adaptability",
                "Cost importance",
                "Risk avoidance",
            ],
            "Normalized Weight": list(normalized_weights.values()),
        }
    )
    weights_df["Normalized Weight"] = weights_df["Normalized Weight"].round(2)
    st.dataframe(weights_df, use_container_width=True, hide_index=True)

st.subheader("Recommendation Details")
for _, row in top_results.iterrows():
    title = f"{row['crop_name']} — score {row['score']:.2f}"
    with st.expander(title):
        left, right = st.columns(2)
        with left:
            st.write(f"**Scientific name:** {row['scientific_name']}")
            st.write(f"**Season / Region:** {row['season']}")
            st.write(f"**Life cycle:** {row['life_cycle']}")
            st.write(f"**Functional uses:** {row['functional_uses']}")
            st.write(f"**Plant structure:** {row['plant_structure']}")
            st.write(f"**Root type:** {row['root_type']}")
        with right:
            st.write(f"**Warnings:** {row['warnings']}")
            st.write(f"**Crude protein:** {row['crude_protein']}")
            st.write(f"**Prohibitive soil:** {row['prohibitive_soil']}")
            st.write(f"**C:N ratio:** {row['cn_ratio']}")

        st.markdown("**Scoring profile**")
        score_profile = pd.DataFrame(
            {
                "Trait": [
                    "Nitrogen fixation",
                    "Erosion control",
                    "Weed suppression",
                    "Root depth",
                    "Forage value",
                    "Soil adaptability",
                    "Cost preference score",
                    "Risk preference score",
                ],
                "Value": [
                    row["nitrogen_fixation_score"],
                    row["erosion_control_score"],
                    row["weed_suppression_score"],
                    row["root_depth_score"],
                    row["forage_value_score"],
                    row["soil_adaptability_score"],
                    6 - row["cost_level_score"],
                    6 - row["risk_factor_score"],
                ],
            }
        )
        st.dataframe(score_profile, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(f"Loaded data file: {loaded_file}")
st.caption("Developed as a decision support tool for cover crop selection using a weighted scoring model.")
