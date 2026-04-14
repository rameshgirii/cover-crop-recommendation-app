import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Cover Crop Decision Support Tool", page_icon="🌱", layout="wide")

DATA_CANDIDATES = [
    Path("cover_crop_scoring_model_table.csv"),
    Path("final_cover_crop_master_table.xlsx"),
    Path("final_cover_crop_master_table.csv"),
]

BENEFIT_COLS = [
    'Nitrogen fixation score',
    'Erosion control score',
    'Weed suppression score',
    'Root depth score',
    'Forage value score',
    'Soil adaptability score'
]
PENALTY_COLS = ['Cost level score', 'Risk factor score']
ALL_SCORE_COLS = BENEFIT_COLS + PENALTY_COLS

DEFAULT_WEIGHTS = {
    'Nitrogen fixation score': 30,
    'Erosion control score': 20,
    'Weed suppression score': 20,
    'Root depth score': 10,
    'Forage value score': 5,
    'Soil adaptability score': 5,
    'Cost level score': 5,
    'Risk factor score': 5,
}

FRIENDLY = {
    'Nitrogen fixation score': 'Nitrogen fixation',
    'Erosion control score': 'Erosion control',
    'Weed suppression score': 'Weed suppression',
    'Root depth score': 'Root depth',
    'Forage value score': 'Forage value',
    'Soil adaptability score': 'Soil adaptability',
    'Cost level score': 'Low cost preference',
    'Risk factor score': 'Low risk preference',
}


def load_data():
    for path in DATA_CANDIDATES:
        if path.exists():
            if path.suffix.lower() == '.csv':
                return pd.read_csv(path), path.name
            return pd.read_excel(path)
    return None, None


def derive_scores(df):
    data = df.copy()
    if 'Season' not in data.columns and 'Region of growth' in data.columns:
        data['Season'] = data['Region of growth']

    if 'Common name' not in data.columns and 'CommonName' in data.columns:
        data['Common name'] = data['CommonName']
    if 'Scientific name' not in data.columns and 'ScientificName' in data.columns:
        data['Scientific name'] = data['ScientificName']
    if 'Functional uses' not in data.columns and 'Function' in data.columns:
        data['Functional uses'] = data['Function']
    if 'Warnings / negative effects' not in data.columns and 'Warnings' in data.columns:
        data['Warnings / negative effects'] = data['Warnings']

    text_cols = ['Functional uses', 'Warnings / negative effects', 'Root type', 'Prohibitive soil']
    for c in text_cols:
        if c not in data.columns:
            data[c] = ''
        data[c] = data[c].fillna('').astype(str)

    if 'Nitrogen fixation score' not in data.columns:
        data['Nitrogen fixation score'] = data['Functional uses'].str.lower().apply(
            lambda x: 5 if 'nitrogen' in x and 'fix' in x else 1
        )
    if 'Erosion control score' not in data.columns:
        data['Erosion control score'] = data['Functional uses'].str.lower().apply(
            lambda x: 5 if 'erosion' in x else (4 if 'soil' in x else 2)
        )
    if 'Weed suppression score' not in data.columns:
        data['Weed suppression score'] = data['Functional uses'].str.lower().apply(
            lambda x: 5 if 'weed' in x else 2
        )
    if 'Root depth score' not in data.columns:
        def root_score(x):
            x = x.lower()
            if 'deep' in x and 'tap' in x:
                return 5
            if 'taproot' in x or 'tap root' in x:
                return 4
            if 'fibrous' in x:
                return 3
            return 2
        data['Root depth score'] = data['Root type'].apply(root_score)
    if 'Forage value score' not in data.columns:
        data['Forage value score'] = data['Functional uses'].str.lower().apply(
            lambda x: 4 if any(k in x for k in ['forage', 'graz', 'feed', 'livestock']) else 2
        )
    if 'Soil adaptability score' not in data.columns:
        def soil_score(x):
            x = x.lower()
            restrictions = sum(k in x for k in ['saline', 'alkaline', 'acid', 'waterlog', 'flood', 'sodic', 'heavy'])
            return max(1, 5 - restrictions)
        data['Soil adaptability score'] = data['Prohibitive soil'].apply(soil_score)
    if 'Cost level score' not in data.columns:
        data['Cost level score'] = 3
    if 'Risk factor score' not in data.columns:
        def risk_score(x):
            x = x.lower()
            count = sum(k in x for k in ['toxic', 'bloat', 'invasive', 'disease', 'pest', 'difficult', 'injury'])
            return min(5, max(1, count + 1))
        data['Risk factor score'] = data['Warnings / negative effects'].apply(risk_score)

    for c in ALL_SCORE_COLS:
        data[c] = pd.to_numeric(data[c], errors='coerce').fillna(3).clip(1, 5)
    return data


