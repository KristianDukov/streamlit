from dotenv import load_dotenv

load_dotenv()
import os
import pandas as pd
import psycopg2
import streamlit as st
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# import requests
# backend = 'http://backend-physio.herokuapp.com/'
# data = requests.get(backend+ 'get_session_history/Kris_Dukov').json()
# df = pd.read_sql()
# df = pd.DataFrame(data)

database = os.environ.get("DATABASE")
user = os.environ.get("USER")
password = os.environ.get("PASSWORD")
host = os.environ.get("HOST")

tab1, tab2 = st.tabs(["Overview", "Detailed"])

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

patients = df_session['patient'].unique()

patient_selectbox = st.sidebar.selectbox(
    'Select Patient',
    patients, help= 'Ще показва само пациентите на дадения терапевт')

# start_date, end_date  = st.sidebar.date_input(label='Time period', value=[datetime.date.today()-datetime.timedelta(days=30),datetime.date.today()])
start_date, end_date  = st.sidebar.date_input(label='Time period', value=[datetime.date(2022,1,1),datetime.date.today()])

filtered = df_session[(df_session['patient'] == patient_selectbox) & (df_session['date']>=start_date)& (df_session['date']<=end_date)]
df_chart = filtered.set_index('date')

########          TAB 1 Overview
# df_overview = filtered.groupby(by = ['date','patient']).agg(target = ('target','sum'), completed = ('completed','sum')).reset_index().sort_values(by = 'date')
filtered['%'] = filtered['completed']/filtered['target']
# df_overview = df_overview.set_index('date')


tab1.write("# Overview")
expander = tab1.expander("See overview table")
expander.write(filtered)
tab1.write("## Workout Completion Rate (Daily)")
sns.set_style('whitegrid')
g = sns.catplot(x="exercise", y= '%', col="date",
                data=filtered,
                kind="bar",height=3, aspect=1.2, palette='Set1',errorbar=None)
for ax in g.axes.flat[1:]:
    sns.despine(ax=ax, left=True)
for ax in g.axes.flat:
    ax.set_ylabel('Completion Rate')
    ax.set_xlabel(ax.get_title())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.0%}'.format(y))) 
    ax.set_title('')
    ax.margins(x=0.3) # slightly more margin as a separation
    for p in ax.patches:
        ax.text(p.get_x() + 0.2, 
                p.get_height() * 1.02, 
                '{:.0%}'.format(p.get_height()), 
                color='black', rotation='horizontal', size='large')
plt.subplots_adjust(wspace=0, bottom=0.18, left=0.06)
tab1.pyplot(g)
tab1.write("## Workout Duration (Daily)")

duration = sns.catplot(y= 'duration', col="date",
                data=filtered,
                kind="bar",height=3, aspect=1.2, palette='Set1',errorbar=None)
for ax in duration.axes.flat[1:]:
    sns.despine(ax=ax, left=True)
for ax in duration.axes.flat:
    ax.set_ylabel('Duration in seconds')
    ax.set_xlabel(ax.get_title())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{0:.0f}'.format(y))) 
    ax.set_title('')
    ax.margins(x=0.3) # slightly more margin as a separation
    for p in ax.patches:
        ax.text(p.get_x() + 0.2, 
                p.get_height() * 1.02, 
                '{0:.0f}'.format(p.get_height()), 
                color='black', rotation='horizontal', size='large')
plt.subplots_adjust(wspace=0, bottom=0.18, left=0.06)

tab1.pyplot(duration)
# tab1.bar_chart(df_overview['%'])
tab1.write("# Pain Levels (daily)")
expander = tab1.expander("See pain table")
df_pain = get_pain()
filtered_pain = df_pain[(df_pain['patient'] == patient_selectbox) & (df_pain['date']>=start_date)& (df_pain['date']<=end_date)]
expander.write(filtered_pain.set_index('date'))

df_pain = pd.melt(filtered_pain, id_vars=['date','patient'], var_name= 'pain_type', value_name='value')
pain = sns.catplot(y= 'value', col="date", x="pain_type",
                data=df_pain,
                kind="bar",height=3, aspect=1.2, palette='Set1',errorbar=None)
for ax in pain.axes.flat[1:]:
    sns.despine(ax=ax, left=True)
