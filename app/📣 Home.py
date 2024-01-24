from io import StringIO
from typing import Union
import folium
import pandas as pd

import requests
import streamlit as st
from streamlit_folium import st_folium
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode


st.set_page_config(layout="wide")
st.image("./data/logo/logo.png", width=300)


def get_icon_color(label: Union[bool, None]):
    if label is True:
        return "red"
    elif label is False:
        return "green"
    else:
        return "gray"


def create_map(chart_data, location=None):
    chart_data = chart_data.fillna("")
    # center map on the mean of the coordinates

    if location is not None:
        m = folium.Map(location=location, zoom_start=18)
    elif len(chart_data) > 0:
        m = folium.Map(
            location=[chart_data["latitude"].mean(), chart_data["longitude"].mean()],
            zoom_start=11,
        )
    else:
        m = folium.Map(location=[-22.917690, -43.413861], zoom_start=11)

    for _, row in chart_data.iterrows():
        icon_color = get_icon_color(row["label"])
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            # Adicionar id_camera ao tooltip
            tooltip=f"ID: {row['id_camera']}",
            # Alterar a cor do ícone de acordo com o status
            icon=folium.features.DivIcon(
                icon_size=(15, 15),
                icon_anchor=(7, 7),
                html=f'<div style="width: 20px; height: 20px; background-color: {icon_color}; border: 2px solid black; border-radius: 70%;"></div>',
            ),
        ).add_to(m)
    return m


def label_emoji(label):
    if label is True:
        return "🔴"
    elif label is False:
        return "🟢"
    else:
        return "⚫"


@st.cache_data(ttl=60)
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

    dataframe = dataframe.sort_values(by="label", ascending=True).reset_index(drop=True)

    ## get more camera information
    url = "https://docs.google.com/spreadsheets/d/122uOaPr8YdW5PTzrxSPF-FD0tgco596HqgB7WK7cHFw/edit#gid=914166579"
    request_url = url.replace("edit#gid=", "export?format=csv&gid=")
    response = requests.get(request_url)
    cameras = pd.read_csv(StringIO(response.content.decode("utf-8")), dtype=str)
    camera_cols = [
        "id_camera",
        "bairro",
        "subprefeitura",
        "id_bolsao",
        "bacia",
        "sub_bacia",
    ]

    cameras = cameras[camera_cols]
    dataframe = pd.merge(dataframe, cameras, how="left", on="id_camera")

    return dataframe, last_update


def get_table_cameras_with_images(dataframe):
    # filter only flooded cameras
    table_data = (
        dataframe[dataframe["label"].notnull()]
        .sort_values(by=["label", "id_camera"], ascending=False)
        .reset_index(drop=True)
    )
    table_data["emoji"] = table_data["label"].apply(label_emoji)

    col_order = [
        "emoji",
        "id_camera",
        "object",
        "bairro",
        "subprefeitura",
        "id_bolsao",
        "bacia",
        "sub_bacia",
        "image_url",
    ]
    table_data = table_data[col_order]

    return table_data


def get_agrid_table(data_with_image):
    # Configure AgGrid
    gb = GridOptionsBuilder.from_dataframe(data_with_image)
    gb.configure_selection("single", use_checkbox=False)
    gb.configure_side_bar()  # if you need a side bar
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)

    # configure individual columns
    gb.configure_column("id_camera", header_name="ID Camera", pinned="left")
    gb.configure_column("emoji", header_name="", pinned="left")
    gb.configure_column("object", header_name="Identificador")
    gb.configure_column("image_url", header_name="URL Imagem")
    gb.configure_column("bairro", header_name="Bairro")
    gb.configure_column("subprefeitura", header_name="Subprefeitura")
    gb.configure_column("id_bolsao", header_name="ID Bolsão")
    gb.configure_column("bacia", header_name="Bacia")
    gb.configure_column("sub_bacia", header_name="Sub Bacia")

    gb.configure_column("image_url", header_name="URL Imagem")

    gb.configure_grid_options(enableCellTextSelection=True)
    # Build grid options
    grid_options = gb.build()

    # Set auto size mode (if you still want to use it, otherwise remove this line)
    grid_response = AgGrid(
        data_with_image,
        gridOptions=grid_options,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        # update_mode=GridUpdateMode.MODEL_CHANGED | GridUpdateMode.COLUMN_RESIZED,
        # fit_columns_on_grid_load=True
        # height=400,
        # width="50%",
    )

    selected_row = grid_response["selected_rows"]
    return selected_row


chart_data, last_update = load_alagamento_detectado_ia()
data_with_image = get_table_cameras_with_images(chart_data)
folium_map = create_map(chart_data)


st.markdown("# Mapa de Alagamentos | Vision AI")
st.markdown(
    """
    Esta aplicação usa as câmeras instaladas na cidade para detectar alagamentos e bolsões de água em tempo real. 
    
    Ela usa o modelo Gemini Pro Vision para identificar alagamentos em imagens.
    """
)


st.markdown(
    f"""
    
    ----
    
    ### Status snapshots:
    - **Ultima atualização**: {str(last_update)}
    - Total: {len(chart_data)}
    - Sucessos: {len(data_with_image)}
    - Falhas:{len(chart_data) - len(data_with_image)}
    
    ----
    
    ### Tabela de Status de Alagamentos
""",
)

selected_row = get_agrid_table(data_with_image)
st.markdown("----")
st.markdown("###  Mapa de Câmeras")
st.markdown("Selecione uma Câmera na tabela visualizar no mapa.")

if selected_row:
    selected_camera_id = selected_row[0]["id_camera"]
    camera_data = chart_data[chart_data["id_camera"] == selected_camera_id]
    if not camera_data.empty:
        camera_location = [
            camera_data.iloc[0]["latitude"],
            camera_data.iloc[0]["longitude"],
        ]
        folium_map = create_map(chart_data, location=camera_location)
        map_data = st_folium(folium_map, key="fig1", height=600, width=1200)

        image_url = camera_data.iloc[0]["image_url"]
        st.markdown("----")
        st.markdown("### 📷 Câmera snapshot")
        st.markdown("Selecione uma Câmera na tabela visualizar o snapshot.")

        if image_url is None:
            st.markdown("Falha ao capturar o snapshot da câmera.")
        else:
            st.image(image_url)


else:
    map_data = st_folium(folium_map, key="fig1", height=600, width=1200)

    st.markdown("----")
    st.markdown("### 📷 Câmera snapshot")
    st.markdown("Selecione uma Câmera na tabela visualizar o snapshot.")

# select chart_data obj based on last_object_clicked coordinates
obj_coord = map_data["last_object_clicked"]


# if obj_coord is None:
#     st.write("Clique no marcador para ver mais detalhes.")
# else:
#     selected_data = chart_data[
#         (chart_data["latitude"] == obj_coord["lat"])
#         & (chart_data["longitude"] == obj_coord["lng"])
#     ]

#     image_url = selected_data["image_url"].values[0]
#     selected_data = (
#         selected_data[["id_camera", "url_camera"]]
#         .rename(
#             columns={
#                 "id_camera": "ID",
#                 "url_camera": "🎥 Feed",
#             }
#         )
#         .T
#     )

#     selected_data.columns = ["Informações"]

#     st.markdown("### 📷 Camera snapshot")
#     if image_url is None:
#         st.markdown("Falha ao capturar o snapshot da câmera.")
#     else:
#         st.image(image_url)

#     selected_data
