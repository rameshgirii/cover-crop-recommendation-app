Cover Crop Recommendation Tool

Project overview
This project is a web-based decision support tool for cover crop selection. It helps users filter and rank cover crops based on selected agronomic preferences from a structured dataset. The app is designed as a Streamlit prototype for the ISAN 5357 term project and uses cover crop trait data to produce practical recommendations. [file:72][file:214][file:215]

Included files
- app.py: Streamlit application.
- scored_cover_crops.csv: dataset used by the app.
- requirements.txt: Python package requirements.
- run_app.sh: helper script to start the app.

Dataset fields used
The recommendation logic is based on these dataset fields:
- Common name
- Scientific name
- Region of growth
- Functional uses
- Warnings / negative effects
- Plant structure
- Root type
- Crude protein
- Prohibitive soil
- Life cycle
- C:N ratio [file:214][file:215]

Current app behavior
The updated app reflects the latest design choices:
- Removes user-controlled importance weight sliders.
- Uses fixed internal scoring weights.
- Keeps Common name and Scientific name as output fields rather than user filters.
- Lets users avoid prohibitive soil conditions using cleaned and grouped soil categories.
- Lets users avoid warning or risk categories using a warning/risk multiselect.
- Omits High boron from the visible soil filter options.
- Ranks crops automatically based on selected preferences. [file:214][file:215]

Main user inputs
Users can choose:
- Region of growth
- Life cycle
- Soil conditions to avoid
- Desired functional uses
- Preferred root type
- Preferred plant structure
- Minimum crude protein average
- Preferred C:N ratio
- Warning / risk categories to avoid [file:214][file:215]

How to run
Option 1:
1. Install dependencies:
   pip install -r requirements.txt
2. Start the app:
   streamlit run app.py

Option 2:
1. Make the script executable if needed:
   chmod +x run_app.sh
2. Start the app:
   ./run_app.sh

Expected output
The app returns ranked cover crop recommendations, including crop names, scientific names, recommendation scores, and supporting trait details. This aligns with the project goal of helping users enter crop preferences and receive ranked recommendations through a practical web interface. [file:72][file:214][file:215]
