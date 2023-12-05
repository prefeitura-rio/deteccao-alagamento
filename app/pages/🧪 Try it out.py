import streamlit as st

from model import run_model

INITIAL_PICTURE = "./data/imgs/flooded1.jpg"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

st.set_page_config(layout="wide", page_title="Try it out")

st.markdown("# Identify a flood through an image")

col1, col2, col3, col4 = st.columns([1, 0.5, 0.5, 1])

picture = st.camera_input("Take a picture")
if picture is not None:
    if picture.size > MAX_FILE_SIZE:
        st.error(
            "The uploaded file is too large. Please upload an image smaller than 5MB."
        )
    else:
        res = run_model(picture)
else:
    picture = INITIAL_PICTURE
    res = run_model(picture)

if res == "Error":
    st.markdown("### Error ❌")
elif res:
    st.markdown("### Flood identified ✅")
else:
    st.markdown("### Flood not identified ❌")

st.image(picture)
