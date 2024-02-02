# -*- coding: utf-8 -*-
# import folium
import pandas as pd
import streamlit as st
# from streamlit_folium import st_folium
from utils.utils import get_agrid_table, get_cameras, treat_data

st.set_page_config(layout="wide")
# st.image("./data/logo/logo.png", width=300)


st.markdown("# Mapa de Alagamentos | Vision AI")

# get cameras
cameras = get_cameras(use_mock_data=True, update_mock_data=False)
cameras_attr, cameras_identifications = treat_data(cameras)

col1, col2 = st.columns(2)
with col1:
    objects = cameras_identifications["object"].unique().tolist()
    objects.sort()
    # dropdown to filter by object
    object_filter = st.selectbox(
        "Filtrar por objeto",
        objects,
        index=objects.index("alert_category"),
    )


with col2:
    labels = (
        cameras_identifications[
            cameras_identifications["object"] == object_filter
        ][  # noqa
            "label"
        ]
        .dropna()
        .unique()
        .tolist()
    )
    labels_default = labels.copy()

    if object_filter == "alert_category":
        labels_default.remove("normal")
    # dropdown to select label given selected object
    label_filter = st.multiselect(
        "Filtrar por label",
        labels,
        # if object_filter return minor and major, else return all labels
        default=labels_default,
    )

# filter both dfs by object and label
cameras_attr = cameras_attr[
    cameras_attr.index.isin(
        cameras_identifications[
            cameras_identifications["object"] == object_filter
        ].index
    )
]

cameras_identifications = cameras_identifications[
    (cameras_identifications["object"] == object_filter)
    & (cameras_identifications["label"].isin(label_filter))
]


# show cameras dfs
merged_df = pd.merge(cameras_attr, cameras_identifications, on="id")
merged_df = merged_df[
    ["timestamp", "object", "label", "label_explanation"]
].sort_values(by=["timestamp", "label"])

# timestamp to datetime BRL+3 with no tz
merged_df["timestamp"] = pd.to_datetime(merged_df["timestamp"]).dt.tz_convert(
    "America/Sao_Paulo"
)
# make two cols
col1, col2 = st.columns(2)

with col1:
    selected_row = get_agrid_table(merged_df.reset_index())

with col2:
    if selected_row:
        st.markdown("### 📷 Camera snapshot")
        # get cameras_attr url from selected row by id
        image_url = cameras_attr.loc[selected_row[0]["id"]]["snapshot_url"]
        if image_url is None:
            st.markdown("Falha ao capturar o snapshot da câmera.")
        else:
            st.image(image_url)


# st.markdown(
#     f"""

#     ----

#     ### Status snapshots:
#     - **Ultima atualização**: {str(last_update)}
#     - Total: {len(chart_data)}
#     - Sucessos: {len(data_with_image)}
#     - Falhas:{len(chart_data) - len(data_with_image)}

#     ----

#     ### Tabela de Status de Alagamentos
# """,
# )

# selected_row = get_agrid_table(data_with_image)
# st.markdown("----")
# st.markdown("###  Mapa de Câmeras")
# st.markdown("Selecione uma Câmera na tabela visualizar no mapa.")

# if selected_row:
#     selected_camera_id = selected_row[0]["id_camera"]
#     camera_data = chart_data[chart_data["id_camera"] == selected_camera_id]
#     if not camera_data.empty:
#         camera_location = [
#             camera_data.iloc[0]["latitude"],
#             camera_data.iloc[0]["longitude"],
#         ]
#         folium_map = create_map(chart_data, location=camera_location)
#         map_data = st_folium(folium_map, key="fig1", height=600, width=1200)

#         image_url = camera_data.iloc[0]["image_url"]
#         st.markdown("----")
#         st.markdown("### 📷 Câmera snapshot")
#         st.markdown("Selecione uma Câmera na tabela visualizar o snapshot.")

#         if image_url is None:
#             st.markdown("Falha ao capturar o snapshot da câmera.")
#         else:
#             st.image(image_url)


# else:
#     map_data = st_folium(folium_map, key="fig1", height=600, width=1200)

#     st.markdown("----")
#     st.markdown("### 📷 Câmera snapshot")
#     st.markdown("Selecione uma Câmera na tabela visualizar o snapshot.")

# # select chart_data obj based on last_object_clicked coordinates
# obj_coord = map_data["last_object_clicked"]


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

# selected_data
