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

import requests
backend = 'http://backend-physio.herokuapp.com/'


tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Detailed", "Конфигуратор", "Update program"])


enable_dashboard = tab1.checkbox('Enable Dashboard')

if enable_dashboard:
    database = os.environ.get("DATABASE")
    user = os.environ.get("USER")
    password = os.environ.get("PASSWORD")
    host = os.environ.get("HOST")



    @st.cache  # 👈 This function will be cached
    def get_data():
        con = psycopg2.connect(database=database, user=user, password=password, host=host, port="5432")
        df = pd.read_sql('select DATE(timestamp_session) as date, exercise, patient, duration, target, completed, min_angle, max_angle, ROW_NUMBER( ) OVER ( PARTITION BY DATE(timestamp_session), exercise, patient  ORDER BY timestamp_session ) as set_number from \"session\"', con=con)
        return df
    df_session = get_data()

    # @st.cache  # 👈 This function will be cached
    def get_pain():
        con = psycopg2.connect(database=database, user=user, password=password, host=host, port="5432")
        df = pd.read_sql('select DATE(timestamp_pain) as date, patient, before_pain, after_pain from \"pain\"', con=con)
        return df

    # @st.cache  # 👈 This function will be cached
    def get_program():
        con = psycopg2.connect(database=database, user=user, password=password, host=host, port="5432")
        df = pd.read_sql("SELECT patient, program_json FROM programs WHERE patient = 'Kris Dukov'", con=con)
        # print(df['program_json'])
        return df['program_json'][0]

    patients = df_session['patient'].unique()

    patient_selectbox = st.sidebar.selectbox(
        'Select Patient',
        patients, help= 'Ще показва само пациентите на дадения терапевт')

    start_date, end_date  = st.sidebar.date_input(label='Time period', value=[datetime.date(2022,1,1),datetime.date.today()])

    filtered = df_session[(df_session['patient'] == patient_selectbox) & (df_session['date']>=start_date)& (df_session['date']<=end_date)]
    df_chart = filtered.set_index('date')

    ########          TAB 1 Overview

    filtered['%'] = filtered['completed']/filtered['target']

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


# # TAB 2 Detailed
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


# TAB 3 CONFIGURATOR
tab3.write('Използвайте за да добавите програма за нов пациент или да добавите упражнение на съществуващ пациент')
patient = tab3.text_input("Patient's name", help = 'Името на пациента')

tuple_exercises = ('balance_left','balance_vstrani','legnal_ruce','legnal_ruce2','legnal_ruce3','legnal_ruce4','legnal_kraka','legnal_kraka2','koremna_presa','legnal_ruceikraka','sednal_ruce','sednal_ruceikraka','sednal_ruceikraka2','sednal_prav','preden_klek','preden_klek2')
exercise_selection = tab3.selectbox(
    'Select Exercise',
    tuple_exercises, help = 'Изберете упражнение за модификация')
current_program_json = requests.get(backend+ f'programs_postgr/{exercise_selection}').json()

reps_count = tab3.slider('Select Number of Reps?', 0, 20, 10)
rest_count = tab3.slider('Select Rest time?', 10, 20, 60, step=5)
tab3.write('## Show Exercise config')
current_program_json['reps'] = reps_count
current_program_json['rest_time'] = rest_count


# Clear session state
# for key in st.session_state:
#     del st.session_state[key]

if 'full_program' not in st.session_state:
    st.session_state['button_enable'] = True


if tab3.button("Add Exercise"):
    tab3.success('Added the exercise successfully', icon="✅")

    if 'full_program' not in st.session_state:
        st.session_state['full_program'] = []
        st.session_state['button_enable'] = False

    # program_json_full = [{"test": "test"}, current_program_json]
    st.session_state['full_program'].append(current_program_json)
    st.json(st.session_state['full_program'],expanded=False)

if tab3.button("Delete Exercise", disabled=st.session_state['button_enable']):
    tab3.error('Program removed')
    st.session_state['full_program'] = st.session_state['full_program'][:-1]
    st.json(st.session_state['full_program'],expanded=False)


if tab3.button("Save Program", disabled=st.session_state['button_enable']):
    tab3.success('Program saved', icon="✅")
    full_program_json = {'patient': patient, 'program_json': st.session_state['full_program']}
    post_request = requests.post(backend + 'insert_programs_postgr', json = full_program_json)
    for key in st.session_state:
        del st.session_state[key]

# Tab 4 Update program
tab4.write('Използвайте само за да промените стойност от съществуваща програма или да премахнете упражнение')
patient_update = tab4.text_input("Добавете името на пациента", help = 'Името на пациента', value = 'Kris Dukov')

current_program_json_update = requests.get(backend+ f'programs_postgr/{patient_update}').json()
list_exercises = []
mapping = {}
for exercise in current_program_json_update:
    list_exercises.append(exercise['name'])
    mapping[exercise['name']]= current_program_json_update.index(exercise)

modifiable_exersise = tab4.selectbox(
    'Изберете упражнение',list_exercises)

reps_count = tab4.slider('Select Number of Reps?', 0, 20, current_program_json_update[mapping[modifiable_exersise]]['reps'], key=123)
rest_count = tab4.slider('Select Rest time?', 10, 60, current_program_json_update[mapping[modifiable_exersise]]['rest_time'], step=5, key = 1234)
current_program_json_update[mapping[modifiable_exersise]]['reps'] = reps_count
current_program_json_update[mapping[modifiable_exersise]]['rest_time'] = rest_count
tab4.json(current_program_json_update, expanded=False)

if tab4.button("Update Program"):
    full_program_json_update = {'patient': patient_update, 'program_json': current_program_json_update}
    post_request = requests.post(backend + 'update_programs_postgr', json = full_program_json_update)
    tab4.success('Program saved', icon="✅")

if tab4.button("Delete Exercise", key=221):
    del current_program_json_update[mapping[modifiable_exersise]]
    tab4.error('Program removed')
