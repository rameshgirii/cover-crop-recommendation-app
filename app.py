import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Cover Crop Selector", page_icon="🌱", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("scored_cover_crops.csv")

def split_items(text):
    return [x.strip() for x in str(text).split(';') if str(x).strip()]

def normalize_soil_label(soil):
    s = str(soil).strip().lower()
    if not s or 'high boron' in s:
        return None
    if 'waterlogged' in s or 'poorly drained' in s or 'flooded' in s or 'high water table' in s:
        return 'Waterlogged / poorly drained soil'
    if 'acidic' in s:
        return 'Acidic soil'
    if 'alkaline' in s:
        return 'Alkaline soil'
    if 'saline' in s:
        return 'Saline soil'
    if 'compacted' in s:
        return 'Compacted soil'
    if 'coarse' in s or 'gravelly' in s or 'sandy' in s or s == 'sand':
        return 'Sandy soil'
    if 'heavy loam' in s or 'very heavy' in s or ('heavy' in s and 'soil' in s):
        return 'Heavy soil'
    if 'clay' in s:
        return 'Clay soil'
    if 'shallow' in s:
        return 'Shallow soil'
    if 'sodic' in s:
        return 'Sodic soil'
    return soil.strip()

def normalize_root_label(root):
    s = str(root).strip().lower()
    if not s:
        return None
    if 'taproot' in s or 'tap root' in s:
        return 'Tap root system'
    if 'fibrous' in s:
        return 'Fibrous root system'
    return None

def normalize_functional_use_label(item):
    s = str(item).strip().lower()
    if not s:
        return None
    if 'quick growth' in s or 'feed substitute' in s or 'forage' in s:
        return None
    if 'nitrogen fixation' in s:
        return 'Nitrogen fixation'
    if 'nitrogen scaveng' in s or 'nutrient scaveng' in s:
        return 'Nitrogen scavenging'
    if 'erosion' in s:
        return 'Erosion control'
    if 'compaction' in s or 'soil permeability improvement' in s:
        return 'Compaction reduction'
    if 'drought tolerance' in s:
        return 'Drought tolerance'
    if 'weed' in s:
        return 'Weed suppression'
    if 'soil building' in s:
        return 'Soil building'
    if 'shade tolerance' in s:
        return 'Shade tolerance'
    if 'phosphorus recycling' in s:
        return 'Phosphorus recycling'
    if 'nutrient recycling' in s:
        return 'Nutrient recycling'
    if 'low fertility tolerance' in s:
        return 'Low fertility tolerance'
    return None

def row_has_selected_goal(raw_text, selected_goals):
    row_goals = {normalize_functional_use_label(x) for x in split_items(raw_text)}
    row_goals.discard(None)
    return any(g in row_goals for g in selected_goals)

def goal_score(row, goals):
    row_goals = {normalize_functional_use_label(x) for x in split_items(row['Functional uses'])}
    row_goals.discard(None)
    if not goals:
        return 0.5
    hits = sum(1 for g in goals if g in row_goals)
    return hits / len(goals)

def normalize_warning_label(warning):
    s = str(warning).strip().lower()
    if not s:
        return None
    if 'toxic to livestock' in s or 'poison' in s or 'anti-nutritional' in s or 'alkaloid' in s:
        return 'Toxicity risk'
    if 'bloat risk' in s or 'choking' in s or 'avoid grazing' in s or 'livestock injury' in s:
        return 'Livestock risk'
    if 'weedy' in s or 'invasive' in s:
        return 'Weedy or invasive'
    if 'difficult to terminate' in s:
        return 'Difficult to terminate'
    if 'pest host' in s or 'hosts insect pests' in s or 'mite' in s or 'cutworm' in s or 'armyworm' in s or 'nematode' in s:
        return 'Pest risk'
    if 'disease host' in s or 'disease' in s or 'foliar' in s or 'root rot' in s or 'ergot' in s or 'blight' in s:
        return 'Disease risk'
    if 'heavy metals' in s:
        return 'Heavy metal accumulation risk'
    if 'allelopathic' in s or 'phytotoxic' in s:
        return 'Residue carryover / suppression risk'
    if 'weak weed competitor' in s:
        return 'Weak weed competition'
    if 'low forage value' in s:
        return 'Low forage value'
    return warning.strip()

