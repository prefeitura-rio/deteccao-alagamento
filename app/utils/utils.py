# -*- coding: utf-8 -*-
import json  # noqa
import os
from typing import Union

import folium
import pandas as pd
import streamlit as st
from api import APIVisionAI
from st_aggrid import AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder

vision_api = APIVisionAI(
    username=os.environ.get("VISION_API_USERNAME"),
    password=os.environ.get("VISION_API_PASSWORD"),
)


@st.cache_data(ttl=600, persist=False)
def get_cameras(
    use_mock_data=False, update_mock_data=False, page_size=300, timeout=120
):

    mock_data_path = "./data/temp/mock_api_data.json"

    if use_mock_data:
        with open(mock_data_path) as f:
            data = json.load(f)
        return data

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
            location=[
                chart_data["latitude"].mean(),
                chart_data["longitude"].mean(),
            ],  # noqa
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
                html=f'<div style="width: 20px; height: 20px; background-color: {icon_color}; border: 2px solid black; border-radius: 70%;"></div>',  # noqa
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


def get_agrid_table(data_with_image):
    # Configure AgGrid
    gb = GridOptionsBuilder.from_dataframe(data_with_image)  # noqa
    gb.configure_selection("single", use_checkbox=False)
    gb.configure_side_bar()  # if you need a side bar
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)  # noqa

    # configure individual columns
    gb.configure_column("id", header_name="ID Camera", pinned="left")
    # gb.configure_column("emoji", header_name="", pinned="left")
    gb.configure_column("object", header_name="Identificador")
    gb.configure_column("label", header_name="Label")
    gb.configure_column("timestamp", header_name="Data detecção")
    gb.configure_column(
        "label_explanation",
        header_name="Descrição",
        cellStyle={"white-space": "normal"},  # This enables text wrapping
        autoHeight=True,  # Adjusts row height based on content
    )

    gb.configure_column(
        "snapshot_timestamp", header_name="Data Snapshot", hide=False
    )  # noqa
    # gb.configure_column("bairro", header_name="Bairro")
    # gb.configure_column("subprefeitura", header_name="Subprefeitura")
    # gb.configure_column("id_bolsao", header_name="ID Bolsão")
    # gb.configure_column("bacia", header_name="Bacia")
    # gb.configure_column("sub_bacia", header_name="Sub Bacia")

    gb.configure_grid_options(enableCellTextSelection=True)
    # Build grid options
    grid_options = gb.build()

    # Set auto size mode (if you still want to use it, otherwise remove this line) # noqa
    grid_response = AgGrid(
        data_with_image,
        gridOptions=grid_options,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        # update_mode=GridUpdateMode.MODEL_CHANGED | GridUpdateMode.COLUMN_RESIZED, # noqa
        # fit_columns_on_grid_load=True
        # height=400,
        # width="50%",
    )

    selected_row = grid_response["selected_rows"]
    return selected_row
