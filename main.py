from dotenv import load_dotenv

load_dotenv()
import os
import pandas as pd
import psycopg2
import streamlit as st
import datetime
# import matplotlib.pyplot as plt

# import requests
# backend = 'http://backend-physio.herokuapp.com/'
# data = requests.get(backend+ 'get_session_history/Kris_Dukov').json()
# df = pd.read_sql()
# df = pd.DataFrame(data)

database = os.environ.get("DATABASE")
user = os.environ.get("USER")
password = os.environ.get("PASSWORD")
host = os.environ.get("HOST")

tab1, tab2, tab3 = st.tabs(["Overview", "Detailed", "Bla Bla"])

@st.cache  # 👈 This function will be cached
def get_data():
    print("database:",database)
    con = psycopg2.connect(database=database, user=user, password=password, host=host, port="5432")
    df = pd.read_sql('select DATE(timestamp_session) as date, exercise, patient, duration, target, completed, min_angle, max_angle, ROW_NUMBER( ) OVER ( PARTITION BY DATE(timestamp_session), exercise, patient  ORDER BY timestamp_session ) as set_number from \"session\"', con=con)
    return df
# df, patients,exercises = get_data()
df_session = get_data()


# @st.cache  # 👈 This function will be cached
def get_pain():
    con = psycopg2.connect(database=database, user=user, password=password, host=host, port="5432")
    df = pd.read_sql('select DATE(timestamp_pain) as date, patient, before_pain, after_pain from \"pain\"', con=con)
    return df
df_pain = get_pain()

patients = df_session['patient'].unique()

patient_selectbox = st.sidebar.selectbox(
    'Example dropdown menu',
    patients, help= 'Ще показва само пациентите на дадения доктор')


start_date, end_date  = st.sidebar.date_input(label='rannge', value=[datetime.date.today()-datetime.timedelta(days=30),datetime.date.today()])

# filtered = df_session[(df_session['patient'].isin(patient_selection)) & (df_session['date']>=start_date)& (df_session['date']<=end_date)]
filtered = df_session[(df_session['patient'] == patient_selectbox) & (df_session['date']>=start_date)& (df_session['date']<=end_date)]


df_chart = filtered.set_index('date')
df_overview = filtered.groupby(by = ['date','patient']).agg(target = ('target','sum'), completed = ('completed','sum')).reset_index().sort_values(by = 'date')
df_overview['%'] = df_overview['completed']/df_overview['target']
df_overview = df_overview.set_index('date')

# TAB 1 Overview
tab1.write("# Overview")
expander = tab1.expander("See overview table")
expander.write(df_overview)
tab1.write("## Completion progression")
tab1.bar_chart(df_overview['%'])
tab1.write("# Pain")
expander = tab1.expander("See pain table")
filtered_pain = df_pain[(df_pain['patient'] == patient_selectbox) & (df_pain['date']>=start_date)& (df_pain['date']<=end_date)].set_index('date')
expander.write(filtered_pain)
tab1.bar_chart(filtered_pain[['before_pain', 'after_pain']])

# TAB 2 Detailed
exercise_selection = tab2.multiselect(
    'Select Exercise',
    filtered['exercise'].unique(), filtered['exercise'].unique(), help= 'Ще показва само упражненията само на този пациент')
filtered = filtered[filtered['exercise'].isin(exercise_selection)].set_index('date')
filtered['%'] = filtered['completed']/filtered['target']
expander = tab2.expander("See detailed table")
expander.write(filtered)

tab2.write("# Progress Target vs Completed")
tab2.bar_chart(filtered[['target', 'completed']])

col1, col2 = tab2.columns([1, 1])
# tab2.write("# Angle Progression")
col1.write("# Angle")
# tab2.write(f"### {exercise_selection}")
col1.write(f"### {exercise_selection}")
col1.area_chart(filtered[['min_angle', 'max_angle']])

col2.write("# Duration")
col2.write(f"### {exercise_selection}")
col2.area_chart(filtered[['duration']])

col1.write("# Reps per Set")

filtered_reps_set = filtered.groupby(by = ['date','set_number']).agg(completed = ('completed','sum')).reset_index().sort_values(by = ['date', 'set_number'])
# chart_data = pd.DataFrame(
#     np.random.rand(9, 4),
#     index=["air","coffee","orange","whitebread","potato","wine","beer","wheatbread","carrot"],
# )

# # Vertical stacked bar chart
# st.bar_chart(filtered_reps_set)

# Convert wide-form data to long-form
# See: https://altair-viz.github.io/user_guide/data.html#long-form-vs-wide-form-data
# data = pd.melt(filtered_reps_set, id_vars=['completed'])
# data
# filtered_reps_set
# Horizontal stacked bar chart

# sub_avg_breast_cancer_df = filtered[["mean radius", "mean texture", "mean perimeter", "area error"]]
# fig = filtered_reps_set.plot.bar(alpha=0.8, ax=bar_ax, title="Reps per Set")


# col1.bar_chart(filtered[['completed']])
# col1.write(filtered_reps_set)
# CHECK https://plotly.com/python/bar-charts/
col1.bar_chart(data = filtered_reps_set, x='date', y = ['completed'], )



# TAB 3
tab3.write("# Here write more detailed graphs and stuff")
tab3.area_chart(df_chart[['duration']])
