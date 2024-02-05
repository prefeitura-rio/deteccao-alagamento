# -*- coding: utf-8 -*-
import json  # noqa
import os
from typing import Union

import folium
import pandas as pd
import streamlit as st
from st_aggrid import (AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder,
                       GridUpdateMode)
from utils.api import APIVisionAI

vision_api = APIVisionAI(
    username=os.environ.get("VISION_API_USERNAME"),
    password=os.environ.get("VISION_API_PASSWORD"),
)


@st.cache_data(ttl=60 * 2, persist=False)
def get_cameras(
    only_active=True,
    use_mock_data=False,
    update_mock_data=False,
    page_size=100,
    timeout=120,
):
    mock_data_path = "./data/temp/mock_api_data.json"

    if use_mock_data:
        with open(mock_data_path) as f:
            data = json.load(f)
        return data
    if only_active:
        cameras_ativas = vision_api._get_all_pages(
            "/agents/89173394-ee85-4613-8d2b-b0f860c26b0f/cameras"
        )
        cameras_ativas_ids = [f"/cameras/{d.get('id')}" for d in cameras_ativas]  # noqa
        data = vision_api._get_all_pages(cameras_ativas_ids, timeout=timeout)
    else:
        data = vision_api._get_all_pages(
            path="/cameras", page_size=page_size, timeout=timeout
        )

    if update_mock_data:
        with open(mock_data_path, "w") as f:
            json.dump(data, f)

    return data


def treat_data(response):
    cameras_aux = pd.read_csv("./data/database/cameras_aux.csv", dtype=str)
    cameras_aux = cameras_aux.rename(columns={"id_camera": "id"}).set_index(
        "id"
    )  # noqa
    # To dataframe
    cameras = pd.DataFrame(response).set_index("id")
    cameras = cameras[cameras["identifications"].apply(lambda x: len(x) > 0)]
    cameras["snapshot_timestamp"] = pd.to_datetime(
        cameras["snapshot_timestamp"]
    ).dt.tz_convert("America/Sao_Paulo")
    cameras = cameras.sort_values(by=["snapshot_timestamp"])
    cameras = cameras.merge(cameras_aux, on="id", how="left")
    cameras_attr = cameras[
        [
            "bairro",
            "subprefeitura",
            "name",
            # "rtsp_url",
            # "update_interval",
            "latitude",
            "longitude",
            "snapshot_url",
            "snapshot_timestamp",
            # "id_h3",
            # "id_bolsao",
            # "bolsao_latitude",
            # "bolsao_longitude",
            # "bolsao_classe_atual",
            # "bacia",
            # "sub_bacia",
            # "geometry_bolsao_buffer_0.002",
        ]
    ]
    exploded_df = cameras.explode("identifications")
    cameras_identifications = pd.DataFrame(
        exploded_df["identifications"].tolist(), index=exploded_df.index
    )

    cameras_identifications["timestamp"] = pd.to_datetime(
        cameras_identifications["timestamp"]
    ).dt.tz_convert("America/Sao_Paulo")
    cameras_identifications = cameras_identifications.sort_values(
        ["timestamp", "label"], ascending=False
    )

    return cameras_attr, cameras_identifications


def get_filted_cameras_objects(
    cameras_attr, cameras_identifications, object_filter, label_filter
):
    # filter both dfs by object and label
    cameras_filter = cameras_attr[
        cameras_attr.index.isin(
            cameras_identifications[
                cameras_identifications["object"] == object_filter
            ].index
        )
    ]

    cameras_identifications_filter = cameras_identifications[
        (cameras_identifications["object"] == object_filter)
        & (cameras_identifications["label"].isin(label_filter))
    ]

    # show cameras dfs
    cameras_identifications_merged = pd.merge(
        cameras_filter, cameras_identifications_filter, on="id"
    )
    cameras_identifications_merged = cameras_identifications_merged.sort_values(  # noqa
        by=["timestamp", "label"], ascending=False
    )

    return (
        cameras_identifications_merged,
        cameras_filter,
        cameras_identifications_filter,
    )


def display_camera_details(row, cameras_identifications):
    camera_id = row.name
    image_url = row["snapshot_url"]
    camera_name = row["name"]
    snapshot_timestamp = row["snapshot_timestamp"].strftime("%d/%m/%Y %H:%M")  # noqa

    st.markdown(f"### 📷 Camera snapshot")  # noqa
    st.markdown(f"Endereço: {camera_name}")
    st.markdown(f"Data Snapshot: {snapshot_timestamp}")

    # get cameras_attr url from selected row by id
    if image_url is None:
        st.markdown("Falha ao capturar o snapshot da câmera.")
    else:
        st.image(image_url)

    camera_identifications = cameras_identifications.loc[camera_id]  # noqa
    get_agrid_table(table=camera_identifications.reset_index())


def get_icon_color(label: Union[bool, None]):
    if label in [
        "major",
        "totally_blocked",
        "impossible",
        "impossibe",
        "poor",
        "true",
    ]:  # noqa
        return "red"
    elif label in ["minor", "partially_blocked", "difficult"]:
        return "orange"
    elif label in ["normal", "free", "easy", "moderate", "clean", "false"]:
        return "green"
    else:
        return "gray"


def create_map(chart_data, location=None):
    chart_data = chart_data.fillna("")
    # center map on the mean of the coordinates
    if location is not None:
        m = folium.Map(location=location, zoom_start=16)
    elif len(chart_data) > 0:
        m = folium.Map(
            location=[
                chart_data["latitude"].mean(),
                chart_data["longitude"].mean(),
            ],  # noqa
            zoom_start=10.0,
        )
    else:
        m = folium.Map(location=[-22.917690, -43.413861], zoom_start=10)

    for _, row in chart_data.iterrows():
        icon_color = get_icon_color(row["label"])
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            # Adicionar id_camera ao tooltip
            tooltip=f"ID: {row['id']}<br>Label: {row['label']}",
            # Alterar a cor do ícone de acordo com o status
            icon=folium.features.DivIcon(
                icon_size=(15, 15),
                icon_anchor=(7, 7),
                html=f'<div style="width: 15px; height: 15px; background-color: {icon_color}; border: 2px solid black; border-radius: 70%;"></div>',  # noqa
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


def get_agrid_table(table):
    gb = GridOptionsBuilder.from_dataframe(table)  # noqa

    gb.configure_column("id", header_name="ID Camera", pinned="left")
    gb.configure_column("object", header_name="Identificador")
    gb.configure_column("label", header_name="Label")
    gb.configure_column("timestamp", header_name="Data Identificação")
    gb.configure_column(
        "label_explanation",
        header_name="Descrição",
        cellStyle={"white-space": "normal"},
        autoHeight=True,
    )

    gb.configure_column(
        "snapshot_timestamp", header_name="Data Snapshot", hide=False
    )  # noqa

    gb.configure_selection("single", use_checkbox=False)
    gb.configure_side_bar()
    gb.configure_grid_options(enableCellTextSelection=True)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)  # noqa
    grid_options = gb.build()

    grid_response = AgGrid(
        table,
        gridOptions=grid_options,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        update_mode=GridUpdateMode.MODEL_CHANGED
        | GridUpdateMode.COLUMN_RESIZED,  # noqa
        # fit_columns_on_grid_load=True
        # custom_css=custom_css,
        # allow_unsafe_jscode=True,
        # height="600px",
        # width="100%",
    )

    selected_row = grid_response["selected_rows"]

    return selected_row