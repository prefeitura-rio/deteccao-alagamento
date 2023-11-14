import streamlit as st

from model import run_model


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

st.set_page_config(layout="wide", page_title="Experimente o Modelo")

st.markdown("# Identifique um alagamento por uma imagem")

my_upload = st.file_uploader("Faça upload de uma imagem", type=["png", "jpg", "jpeg"])

if my_upload is not None:
    if my_upload.size > MAX_FILE_SIZE:
        st.error(
            "The uploaded file is too large. Please upload an image smaller than 5MB."
        )
    else:
        res = run_model(my_upload)
else:
    my_upload = "./data/imgs/flooded1.jpg"
    res = run_model(my_upload)

if res:
    st.markdown("### Alagamento Identificado ✅")
else:
    st.markdown("### Alagamento Não Identificado ❌")

st.image(my_upload)
