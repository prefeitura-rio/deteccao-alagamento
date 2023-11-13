from pathlib import Path

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

ICON_URL = "https://cdn-icons-png.flaticon.com/512/2060/2060364.png"
icon_data = {
    # Icon from Wikimedia, used the Creative Commons Attribution-Share Alike 3.0
    # Unported, 2.5 Generic, 2.0 Generic and 1.0 Generic licenses
    "url": ICON_URL,
    "width": 242,
    "height": 242,
    "anchorY": 242,
}

tmp_data_path = Path(__file__).parent.parent / "data" / "cameras_h3_1.csv"
chart_data = pd.read_csv(tmp_data_path)
chart_data["icon_data"] = None
for i in chart_data.index:
    chart_data["icon_data"][i] = icon_data

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
                "IconLayer",
                data=chart_data,
                get_icon="icon_data",
                get_position="[longitude, latitude]",
                get_size=4,
                size_scale=5,
                pickable=True,
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
