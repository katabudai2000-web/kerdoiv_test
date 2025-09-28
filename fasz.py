import streamlit as st
import time

st.title("Teszt kérdőív – Streamlit")

# időmérés indul
if "start_time" not in st.session_state:
    st.session_state["start_time"] = time.time()

# kérdés 1
name = st.text_input("Mi a keresztneved?")

# kérdés 2
color = st.radio("Melyik színt szereted jobban?", ["Piros", "Kék", "Zöld"])

# gomb
if st.button("Beküldés"):
    end_time = time.time()
    elapsed = round(end_time - st.session_state["start_time"], 2)
    st.success(f"Köszönöm, {name}! A válaszod rögzítve. ⏱️ {elapsed} másodperc alatt töltötted ki.")
