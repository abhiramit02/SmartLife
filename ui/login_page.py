import streamlit as st
import hashlib
from db.mongo_connection import db

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_page():
    st.sidebar.image("D:/SmartLife/assets/loginlogo.jpeg", use_column_width=True, caption="SmartLife")

    st.subheader("🔐 Login to SmartLife")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users_col = db.users
        user = users_col.find_one({"username": username})
        if user and user["password"] == hash_password(password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Welcome back, {username}!")
        else:
            st.error("Invalid username or password.")
