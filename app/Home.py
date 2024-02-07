# -*- coding: utf-8 -*-
# import folium # noqa

import streamlit as st
from streamlit_folium import st_folium  # noqa
from utils.utils import (
    create_map,
    display_camera_details,
    get_agrid_table,
    get_cameras,
    get_filted_cameras_objects,
    treat_data,
    get_icon_color,
)

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
# st.image("./data/logo/logo.png", width=300)

DEFAULT_OBJECT = "water_level"
st.markdown("# Identificações | Vision AI")

# get cameras
cameras = get_cameras(
    page_size=3000,
    only_active=False,
    use_mock_data=False,
    update_mock_data=False,
)
cameras_attr, cameras_identifications = treat_data(cameras)

col1, col2 = st.columns(2)

with col1:
    objects = cameras_identifications["object"].unique().tolist()
    objects.sort()
    # dropdown to filter by object
    object_filter = st.selectbox(
        "Filtrar por objeto",
        objects,
        index=objects.index(DEFAULT_OBJECT),
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

    # if object_filter == "road_blockade":
    #     labels_default.remove("normal")
    # dropdown to select label given selected object
    label_filter = st.multiselect(
        "Filtrar por label",
        labels,
        # if object_filter return minor and major, else return all labels
        default=labels_default,
    )


(
    cameras_identifications_merged,
    cameras_filter,
    cameras_identifications_filter,
) = get_filted_cameras_objects(
    cameras_attr, cameras_identifications, object_filter, label_filter
)


# make two cols
col1, col2 = st.columns(2)
folium_map = create_map(cameras_identifications_merged.reset_index())

with col1:
    selected_cols = [
        "index",
        "id",
        "object",
        "label",
        "timestamp",
        "snapshot_timestamp",
        "bairro",
    ]
    aggrid_table = cameras_identifications_merged.reset_index()

    aggrid_table["index"] = aggrid_table["label"].apply(
        lambda label: get_icon_color(label=label, type="emoji")
    )
    aggrid_table = aggrid_table[selected_cols]
    # aggrid_table = aggrid_table[selected_cols]
    selected_row = get_agrid_table(aggrid_table)  # noqa

with col2:
    if selected_row:
        camera_id = selected_row[0]["id"]
        row = cameras_filter.loc[camera_id]

        camera_location = [row["latitude"], row["longitude"]]
        folium_map = create_map(
            cameras_identifications_merged.reset_index(),
            location=camera_location,  # noqa
        )

        display_camera_details(
            row=row, cameras_identifications=cameras_identifications
        )  # noqa
    else:
        st.markdown(
            """
            ### 📷 Câmera snapshot
            Selecione uma Câmera na tabela para visualizar mais detalhes.
            """
        )

with col1:
    st.markdown("### 📍 Mapa")
    st_folium(folium_map, key="fig1", height=600, width="100%")

    # for camera_id in cameras_identifications_filter.index:
    #     row = cameras_filter.loc[camera_id]
    #     display_camera_details(
    #         row=row, cameras_identifications=cameras_identifications
    #     )
    #     time.sleep(2)
