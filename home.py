import streamlit as st
state = st.session_state
from st_click_detector import click_detector as cd
import pandas as pd

# initialize
from scripts import tools
tools.init()
tools.get_data()

st.header('History of Black Writing corpus search')

tools.about()

clicked = tools.display_table()

if len(clicked.selection['rows']) > 0:
    state.selected = state.inventory_full.iloc[clicked.selection['rows'][0]]

    st.table(state.selected[state.default_cols].to_frame(name='Values'))
