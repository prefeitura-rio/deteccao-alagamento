import base64
from datetime import datetime
import io
from typing import Union

import folium
import pandas as pd
from PIL import Image
import requests
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(layout="wide", page_title="Alagamentos em Tempo Real")

st.image("./data/logo/logo.png", width=300)

st.markdown("# Alagamentos em Tempo Real usando IA")
st.markdown(
    """Esta aplicação usa as câmeras instaladas na cidade para detectar alagamentos e 
    bolsões de água em tempo real. A AI é ativada automaticamente nas regiões que 
    estão chovendo segundo os pluviômetros da cidade. Ela usa o modelo GPT-4 Vision para
    identificar alagamentos em imagens."""
)


def generate_image(image_b64: str) -> Image:
    """Generate image from base64 string"""
    image_bytes = base64.b64decode(image_b64)
    image = Image.open(io.BytesIO(image_bytes))
    return image


if "error" not in st.session_state:
    st.session_state["error"] = False

try:
    raw_api_data = requests.get(
        "https://api.dados.rio/v2/clima_alagamento/alagamento_detectado_ia/"
    ).json()
    # raw_api_data = [
    #     {
    #         "datetime": "2023-11-14 19:01:26",
    #         "id_camera": "001",
    #         "url_camera": "rtsp://url:port",
    #         "latitude": -22.881833,
    #         "longitude": -43.371461,
    #         "image_base64": base64.b64encode(
    #             open("./data/imgs/flooded2.jpg", "rb").read()
    #         ).decode("utf-8"),
    #         "ai_classification": [
    #             {
    #                 "object": "alagamento",
    #                 "label": True,
    #                 "confidence": 0.7,
    #             },
    #         ],
    #     },
    #     {
    #         "datetime": "2023-11-14 19:01:26",
    #         "id_camera": "001",
    #         "url_camera": "rtsp://url:port",
    #         "latitude": -22.882833,
    #         "longitude": -43.371461,
    #         "image_base64": base64.b64encode(
    #             open("./data/imgs/flooded2.jpg", "rb").read()
    #         ).decode("utf-8"),
    #         "ai_classification": [
    #             {
    #                 "object": "alagamento",
    #                 "label": False,
    #                 "confidence": 0.7,
    #             },
    #         ],
    #     },
    #     {
    #         "datetime": "2023-11-14 19:01:26",
    #         "id_camera": "001",
    #         "url_camera": "rtsp://url:port",
    #         "latitude": -22.881833,
    #         "longitude": -43.372461,
    #         "image_base64": base64.b64encode(
    #             open("./data/imgs/flooded2.jpg", "rb").read()
    #         ).decode("utf-8"),
    #         "ai_classification": [
    #             {
    #                 "object": "alagamento",
    #                 "label": None,
    #                 "confidence": 0.7,
    #             },
    #         ],
    #     },
    #     {
    #         "datetime": "2023-11-14 19:01:26",
    #         "id_camera": "001",
    #         "url_camera": "rtsp://url:port",
    #         "latitude": -22.882833,
    #         "longitude": -43.372461,
    #         "image_base64": None,
    #         "ai_classification": [
    #             {
    #                 "object": "alagamento",
    #                 "label": None,
    #                 "confidence": 0.7,
    #             },
    #         ],
    #     },
    # ]
    last_update = requests.get(
        "https://api.dados.rio/v2/clima_alagamento/ultima_atualizacao_alagamento_detectado_ia/"
    ).text.strip('"')
    st.session_state["error"] = False
except Exception as exc:
    raw_api_data = []
    last_update = ""
    st.session_state["error"] = True

st.markdown(
    f"""
    **Conexão com API**: {"✅" if not st.session_state["error"] else "❌"}

    **Última atualização**: {datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")}
""",
)

chart_data = pd.DataFrame(raw_api_data)

# center map on the mean of the coordinates
if len(chart_data) > 0:
    m = folium.Map(
        location=[chart_data["latitude"].mean(), chart_data["longitude"].mean()],
        zoom_start=11,
    )
else:
    m = folium.Map(location=[-22.917690, -43.413861], zoom_start=11)


def get_icon_color(label: Union[bool, None]):
    if label:
        return "orange"
    elif label is None:
        return "gray"
    else:
        return "green"


for i in range(0, len(chart_data)):
    folium.Marker(
        location=[chart_data.iloc[i]["latitude"], chart_data.iloc[i]["longitude"]],
        # add nome_da_camera and status to tooltip
        tooltip=f"""
        ID: {chart_data.iloc[i]['id_camera']}""",
        # change icon color according to status
        icon=folium.Icon(
            color=get_icon_color(chart_data.iloc[i]["ai_classification"][0]["label"])
        ),
        # icon=folium.CustomIcon(
        #     icon_data["url"],
        #     icon_size=(icon_data["width"], icon_data["height"]),
        #     icon_anchor=(icon_data["width"] / 2, icon_data["height"]),
        # ),
    ).add_to(m)


map_data = st_folium(m, key="fig1", height=600, width=1200)

# select chart_data obj based on last_object_clicked coordinates
obj_coord = map_data["last_object_clicked"]


if obj_coord is None:
    st.write("Clique em um marcador para ver os detalhes")
else:
    selected_data = chart_data[
        (chart_data["latitude"] == obj_coord["lat"])
        & (chart_data["longitude"] == obj_coord["lng"])
    ]

    image_b64 = selected_data["image_base64"].values[0]

    selected_data = (
        selected_data[["id_camera", "url_camera"]]
        .rename(
            columns={
                "id_camera": "Identificador",
                "url_camera": "🎥 Camera",
            }
        )
        .T
    )

    selected_data.columns = ["Infos"]

    st.markdown("### 📷 Imagem da Câmera")
    if image_b64 is None:
        st.markdown("Não foi possível acessar a câmera.")
    else:
        st.image(generate_image(image_b64))

    selected_data
