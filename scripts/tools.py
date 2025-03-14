import streamlit as st
state = st.session_state
import pandas as pd
import os
import re
import numpy as np
from natsort import natsorted

def init():

    # set page configuration. Can only be set once per session and must be first st command called
    try:
        st.set_page_config(page_title='HBW corpus searching', page_icon=':book:', layout='wide',initial_sidebar_state='collapsed')
    except st.errors.StreamlitAPIException as e:
        if "can only be called once per app" in e.__str__():
            return

    if "selected" not in state:
        state.selected = None

    # set any custom css
    with open(os.path.abspath('./style.css')) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# @st.cache_resource
def get_data():
    # set book metadata
    df = pd.read_csv('data/BBIP_metadata_20241231_with_wc.csv')
    if 'Unnamed: 0' in df.columns:
        df.drop(['Unnamed: 0'], inplace=True, axis=1)

    # doing a little data merging
    df['Author(s)'] = df[['Author', 'Second Author',
                'Additional Authors']].apply(
                lambda x: '; '.join(x.dropna()), axis=1)
    df['All keywords'] = df[['Literary movement',
                'Genre','LC genre','LC subjects','wc_subject','wc_genre']].apply(
                lambda x: '; '.join(x.dropna()), axis=1)
    df['All keywords'] = df['All keywords'].apply(lambda x:
        '; '.join(natsorted(set([t.title().strip().rstrip('.') for t in x.split(';')]))))
    df['All keywords'] = df['All keywords'].replace(r'^\s*$', np.nan, regex=True)

    def get_earliest_date(x):
        dates = {date for date in x if isinstance(date, str) and date.isdigit()}
        return int(min(dates)) if dates else None
    df['Date'] = df[['Date of Publication', 'Other dates', 'LC Pub Date']].apply(get_earliest_date, axis=1)

    # update default col headers
    col_map = {'wc_summary':'Summary'}
    df.rename(columns=col_map, inplace=True)

    state.inventory_full = df
    # state.inventory = df
    state.default_cols = ['Title','Author(s)','Date','BBIPID','All keywords','Summary']

    # update authority references
    state.authorities = ['Library of Congress ID','WorldCat-OCLC entry']
    state.inventory_full['Library of Congress ID'] = state.inventory_full['Library of Congress ID'].apply(lambda x: f"https://lccn.loc.gov/{x}" if not pd.isnull(x) else None)
    state.inventory_full['WorldCat-OCLC entry'] = state.inventory_full['WorldCat-OCLC entry'].str.replace(r'^[^\d]+', '', regex=True).apply(lambda x: f"https://search.worldcat.org/title/{x}" if pd.notnull(x) and x else None)

def about():
    head_cols = st.columns(2)
    with head_cols[0]:
        st.write('*Select any column header to sort the data.*')
    with head_cols[1]:
        with st.expander('About this data'):
            st.markdown("""This table contains metadata from HBW, Library of Congress, and OCLC/WorldCat. It contains the full HBW corpus as of December 31, 2024.

* **Title** - full title of the book
* **Author(s)** - all named authors of the book
* **Date** - earliest known publication date
* **BBIPID** - HBW's ID number, normally indicates the book was scanned
    * *Multiple BBIP IDs*: title was scanned more than once.
    * *No BBIP ID*: title has probably not been scanned
* **All keywords** - combined list of genres, keywords, subjects, etc. from all sources
* **Summary** - book summary taken from WorldCat
            """)

def filter_inv():

    # date filter
    if 'beg_date' not in state:
        state.beg_date = state.inventory_full['Date'].min()
    if 'end_date' not in state:
        state.end_date = state.inventory_full['Date'].max()

    t_df = state.inventory_full[(state.inventory_full['Date']>=state.beg_date) & (state.inventory_full['Date']<=state.end_date)  | (state.inventory_full['Date'].isnull())]

    # search filter
    if 'search' not in state:
        state.search = ''
    searchstring = '|'.join(state.search.split())

    # Search across all columns
    # t_df = t_df[t_df.apply(
    # lambda row: row.astype(str).str.contains(searchstring, na=False, case=False).any(), axis=1)]
    mask = t_df.apply(lambda col: col.astype(str).str.contains(searchstring, na=False, case=False))
    t_df = t_df[mask.any(axis=1)]

    state.inventory = t_df.copy()

# download csv
@st.cache_data
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

# @st.cache_resource
def display_table():

    filter_cols = st.columns((1,1,2,1,1))

    with filter_cols[0]:
        state.beg_date = st.number_input(
    "Start date", value=state.inventory_full['Date'].min(),
        format='%.0f')

    with filter_cols[1]:
        state.end_date = st.number_input(
    "End date", value=state.inventory_full['Date'].max(),
        format='%.0f')

    with filter_cols[2]:
        state.search = st.text_input('*Search all fields (not case sensitive, searches all terms)*')

    filter_inv()

    with filter_cols[4]:
        fn = f"HBW_{state.beg_date:.0f}-{state.end_date:.0f}"
        if state.search != '':
            fn += f"-{state.search.replace(' ','-')}"
        fn += '.csv'

        csv = convert_df(state.inventory[state.default_cols + state.authorities])
        st.download_button(
            "Download filtered data",
            csv,fn,"text/csv",key='download-csv')
    #
    # with filter_cols[2]:
    #     state.display40 = st.pills('*Texts to display*', ['All titles', '40 books'], default=['All titles'], key='dt', selection_mode='single')

    st.write(f"***{len(state.inventory)} titles displayed*** - ({len(state.inventory[~state.inventory['All keywords'].isnull()])} with keywords, {len(state.inventory[~state.inventory['Summary'].isnull()])} with summaries)")

    clicked = st.dataframe(state.inventory[state.default_cols].style.format({'Date': '{:.0f}'}), use_container_width=True, hide_index=True, key="display", selection_mode="single-row", on_select="rerun")

    if clicked:
        return clicked
