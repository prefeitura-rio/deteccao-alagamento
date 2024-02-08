# -*- coding: utf-8 -*-
import json  # noqa
import os  # noqa
from typing import Union

import folium
import pandas as pd
import streamlit as st
from st_aggrid import (
    AgGrid,
    ColumnsAutoSizeMode,
    GridOptionsBuilder,
    GridUpdateMode,
)
from utils.api import APIVisionAI


def get_vision_ai_api():
    def user_is_logged_in():
        if "logged_in" not in st.session_state:
            st.session_state["logged_in"] = False

        def callback_data():
            username = st.session_state["username"]
            password = st.session_state["password"]
            try:
                _ = APIVisionAI(
                    username=username,
                    password=password,
                )
                st.session_state["logged_in"] = True
            except Exception as exc:
                st.error(f"Error: {exc}")
                st.session_state["logged_in"] = False

        if st.session_state["logged_in"]:
            return True

        st.write("Please login")
        st.text_input("Username", key="username")
        st.text_input("Password", key="password", type="password")
        st.button("Login", on_click=callback_data)
        return False

    if not user_is_logged_in():
        st.stop()

    vision_api = APIVisionAI(
        username=st.session_state["username"],
        password=st.session_state["password"],
    )
    return vision_api


vision_api = get_vision_ai_api()
# vision_api = APIVisionAI(
#     username=os.environ.get("VISION_API_USERNAME"),
#     password=os.environ.get("VISION_API_PASSWORD"),
# )


@st.cache_data(ttl=60 * 2, persist=False)
def get_cameras(
    only_active=True,
    use_mock_data=False,
    update_mock_data=False,
    page_size=3000,
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


@st.cache_data(ttl=60 * 2, persist=False)
def get_objects(
    page_size=100,
    timeout=120,
):
    data = vision_api._get_all_pages(
        path="/objects", page_size=page_size, timeout=timeout
    )
    return data


@st.cache_data(ttl=60 * 60, persist=False)
def get_prompts(
    page_size=100,
    timeout=120,
):
    data = vision_api._get_all_pages(
        path="/prompts", page_size=page_size, timeout=timeout
    )
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


def explode_df(dataframe, column_to_explode, prefix=None):
    df = dataframe.copy()
    exploded_df = df.explode(column_to_explode)
    new_df = pd.json_normalize(exploded_df[column_to_explode])

    if prefix:
        new_df = new_df.add_prefix(f"{prefix}_")

    df.drop(columns=column_to_explode, inplace=True)
    new_df.index = exploded_df.index
    result_df = df.join(new_df)

    return result_df


def get_objetcs_labels_df(objects, keep_null=False):
    objects_df = objects.rename(columns={"id": "object_id"})
    objects_df = objects_df[["name", "object_id", "labels"]]
    labels = explode_df(objects_df, "labels")
    if not keep_null:
        labels = labels[~labels["value"].isin(["null"])]
    labels = labels.rename(columns={"label_id": "label"})
    labels = labels.reset_index(drop=True)
    return labels


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


def get_icon_color(label: Union[bool, None], type=None):
    if label in [
        "major",
        "totally_blocked",
        "impossible",
        "impossibe",
        "poor",
        "true",
        "flodding",
    ]:  # noqa
        if type == "emoji":
            return "🔴"
        return "red"

    elif label in ["minor", "partially_blocked", "difficult", "puddle"]:
        if type == "emoji":
            return "🟠"
        return "orange"
    elif label in [
        "normal",
        "free",
        "easy",
        "moderate",
        "clean",
        "false",
        "low_indifferent",
    ]:
        if type == "emoji":
            return "🟢"

        return "green"
    else:
        if type == "emoji":
            return "⚫"
        return "grey"


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
            zoom_start=11,
        )
    else:
        m = folium.Map(location=[-22.917690, -43.413861], zoom_start=11)

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


def display_camera_details(row, cameras_identifications):
    camera_id = row.name
    image_url = row["snapshot_url"]
    camera_name = row["name"]
    snapshot_timestamp = row["snapshot_timestamp"].strftime("%d/%m/%Y %H:%M")  # noqa

    st.markdown(f"### 📷 Camera snapshot")  # noqa
    st.markdown(f"Endereço: {camera_name}")
    # st.markdown(f"Data Snapshot: {snapshot_timestamp}")

    # get cameras_attr url from selected row by id
    if image_url is None:
        st.markdown("Falha ao capturar o snapshot da câmera.")
    else:
        st.markdown(
            f"""<img src='{image_url}' style='max-width: 100%; max-height: 371px;'> """,  # noqa
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 📃 Detalhes")

    camera_identifications = cameras_identifications.loc[camera_id]  # noqa
    camera_identifications = camera_identifications.reset_index(drop=True)

    camera_identifications[""] = camera_identifications["label"].apply(
        lambda x: get_icon_color(x, type="emoji")
    )
    camera_identifications.index = camera_identifications[""]

    camera_identifications["timestamp"] = camera_identifications[
        "timestamp"
    ].apply(  # noqa
        lambda x: x.strftime("%d/%m/%Y %H:%M")
    )
    rename_columns = {
        "timestamp": "Data Identificação",
        "object": "Identificador",
        "label": "Label",
        "label_explanation": "Descrição",
    }
    camera_identifications = camera_identifications[list(rename_columns.keys())]  # noqa

    camera_identifications = camera_identifications.rename(
        columns=rename_columns
    )  # noqa

    st.dataframe(camera_identifications)


def display_agrid_table(table):
    gb = GridOptionsBuilder.from_dataframe(table, index=True)  # noqa

    gb.configure_column("index", header_name="", pinned="left")
    gb.configure_column("id", header_name="ID Camera", pinned="left")  # noqa
    gb.configure_column("object", header_name="Identificador", wrapText=True)
    gb.configure_column("label", header_name="Label", wrapText=True)
    gb.configure_column(
        "timestamp", header_name="Data Identificação", wrapText=True
    )  # noqa
    gb.configure_column(
        "snapshot_timestamp",
        header_name="Data Snapshot",
        hide=False,
        wrapText=True,  # noqa
    )  # noqa
    gb.configure_column(
        "label_explanation",
        header_name="Descrição",
        cellStyle={"white-space": "normal"},
        autoHeight=True,
        wrapText=True,
        hide=True,
    )
    gb.configure_side_bar()
    gb.configure_selection("single", use_checkbox=False)
    gb.configure_grid_options(enableCellTextSelection=True)
    # gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)  # noqa
    grid_options = gb.build()
    grid_response = AgGrid(
        table,
        gridOptions=grid_options,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        update_mode=GridUpdateMode.MODEL_CHANGED
        | GridUpdateMode.COLUMN_RESIZED,  # noqa
        # fit_columns_on_grid_load=True,
        height=413,
        custom_css={
            "#gridToolBar": {
                "padding-bottom": "0px !important",
            }
        },
    )

    selected_row = grid_response["selected_rows"]

    return selected_row
