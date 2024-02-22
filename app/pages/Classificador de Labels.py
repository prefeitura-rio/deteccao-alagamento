# -*- coding: utf-8 -*-

import pandas as pd
import streamlit as st
from utils.utils import (
    get_ai_identifications_cache,
    get_objects_cache,
    get_objetcs_labels_df,
    send_user_identification,
)

st.set_page_config(
    page_title="Classificador de Labels",
    layout="wide",
    initial_sidebar_state="collapsed",
)
# st.image("./data/logo/logo.png", width=300)

st.markdown("# Classificador de labels | Vision AI")

objects = pd.DataFrame(get_objects_cache())

object_labels = get_objetcs_labels_df(objects)
# labels.index = labels["name"]
# labels = labels.drop(columns=["name"])

identifications = [
    identification
    for identification in get_ai_identifications_cache()
    if identification["object"] != "image_description"
]


# https://docs.google.com/document/d/1PRCjbIJw4_g3-p4gLjYoN0qTaenephyZyOsiOfVGWzM/edit
def put_selected_label(label, index):
    send_user_identification(identifications[index]["id"], label)

    if (identifications[index]["object"] == "image_corrupted") and (label == "true"):
        jump = 1
        while (index + jump) < len(identifications) and identifications[index + jump][
            "snapshot_url"
        ] == identifications[index]["snapshot_url"]:
            send_user_identification(identifications[index + jump]["id"], "null")
            jump += 1

        if (index + jump) >= len(identifications):
            st.session_state.finish = True
        else:
            st.session_state.next_id = identifications[index + jump]["id"]
    else:
        if index + 1 >= len(identifications):
            st.session_state.finish = True
        else:
            st.session_state.next_id = identifications[index + 1]["id"]


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


def buttom(
    label,
    label_translated,
    index,
):
    if st.button(
        label_translated,
        on_click=put_selected_label,
        args=(
            label,
            index,
        ),
    ):  # noqa
        pass


if "next_id" not in st.session_state:
    st.session_state.next_id = None
    st.session_state.finish = False

index = 0
if st.session_state.next_id is not None:
    for i, identification in enumerate(identifications):
        if identification["id"] == st.session_state.next_id:
            index = i

if index >= len(identifications) or st.session_state.finish:
    st.write("Você já revisou todas as imagens.")
    if st.button("Reset"):
        st.markdown("TODO: Reset the state variables and start over.")
else:
    identification = identifications[index]
    object_ = identification["object"]
    snapshot_url = identification["snapshot_url"]
    possible_labels = object_labels[object_labels["name"] == object_]

    col1, col2 = st.columns([1, 1.5])
    with col2:
        st.image(snapshot_url)
    with col1:
        st.markdown(f"### {identification['question']}")
        st.markdown(f"**Explicação:** {identification['explanation']}")

    for text, label in zip(possible_labels["text"], possible_labels["value"]):
        with col1:
            buttom(label=label, label_translated=text, index=index)
