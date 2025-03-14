import streamlit as st
state = st.session_state
# from st_click_detector import click_detector as cd
import pandas as pd

# initialize
from scripts import tools
tools.init()
tools.get_data()

st.header('History of Black Writing corpus search')

tools.about()

clicked = tools.display_table()

def make_clickable(val):
    if not pd.isnull(val):
        return f'<a href="{val}">{val}</a>'
    else:
        return None

if len(clicked.selection['rows']) > 0:

    t_df = state.inventory.iloc[clicked.selection['rows']]

    for c in state.authorities:
        t_df[c] = t_df[c].apply(make_clickable)

    st.write(t_df[0:1][state.default_cols + state.authorities].T.to_html(escape=False, table_id="myTable"), unsafe_allow_html=True)

    # state.selected = state.inventory.iloc[clicked.selection['rows'][0]]
    # st.table(state.selected[state.default_cols + state.authorities].to_frame(name='Values'))
