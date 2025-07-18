import streamlit as st
import hashlib
from db.mongo_connection import db

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup_page():
    st.subheader("📝 Create a New Account")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up"):
        if password != confirm:
            st.error("Passwords do not match.")
            return

        users_col = db.users
        if users_col.find_one({"username": username}):
            st.error("Username already exists.")
        else:
            users_col.insert_one({
                "username": username,
                "password": hash_password(password)
            })
            st.success("Account created! Go to Login.")
