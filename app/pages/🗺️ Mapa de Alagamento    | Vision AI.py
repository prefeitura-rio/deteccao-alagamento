import datetime
from typing import Union
import folium
import pandas as pd

import requests
import streamlit as st
from streamlit_folium import st_folium


st.set_page_config(layout="wide", page_title="Experimente o Modelo")
st.image("./data/logo/logo.png", width=300)


def get_icon_color(label: Union[bool, None]):
    if label:
        return "red"
    elif label is None:
        return "gray"
    else:
        return "green"


def create_map(chart_data):
    chart_data = chart_data.fillna("")
    # center map on the mean of the coordinates
    if len(chart_data) > 0:
        m = folium.Map(
            location=[chart_data["latitude"].mean(), chart_data["longitude"].mean()],
            zoom_start=11,
        )
    else:
        m = folium.Map(location=[-22.917690, -43.413861], zoom_start=11)

    for i in range(0, len(chart_data)):
        ai_classification = chart_data.iloc[i].get("ai_classification", [])
        if ai_classification == []:
            ai_classification = [{"label": None}]
        folium.Marker(
            location=[chart_data.iloc[i]["latitude"], chart_data.iloc[i]["longitude"]],
            # add nome_da_camera and status to tooltip
            tooltip=f"""
            ID: {chart_data.iloc[i]['id_camera']}""",
            # change icon color according to status
            icon=folium.features.DivIcon(
                icon_size=(15, 15),
                icon_anchor=(7, 7),
                html=f'<div style="width: 20px; height: 20px; background-color: {get_icon_color(ai_classification[0].get("label", None))}; border: 2px solid black; border-radius: 70%;"></div>',
            ),
        ).add_to(m)

    return m


@st.cache_data
def load_alagamento_detectado_ia():
    raw_api_data = requests.get(
        "https://api.dados.rio/v2/clima_alagamento/alagamento_detectado_ia/"
    ).json()
    last_update = pd.to_datetime(
        requests.get(
            "https://api.dados.rio/v2/clima_alagamento/ultima_atualizacao_alagamento_detectado_ia/"
        ).text.strip('"')
    )

    return pd.DataFrame(raw_api_data), last_update


chart_data, last_update = load_alagamento_detectado_ia()

folium_map = create_map(chart_data)

## front

st.markdown("# Mapa de Alagamentos | Vision AI")

st.markdown(
    f"""
    **Last update**: {str(last_update)}
""",
)

map_data = st_folium(folium_map, key="fig1", height=600, width=1200)

# select chart_data obj based on last_object_clicked coordinates
obj_coord = map_data["last_object_clicked"]


if obj_coord is None:
    st.write("Click on a marker to view the details")
else:
    selected_data = chart_data[
        (chart_data["latitude"] == obj_coord["lat"])
        & (chart_data["longitude"] == obj_coord["lng"])
    ]

    image_url = selected_data["image_url"].values[0]
    selected_data = (
        selected_data[["id_camera", "url_camera"]]
        .rename(
            columns={
                "id_camera": "ID",
                "url_camera": "🎥 Feed",
            }
        )
        .T
    )

    selected_data.columns = ["Informations"]

    st.markdown("### 📷 Camera snapshot")
    if image_url is None:
        st.markdown("Failed to get snapshot from the camera.")
    else:
        st.image(image_url)

    selected_data
