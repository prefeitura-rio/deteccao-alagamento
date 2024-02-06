# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
from utils.utils import (get_cameras, get_objects, get_objetcs_labels_df,
                         treat_data)

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
# st.image("./data/logo/logo.png", width=300)

st.markdown("# Classificador de labels | Vision AI")

cameras = get_cameras(
    only_active=False,
    use_mock_data=False,
    update_mock_data=True,
)
objects = pd.DataFrame(get_objects())

cameras_attr, cameras_identifications = treat_data(cameras)
snapshots = cameras_attr[cameras_attr["snapshot_url"].notnull()][
    ["snapshot_url"]
]  # noqa
cameras_objs = cameras_identifications[cameras_identifications.notna()][
    ["object", "label"]
]
cameras_objs = cameras_objs[~cameras_objs["label"].isin(["null"])]
cameras_objs = cameras_objs.merge(snapshots, on="id")
cameras_objs = cameras_objs.sample(frac=1)
labels = get_objetcs_labels_df(objects)
labels.index = labels["name"]
labels = labels.drop(columns=["name"])

# cameras_objs = cameras_objs.head(4)


def put_selected_label(labels_options, label):
    selected_label = labels_options[labels_options["value"] == label]
    selected_label = selected_label.reset_index()
    label_to_put = selected_label.to_dict(orient="records")
    # TODO: make a put for selected object/label
    print(label_to_put, "\n")


customized_button = st.markdown(
    """
    <style >
    div.stButton > button:first-child {
        height: 100% !important;
        width: 100% !important;
        font-size: 15px !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
    </style>""",
    unsafe_allow_html=True,
)


def buttom(label, labels_options):
    if st.button(
        label,
        on_click=put_selected_label,
        args=(
            labels_options,
            label,
        ),
    ):  # noqa
        pass


# Create a state variable to keep track of the current image index
if "current_image_index" not in st.session_state:
    st.session_state.current_image_index = 0


# Check if there are more images to review
if st.session_state.current_image_index >= len(cameras_objs):
    st.write("You have reviewed all images.")
    if st.button("Reset"):
        st.markdown("TODO: Reset the state variables and start over.")

else:
    # Get the current image from the DataFrame
    current_image = cameras_objs.iloc[st.session_state.current_image_index]  # noqa
    st.write(
        f"INDEX: {st.session_state.current_image_index +1} / {len(cameras_objs)}"  # noqa
    )  # noqa
    # Extract relevant information
    name = current_image["object"]

    snapshot_url = current_image["snapshot_url"]

    # Center the image
    st.markdown(
        f"""
        <div style='display: flex; justify-content: center; align-items: center;'>
        <img src='{snapshot_url}' style='max-width: 600px; max-height: 400px;'>
        </div>
        """,
        unsafe_allow_html=True,
    )

    labels_options = labels.loc[name]
    choices = labels_options["value"].tolist()

    st.markdown(
        f"<h2 style='text-align: center;'>{name}</h2>",
        unsafe_allow_html=True,
    )

    # place labels in a grid of 2 columns
    col1, col2, col3, col4 = st.columns(4)
    for i, label in enumerate(choices):
        if i % 2 == 0:
            with col2:
                buttom(label, labels_options)
        else:
            with col3:
                buttom(label, labels_options)

    st.session_state.current_image_index += 1  # noqa