for ax in pain.axes.flat:
    ax.set_ylabel('Pain Levels')
    ax.set_xlabel(ax.get_title())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{0:.0f}'.format(y))) 
    ax.set_title('')
    ax.margins(x=0.3) # slightly more margin as a separation
    for p in ax.patches:
        ax.text(p.get_x() + 0.2, 
                p.get_height() * 1.02, 
                '{0:.0f}'.format(p.get_height()), 
                color='black', rotation='horizontal', size='large')
plt.subplots_adjust(wspace=0, bottom=0.18, left=0.06)
tab1.pyplot(pain)


# TAB 2 Detailed
exercise_selection = tab2.selectbox(
    'Select Exercise',
    filtered['exercise'].unique(), help= 'Ще показва само упражненията само на този пациент')
filtered = filtered[filtered['exercise']== exercise_selection]
# filtered['%'] = filtered['completed']/filtered['target']
expander = tab2.expander("See detailed table")
expander.write(filtered)

tab2.write("# Progress Target vs Completed")

df_reps_set = pd.melt(filtered, id_vars=['date', 'exercise', 'patient', 'duration', 'min_angle', 'max_angle', 'set_number', '%'], value_vars=['target', 'completed'], var_name= 'set completion', value_name='reps')

reps_set = sns.catplot(x="set_number", y= 'reps', col="date", hue = 'set completion',
                data=df_reps_set,
                kind="bar",height=3, aspect=1.2, palette='Set1',errorbar=None)
for ax in reps_set.axes.flat[1:]:
    sns.despine(ax=ax, left=True)
for ax in reps_set.axes.flat:
    ax.set_ylabel('Reps per Set')
    ax.set_xlabel(ax.get_title())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.0f}'.format(y))) 
    ax.set_title('')
    ax.margins(x=0.3) # slightly more margin as a separation
    for p in ax.patches:
        ax.text(p.get_x() + 0.2, 
                p.get_height() * 1.02, 
                '{:.0f}'.format(p.get_height()), 
                color='black', rotation='horizontal', size='large')
plt.subplots_adjust(wspace=0, bottom=0.18, left=0.06)
tab2.pyplot(reps_set)


tab2.write("# Angle Progression (daily)")
df_min_max = filtered.groupby('date').agg(min_angle = ('min_angle', 'min'), max_angle = ('max_angle', 'max')).reset_index()
df_min_max_melt = pd.melt(df_min_max, id_vars=['date'], var_name= 'Angle_type', value_name='Angle')


fig, ax = plt.subplots()
plt.figure(figsize = (10,2))
min_max = sns.lineplot(x='date', 
             y='Angle',
             hue='Angle_type', 
             palette=['b','r'],
             data=df_min_max_melt)


# plt.figure(figsize=(8, 3))
# splot = sns.barplot(x="date", y="Angle", hue="Angle_type",
#                     data=df_min_max_melt)
# for p in splot.patches:
#     splot.annotate(format(round(p.get_height()), '.0f'),
#                    (p.get_x() + p.get_width() / 2., p.get_height()),
#                    ha='center', va='center',
#                    size=10,
#                    xytext=(0, 0),
#                    textcoords='offset points')
# tab2.pyplot(splot.figure)



tab2.pyplot(min_max.figure)
tab2.write("# Alternative Angle Progression (daily)")

tab2.area_chart(df_min_max.set_index('date'))

tab2.write("# Workout Duration (daily)")

duration_set = sns.catplot(x="set_number", y= 'duration', col="date",
                data=df_reps_set,
                kind="bar",height=3, aspect=1.2, palette='Set1',errorbar=None)
for ax in duration_set.axes.flat[1:]:
    sns.despine(ax=ax, left=True)
for ax in duration_set.axes.flat:
    ax.set_ylabel('Reps per Set')
    ax.set_xlabel(ax.get_title())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.0f}'.format(y))) 
    ax.set_title('')
    ax.margins(x=0.3) # slightly more margin as a separation
    for p in ax.patches:
        ax.text(p.get_x() + 0.2, 
                p.get_height() * 1.02, 
                '{:.0f}'.format(p.get_height()), 
                color='black', rotation='horizontal', size='large')
plt.subplots_adjust(wspace=0, bottom=0.18, left=0.06)
tab2.pyplot(duration_set)