def extract_unique_options(series, normalizer):
    vals = set()
    for raw in series.dropna():
        for item in split_items(raw):
            norm = normalizer(item)
            if norm:
                vals.add(norm)
    return sorted(vals)

def row_has_selected_soil(raw_text, selected_soils):
    row_soils = {normalize_soil_label(x) for x in split_items(raw_text)}
    row_soils.discard(None)
    return any(s in row_soils for s in selected_soils)

def row_has_selected_warning(raw_text, selected_warnings):
    row_warnings = {normalize_warning_label(x) for x in split_items(raw_text)}
    row_warnings.discard(None)
    return any(w in row_warnings for w in selected_warnings)

def cn_match_value(avg, pref):
    if pd.isna(avg):
        return 0.0 if pref != 'Any' else 0.5
    if pref == 'Low':
        return 1.0 if avg <= 20 else 0.5 if avg <= 35 else 0.0
    if pref == 'Medium':
        return 1.0 if 20 < avg <= 40 else 0.3
    if pref == 'High':
        return 1.0 if avg > 40 else 0.4 if avg > 20 else 0.0
    return 0.5

def explain_match(row, prefs):
    reasons = []
    row_goals = {normalize_functional_use_label(x) for x in split_items(row['Functional uses'])}
    row_goals.discard(None)
    if prefs['region'] != 'Any' and row['Region of growth'] == prefs['region']:
        reasons.append(f"matches the {prefs['region'].lower()} growing region")
    if prefs['life'] != 'Any' and row['Life cycle'] == prefs['life']:
        reasons.append(f"fits the {prefs['life'].lower()} life cycle")
    for goal in prefs['goals']:
        if goal in row_goals:
            reasons.append(f"supports {goal.lower()}")
    if prefs['preferred_root'] != 'Any' and normalize_root_label(row['Root type']) == prefs['preferred_root']:
        reasons.append('matches the preferred root type')
    if prefs['preferred_structure'] != 'Any' and str(row['Plant structure']) == prefs['preferred_structure']:
        reasons.append('matches the preferred plant structure')
    if prefs['avoid_warnings']:
        reasons.append('avoids the selected warning categories')
    return ('; '.join(reasons[:3]).capitalize() + '.') if reasons else 'Matches several of the selected conditions.'

df = load_data()
soil_options = extract_unique_options(df['Prohibitive soil'], normalize_soil_label)
warning_options = extract_unique_options(df['Warnings'], normalize_warning_label)
goal_pool = extract_unique_options(df['Functional uses'], normalize_functional_use_label)

st.title("Cover Crop Recommendation Tool")
st.write("Choose the crop traits and conditions that matter to you, and the app will rank cover crops automatically using your dataset fields.")

with st.sidebar:
    st.header("User choices")
    region = st.selectbox("Region of growth", ['Any'] + sorted(df['Region of growth'].dropna().unique().tolist()))
    life = st.selectbox("Life cycle", ['Any'] + sorted(df['Life cycle'].dropna().unique().tolist()))
    avoid_soils = st.multiselect("Avoid crops prohibited by these soil conditions", soil_options)
    goals = st.multiselect("Desired functional uses", goal_pool)
    root_options = extract_unique_options(df['Root type'], normalize_root_label)
    preferred_root = st.selectbox("Preferred root type", ['Any'] + root_options)
    preferred_structure = st.selectbox("Preferred plant structure", ['Any'] + sorted(df['Plant structure'].dropna().unique().tolist()))
    protein_pref = st.selectbox("Preferred crude protein level", ['Any', 'Low', 'Medium', 'High'])
    cn_pref = st.selectbox("Preferred C:N ratio", ['Any', 'Low', 'Medium', 'High'])
    avoid_warning_choices = st.multiselect("Avoid crops with these warnings / risks", warning_options)

