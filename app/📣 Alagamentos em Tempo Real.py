from pathlib import Path
import folium
import pandas as pd
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

tmp_data_path = Path(__file__).parent.parent / "data" / "cameras_h3_1.csv"
chart_data = pd.read_csv(tmp_data_path)[:100]
# dropna status_right from chart_data
chart_data = chart_data.dropna(subset=["status_right"])
# remove all Unnamed columns
chart_data = chart_data.loc[:, ~chart_data.columns.str.contains("^Unnamed")]
chart_data.to_csv(index=False)

# center map on the mean of the coordinates
m = folium.Map(
    location=[chart_data["latitude"].mean(), chart_data["longitude"].mean()],
    zoom_start=11,
)

for i in range(0, len(chart_data)):
    folium.Marker(
        location=[chart_data.iloc[i]["latitude"], chart_data.iloc[i]["longitude"]],
        # add nome_da_camera and status to tooltip
        tooltip=f"""
        Status: {chart_data.iloc[i]['status']}<br>
        Endereço: {chart_data.iloc[i]['nome_da_camera']}""",
        # change icon color according to status
        icon=folium.Icon(
            color="green" if chart_data.iloc[i]["status"] == "normal" else "red"
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

    selected_data = (
        selected_data[["nome_da_camera", "bairro", "zona", "chuva_15min", "rtsp"]]
        .rename(
            columns={
                "nome_da_camera": "Endereço",
                "bairro": "Bairro",
                "zona": "Zona",
                "chuva_15min": "🌧️ Chuva 15min",
                "rtsp": "🎥 Camera",
            }
        )
        .T
    )

    selected_data.columns = ["Infos"]

    st.markdown("## 📷 Imagem da Camera")
    st.image("./data/imgs/flooded1.jpg")

    selected_data
