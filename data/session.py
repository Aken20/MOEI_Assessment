"""
data/session.py
Shared data loader — all pages import from here so 
Streamlit cache is shared across pages (single load).
"""

import streamlit as st
from data.loader import load_all
from data.metrics import build_employee_master

@st.cache_data(ttl=3600, show_spinner=False)
def get_master():
    sheets = load_all()
    return build_employee_master(
        emp_df=sheets["employees"],
        perf_df=sheets["performance"],
        train_df=sheets["training"],
        move_df=sheets["movement"],
        leave_df=sheets["leave"],
    )

@st.cache_data(ttl=3600, show_spinner=False)
def get_raw_sheets():
    return load_all()