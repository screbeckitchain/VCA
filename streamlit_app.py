import asyncio
import streamlit as st

from VCA import _capture_analysis

st.title("VC Portfolio Analyzer")

url = st.text_input("Введите URL сайта фонда:")

if st.button("Запустить анализ") and url:
    with st.spinner("Анализируем сайт..."):
        results = asyncio.run(_capture_analysis(url))
    st.text(results)
