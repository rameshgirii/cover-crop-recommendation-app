Cover Crop Recommendation Tool

Files in this package:
- app.py
- cover_crop_recommendation_notebook.ipynb
- cover_crop_scoring_model_table.csv
- README.txt

Purpose:
This project is a Python-based web decision support tool for cover crop selection.
It uses a structured dataset and a recommendation model to rank cover crops based
on user priorities such as nitrogen fixation, weed suppression, erosion control,
and growing region.

How to run the web app:
1. Open a terminal or command prompt.
2. Go to the folder that contains app.py and cover_crop_scoring_model_table.csv.
3. Install Streamlit if needed:
   pip install streamlit pandas
4. Run the app:
   streamlit run app.py
5. Open the local URL shown in the terminal, usually:
   http://localhost:8501

How to open the notebook:
1. Make sure Jupyter Notebook or JupyterLab is installed.
2. In the same folder, run:
   jupyter notebook
   or
   jupyter lab
3. Open cover_crop_recommendation_notebook.ipynb.

Important note:
Keep app.py and cover_crop_scoring_model_table.csv in the same folder so the app
can read the dataset correctly.

Course context:
This project supports the ISAN 5357 term project requirement for a Python-based
application or model with a data file and notebook deliverable.
