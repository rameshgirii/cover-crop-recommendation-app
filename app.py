import streamlit as st
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="Cover Crop Selector", page_icon="🌱", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("scored_cover_crops.csv")

def explain_match(row, prefs):
    reasons=[]
    fu=str(row['Functional uses']).lower()
    rw=str(row['Warnings']).lower()
    if prefs['region']!='Any' and row['Region of growth']==prefs['region']:
        reasons.append(f"matches the {prefs['region'].lower()} growing region")
    if prefs['life']!='Any' and row['Life cycle']==prefs['life']:
        reasons.append(f"fits the {prefs['life'].lower()} life cycle preference")
    for goal in prefs['goals']:
        if goal.lower() in fu:
            reasons.append(f"supports {goal.lower()}")
    if prefs['avoid_risk'] and not any(w in rw for w in ['toxic','poison','bloat','invasive']):
        reasons.append('has relatively fewer severe warning flags')
    return ('; '.join(reasons[:3]).capitalize() + '.') if reasons else 'Matches several of the selected conditions.'

df=load_data()
st.title("🌱 Cover Crop Recommendation Tool")
st.write("This prototype uses all 11 fixed dataset parameters through filters, weighted preferences, and transparent result profiles.")

with st.sidebar:
    st.header("User choices")
    region=st.selectbox("Region of growth", ['Any'] + sorted(df['Region of growth'].dropna().unique().tolist()))
    life=st.selectbox("Life cycle", ['Any'] + sorted(df['Life cycle'].dropna().unique().tolist()))
    soil_options=sorted(df['Prohibitive soil'].dropna().unique().tolist())
    avoid_soils=st.multiselect("Avoid crops prohibited by these soil conditions", soil_options)
    goal_pool=['Nitrogen fixation','Nitrogen scavenging','Drought tolerance','Soil erosion reduction','Weed suppression','Compaction reduction','Shade tolerance','Soil building','Phosphorus recycling','Nutrient recycling','Goat feed substitute']
    goals=st.multiselect("Desired functional uses", goal_pool, default=['Nitrogen fixation','Soil erosion reduction'])
    preferred_root=st.selectbox("Preferred root type", ['Any'] + sorted(df['Root type'].dropna().unique().tolist()))
    preferred_structure=st.selectbox("Preferred plant structure", ['Any'] + sorted(df['Plant structure'].dropna().unique().tolist()))
    min_cp=st.slider("Minimum crude protein average", 0.0, 40.0, 10.0, 0.5)
    cn_pref=st.selectbox("Preferred C:N ratio", ['Any','Low','Medium','High'])
    avoid_risk=st.checkbox("Avoid higher-risk warnings when possible", value=True)
    st.subheader("Importance weights")
    w_goal=st.slider("Functional use match", 0.0, 5.0, 4.0, 0.5)
    w_root=st.slider("Root and structure match", 0.0, 5.0, 2.0, 0.5)
    w_cp=st.slider("Crude protein", 0.0, 5.0, 2.0, 0.5)
    w_cn=st.slider("C:N ratio", 0.0, 5.0, 2.0, 0.5)
    w_risk=st.slider("Low-risk preference", 0.0, 5.0, 3.0, 0.5)

work=df.copy()
if region!='Any':
    work=work[work['Region of growth']==region]
if life!='Any':
    work=work[work['Life cycle']==life]
if avoid_soils:
    work=work[~work['Prohibitive soil'].isin(avoid_soils)]
work['root_match']=(work['Root type']==preferred_root).astype(float) if preferred_root!='Any' else 0.5
work['structure_match']=(work['Plant structure']==preferred_structure).astype(float) if preferred_structure!='Any' else 0.5

def goal_score(row):
    txt=str(row['Functional uses']).lower()
    if not goals:
        return 0.5
    hits=sum(1 for g in goals if g.lower() in txt)
    return hits/len(goals)

work['goal_match']=work.apply(goal_score, axis=1)
work['cp_norm']=(pd.to_numeric(work['Crude protein avg'], errors='coerce').fillna(0).clip(lower=min_cp)-min_cp)
if work['cp_norm'].max()>0:
    work['cp_norm']=work['cp_norm']/work['cp_norm'].max()
cn_vals=pd.to_numeric(work['C:N ratio avg'], errors='coerce').fillna(np.nan)
if cn_pref=='Low':
    work['cn_match']=np.where(cn_vals.notna(), np.where(cn_vals<=20,1.0,np.where(cn_vals<=35,0.5,0.0)),0.0)
elif cn_pref=='Medium':
    work['cn_match']=np.where(cn_vals.notna(), np.where((cn_vals>20)&(cn_vals<=40),1.0,0.3),0.0)
elif cn_pref=='High':
    work['cn_match']=np.where(cn_vals.notna(), np.where(cn_vals>40,1.0,np.where(cn_vals>20,0.4,0.0)),0.0)
else:
    work['cn_match']=0.5
risk_raw=pd.to_numeric(work['Risk factor score'], errors='coerce').fillna(3)
work['risk_match']=(6-risk_raw)/5 if avoid_risk else 0.5
work['root_struct_match']=(work['root_match']+work['structure_match'])/2
weight_sum=max(w_goal+w_root+w_cp+w_cn+w_risk,0.0001)
work['Final recommendation score']=(w_goal*work['goal_match']+w_root*work['root_struct_match']+w_cp*work['cp_norm']+w_cn*work['cn_match']+w_risk*work['risk_match'])/weight_sum*100
prefs={'region':region,'life':life,'goals':goals,'avoid_risk':avoid_risk}
work=work.sort_values('Final recommendation score', ascending=False).reset_index(drop=True)

if work.empty:
    st.warning('No crops matched the current hard filters. Relax one or more filters and try again.')
else:
    top=work.head(5).copy()
    top['Why recommended']=top.apply(lambda r: explain_match(r, prefs), axis=1)
    c1,c2,c3=st.columns(3)
    c1.metric('Crops considered', len(work))
    c2.metric('Top score', f"{work['Final recommendation score'].max():.1f}")
    c3.metric('Selected goals', len(goals))
    st.subheader('Top recommendations')
    show_cols=['Common name','Scientific name','Final recommendation score','Why recommended','Region of growth','Life cycle','Functional uses','Warnings','Plant structure','Root type','Crude protein','Prohibitive soil','C:N ratio']
    st.dataframe(top[show_cols], use_container_width=True, hide_index=True)
    st.subheader('All scored crops')
    full_cols=['Common name','Scientific name','Final recommendation score','Region of growth','Functional uses','Warnings','Plant structure','Root type','Crude protein','Prohibitive soil','Life cycle','C:N ratio']
    st.dataframe(work[full_cols], use_container_width=True, hide_index=True)
    st.subheader('Derived trait score view')
    trait_cols=['Common name','Nitrogen fixation score','Erosion control score','Weed suppression score','Drought tolerance score','Compaction reduction score','Forage value score','Root depth score','Soil adaptability score','Risk factor score']
    st.dataframe(work[trait_cols], use_container_width=True, hide_index=True)
    st.caption('All 11 fixed parameters are reflected in the interface and result profiles. Some fields act as filters, some as weighted preferences, and all remain visible for transparency.')
