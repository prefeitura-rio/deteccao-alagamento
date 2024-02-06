# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
from utils.utils import get_cameras, get_objects, get_objetcs_labels_df, treat_data

st.set_page_config(layout="wide", page_title="Pontos de Alagamento")
st.image("./data/logo/logo.png", width=300)

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

cameras_objs = cameras_objs.head(4)

st.markdown(
    """
    <style>
    .big-button {
        width: 100%;
        font-size: 24px;
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def put_selected_label(labels_options, label):
    selected_label = labels_options[labels_options["value"] == label]
    selected_label = selected_label.reset_index()
    label_to_put = selected_label.to_dict(orient="records")
    # TODO: make a put for selected object/label
    print(label_to_put, "\n")


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
    st.image(snapshot_url, use_column_width=True)
    labels_options = labels.loc[name]
    choces = labels_options["value"].tolist()

    st.markdown(f"**Options for {name}:**")

    for label in choces:
        if st.button(
            label,
            on_click=put_selected_label,
            args=(
                labels_options,
                label,
            ),
        ):  # noqa
            pass
    st.session_state.current_image_index += 1  # noqa
