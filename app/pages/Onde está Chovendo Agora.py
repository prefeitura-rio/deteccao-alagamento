# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Onde está Chovendo Agora", layout="wide", initial_sidebar_state="collapsed"
)

# embed a webpage that covers all screen
st.write(f'<iframe src="https://www.dados.rio/chuvas/onde-esta-chovendo-agora" width="100%" height="920px" style="border: none; margin: 0; padding: 0;"></iframe>', unsafe_allow_html=True)
