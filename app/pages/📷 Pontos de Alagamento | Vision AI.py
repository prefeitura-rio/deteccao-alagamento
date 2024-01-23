import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide", page_title="Experimente o Modelo")
st.image("./data/logo/logo.png", width=300)

st.markdown("# Pontos de Alagamento | Vision AI")


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

    dataframe = pd.json_normalize(
        raw_api_data,
        record_path="ai_classification",
        meta=[
            "datetime",
            "id_camera",
            "url_camera",
            "latitude",
            "longitude",
            "image_url",
        ],
    )

    # filter only flooded cameras
    dataframe = dataframe[dataframe["label"] == True]

    return dataframe, last_update


chart_data, last_update = load_alagamento_detectado_ia()