def normalize_weights(weights):
    total = sum(weights.values())
    if total == 0:
        return {k: 1 / len(weights) for k in weights}
    return {k: v / total for k, v in weights.items()}


def apply_model(df, weights, season_choice, life_cycle_choice, top_n):
    out = df.copy()
    if season_choice != 'Any' and 'Season' in out.columns:
        out = out[out['Season'].astype(str).str.lower() == season_choice.lower()]
    if life_cycle_choice != 'Any' and 'Life cycle' in out.columns:
        out = out[out['Life cycle'].astype(str).str.lower() == life_cycle_choice.lower()]

    norm = normalize_weights(weights)
    out['Recommendation score'] = 0.0
    for col, wt in norm.items():
        if col in BENEFIT_COLS:
            out['Recommendation score'] += out[col] * wt
        else:
            out['Recommendation score'] += (6 - out[col]) * wt
    out['Recommendation score'] = out['Recommendation score'].round(3)
    out = out.sort_values('Recommendation score', ascending=False).reset_index(drop=True)
    return out.head(top_n), norm


def explain_row(row):
    reasons = []
    if row['Nitrogen fixation score'] >= 4:
        reasons.append('strong nitrogen benefit')
    if row['Erosion control score'] >= 4:
        reasons.append('good erosion control')
    if row['Weed suppression score'] >= 4:
        reasons.append('good weed suppression')
    if row['Root depth score'] >= 4:
        reasons.append('strong root system')
    if row['Soil adaptability score'] >= 4:
        reasons.append('broader soil adaptability')
    if row['Risk factor score'] <= 2:
        reasons.append('lower warning risk')
    return '; '.join(reasons) if reasons else 'balanced agronomic profile'


df_raw, source_name = load_data()

st.title('🌱 Cover Crop Decision Support Tool')
st.write('This Streamlit prototype ranks cover crops using a weighted recommendation model based on user priorities such as nitrogen fixation, erosion control, weed suppression, cost, and risk.')

if df_raw is None:
    st.error('No input data file was found. Put cover_crop_scoring_model_table.csv or final_cover_crop_master_table.xlsx in the same folder as app.py.')
    st.stop()

df = derive_scores(df_raw)

with st.sidebar:
    st.header('User inputs')
    season_options = ['Any'] + sorted(df['Season'].dropna().astype(str).unique().tolist()) if 'Season' in df.columns else ['Any']
    life_cycle_options = ['Any'] + sorted(df['Life cycle'].dropna().astype(str).unique().tolist()) if 'Life cycle' in df.columns else ['Any']
    season_choice = st.selectbox('Preferred season/region', season_options, index=0)
    life_cycle_choice = st.selectbox('Preferred life cycle', life_cycle_options, index=0)
    top_n = st.slider('Number of recommendations', min_value=3, max_value=10, value=5)
    st.markdown('### Priority weights')
    weights = {}
    for col in ALL_SCORE_COLS:
        weights[col] = st.slider(FRIENDLY[col], min_value=0, max_value=50, value=DEFAULT_WEIGHTS[col], step=5)

results, norm_weights = apply_model(df, weights, season_choice, life_cycle_choice, top_n)

c1, c2 = st.columns([2, 1])
with c1:
    st.subheader('Top recommendations')
    if results.empty:
        st.warning('No crops matched the selected filters. Try choosing broader settings.')
    else:
        display_cols = [c for c in [
            'Common name','Scientific name','Season','Life cycle','Recommendation score',
            'Nitrogen fixation score','Erosion control score','Weed suppression score',
            'Root depth score','Forage value score','Soil adaptability score',
            'Cost level score','Risk factor score'
        ] if c in results.columns]
        st.dataframe(results[display_cols], use_container_width=True)

with c2:
    st.subheader('Normalized weights')
    weight_df = pd.DataFrame({
        'Trait': [FRIENDLY[k] for k in norm_weights.keys()],
        'Weight': [round(v, 3) for v in norm_weights.values()]
    }).sort_values('Weight', ascending=False)
    st.dataframe(weight_df, use_container_width=True, hide_index=True)

st.subheader('Recommendation details')
if not results.empty:
    for _, row in results.iterrows():
        with st.expander(f"{row.get('Common name', 'Crop')} — score {row['Recommendation score']}"):
            st.write(f"**Why recommended:** {explain_row(row)}")
            left, right = st.columns(2)
            with left:
                for field in ['Scientific name', 'Season', 'Life cycle', 'Root type', 'Plant structure', 'Crude protein', 'C:N ratio']:
                    if field in row.index:
                        st.write(f"**{field}:** {row[field]}")
            with right:
                for field in ['Functional uses', 'Warnings / negative effects', 'Prohibitive soil']:
                    if field in row.index:
                        st.write(f"**{field}:** {row[field]}")

st.subheader('Data source')
st.caption(f"Loaded data file: {source_name}")