work = df.copy()
if region != 'Any':
    work = work[work['Region of growth'] == region]
if life != 'Any':
    work = work[work['Life cycle'] == life]
if avoid_soils:
    work = work[~work['Prohibitive soil'].apply(lambda x: row_has_selected_soil(x, avoid_soils))]
if avoid_warning_choices:
    work = work[~work['Warnings'].apply(lambda x: row_has_selected_warning(x, avoid_warning_choices))]

work['region_match'] = (work['Region of growth'] == region).astype(float) if region != 'Any' else 0.5
work['life_match'] = (work['Life cycle'] == life).astype(float) if life != 'Any' else 0.5
work['root_group'] = work['Root type'].apply(normalize_root_label)
work['root_match'] = (work['root_group'] == preferred_root).astype(float) if preferred_root != 'Any' else 0.5
work['structure_match'] = (work['Plant structure'] == preferred_structure).astype(float) if preferred_structure != 'Any' else 0.5
work['goal_match'] = work.apply(lambda row: goal_score(row, goals), axis=1)
cp_vals = pd.to_numeric(work['Crude protein avg'], errors='coerce')
if protein_pref == 'Low':
    work['protein_match'] = cp_vals.apply(lambda x: 1.0 if pd.notna(x) and x < 12 else 0.3 if pd.notna(x) and x < 20 else 0.0)
elif protein_pref == 'Medium':
    work['protein_match'] = cp_vals.apply(lambda x: 1.0 if pd.notna(x) and 12 <= x <= 20 else 0.3 if pd.notna(x) else 0.0)
elif protein_pref == 'High':
    work['protein_match'] = cp_vals.apply(lambda x: 1.0 if pd.notna(x) and x > 20 else 0.3 if pd.notna(x) and x >= 12 else 0.0)
else:
    work['protein_match'] = 0.5
work['cn_match'] = pd.to_numeric(work['C:N ratio avg'], errors='coerce').apply(lambda x: cn_match_value(x, cn_pref))
work['root_struct_match'] = (work['root_match'] + work['structure_match']) / 2
w_region, w_life, w_goal, w_root, w_protein, w_cn = 0.15, 0.10, 0.25, 0.15, 0.15, 0.20
work['Final recommendation score'] = (
    w_region * work['region_match'] +
    w_life * work['life_match'] +
    w_goal * work['goal_match'] +
    w_root * work['root_struct_match'] +
    w_protein * work['protein_match'] +
    w_cn * work['cn_match']
) * 100

prefs = {
    'region': region,
    'life': life,
    'goals': goals,
    'preferred_root': preferred_root,
    'preferred_structure': preferred_structure,
    'avoid_warnings': avoid_warning_choices,
}

work = work.sort_values('Final recommendation score', ascending=False).reset_index(drop=True)

if work.empty:
    st.warning('No crops matched the current filters. Relax one or more filters and try again.')
else:
    top = work.head(5).copy()
    top['Why recommended'] = top.apply(lambda r: explain_match(r, prefs), axis=1)
    c1, c2 = st.columns(2)
    c1.metric('Crops considered', len(work))
    c2.metric('Selected goals', len(goals))
    st.subheader('Top recommendations')
    show_cols = ['Common name', 'Scientific name', 'Final recommendation score', 'Why recommended', 'Region of growth', 'Life cycle', 'Functional uses', 'Warnings', 'Plant structure', 'Root type', 'Crude protein', 'Prohibitive soil', 'C:N ratio']
    st.dataframe(top[show_cols], use_container_width=True, hide_index=True)
    st.subheader('All scored crops')
    full_cols = ['Common name', 'Scientific name', 'Final recommendation score', 'Region of growth', 'Functional uses', 'Warnings', 'Plant structure', 'Root type', 'Crude protein', 'Prohibitive soil', 'Life cycle', 'C:N ratio']
    st.dataframe(work[full_cols], use_container_width=True, hide_index=True)
    st.caption('Common name and scientific name are shown as output fields. The recommendation ranking uses the user-selected dataset preferences in the sidebar.')
