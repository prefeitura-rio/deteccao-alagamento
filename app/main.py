from pathlib import Path

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

tmp_data_path = Path(__file__).parent.parent / "data" / "cameras_h3_1.csv"
chart_data = pd.read_csv(tmp_data_path)

st.pydeck_chart(
    pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=-22.93,
            longitude=-43.41,
            zoom=9,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=chart_data,
                get_position="[longitude, latitude]",
                get_color="[200, 30, 0, 160]",
                get_radius=200,
            ),
        ],
        tooltip={
            "html": "<b>Camera:</b> {nome_da_camera}<br/><b>Status:</b> {status_right}",
            "style": {
                "backgroundColor": "steelblue",
                "color": "white",
            },
        },
    )
)
