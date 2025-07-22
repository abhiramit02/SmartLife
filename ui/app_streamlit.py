# ui/app_streamlit.py

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import base64

import streamlit as st
import requests
from langchain_groq import ChatGroq
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from ui.pdf_chat_module import render_pdf_chat
from tools.diet_advisor import diet_suggestion
from dotenv import load_dotenv
from tools.smartlife_voice_assistant import main as run_voice_assistant
from ui.login_page import login_page
from ui.signup_page import signup_page

import tempfile

import datetime
from tools.calendar_tool import add_task, get_tasks, complete_task, get_motivation
from tools.smartlife_features import (
    get_random_wellness_tip,
    get_random_diet_tip,
    get_random_motivational_quote,
    get_voice_assistant_response,
    get_tip_based_on_mood,
    get_contextual_wellness_response
)
from tools.motivation_booster import (
    get_random_spotify_playlist,
    get_random_youtube_video,
    get_random_nature_video,
    get_youtube_video_by_query
)
import io
from tools.smartlife_voice_assistant import run_voice_assistant

import streamlit as st
from langchain_groq import ChatGroq
from gtts import gTTS
import base64  # Make sure this is at the top of your script

def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        b64_data = base64.b64encode(img_file.read()).decode()
    return b64_data


# Load environment
load_dotenv()
print("✅ YOUTUBE_API_KEY from .env:", os.getenv("YOUTUBE_API_KEY"))
import os
from dotenv import load_dotenv
load_dotenv()
# Get keys from Streamlit secrets
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
SERP_API_KEY = st.secrets["SERPAPI_API_KEY"]

# ✅ Access the key from Streamlit secrets
groq_api_key = st.secrets["GROQ_API_KEY"]

# ✅ Pass the key explicitly
llm = ChatGroq(
    api_key=groq_api_key,  # REQUIRED!
    model="mixtral-8x7b-32768"  # or "llama3-8b-8192", etc.
)

if 'users' not in st.session_state:
    st.session_state.users = {
        "Abhirami": "abhiramit09"  # Predefined user for testing
    }

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'username' not in st.session_state:
    st.session_state.username = ""


def speak_streamlit(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        temp_path = fp.name
        tts.save(temp_path)
        audio_bytes = open(temp_path, "rb").read()
    os.remove(temp_path)
    return io.BytesIO(audio_bytes)


# --- News & Weather Functions ---
def get_weather(city):
    params = {"engine": "google", "q": f"weather in {city}", "api_key": SERP_API_KEY}
    response = requests.get("https://serpapi.com/search", params=params)
    if response.status_code == 200:
        data = response.json()
        weather_box = data.get("weather_result", {})
        temp = weather_box.get("temperature")
        description = weather_box.get("description")
        if temp and description:
            return f"The weather in {city} is {description} with a temperature of {temp}°C.", data
        snippet = data.get("answer_box", {}).get("snippet")
        if snippet:
            return f"Weather info: {snippet}", data
        for res in data.get("organic_results", []):
            title = res.get("title", "")
            if "°C" in title or "weather" in title.lower():
                return f"Weather info: {title}", data
        return "Weather update is currently unavailable.", data
    else:
        return "Weather update is currently unavailable.", {}

def get_top_news():
    url = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&country=in&language=en&category=top"
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get("results", [])[:5]
        if not articles:
            return "No news headlines available."
        return "\n\n".join([f"{i+1}. {a['title']}" for i, a in enumerate(articles)])
    else:
        return f"Couldn't fetch news. Status: {response.status_code}"

# --- LLM Setup ---
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(return_messages=True)

llm = ChatGroq(model="llama3-70b-8192", temperature=0.5)

conversation = ConversationChain(llm=llm, memory=st.session_state.memory, verbose=False)
import streamlit as st

# Initialize session state variables
if "page" not in st.session_state:
    st.session_state.page = "login"  # Start at login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Dummy user store (replace with DB or file system in real app)
if "users" not in st.session_state:
    st.session_state.users = {}  # {username: password}

# Login page
import streamlit as st

def login_page():
    st.set_page_config(page_title="Login | SmartLife", layout="wide")

    # Two-column layout: left for image, right for login
    left_col, right_col = st.columns([0.5, 0.6])

    with left_col:
        st.image("assets/login_logo.jpeg", use_container_width=True)


    with right_col:
        st.markdown("<h1 style='text-align: center;'>🔐 Login</h1>", unsafe_allow_html=True)
        st.markdown("""
    <style>
        .small-input input {
            width: 200px !important;
            height: 30px !important;
            font-size: 14px !important;
        }
    </style>
""", unsafe_allow_html=True)


        username = st.text_input("Username")  # No key
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username in st.session_state.users and st.session_state.users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "home"
            else:
                st.error("Invalid username or password.")

        st.markdown("---")
        st.text("New user?")
        if st.button("Go to Sign Up"):
            st.session_state.page = "signup"


# Signup page
def signup_page():
    st.set_page_config(page_title="Sign Up | SmartLife", layout="wide")

    # Two-column layout: left for image, right for signup form
    left_col, right_col = st.columns([0.6, 1])  # 0.5 width each

    with left_col:
        # Make image fill container
        st.image("assets/signup.png", use_container_width=True)

    with right_col:
        st.markdown("<h1 style='text-align: center;'>📝 Sign Up</h1>", unsafe_allow_html=True)

        username = st.text_input("Choose a Username")
        password = st.text_input("Choose a Password", type="password")

        if st.button("Create Account"):
            if username in st.session_state.users:
                st.error("Username already exists.")
            else:
                st.session_state.users[username] = password
                st.success("Account created successfully!")
                st.session_state.page = "login"

        if st.button("Back to Login"):
            st.session_state.page = "login"
# Home page
def home_page():
    st.title("🤖 SmartLife – Your AI Companion")
    st.success(f"Welcome, {st.session_state.username}!")
    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.session_state.username = ""

# Routing logic
# --- UI Setup ---
st.set_page_config(page_title="SmartLife AI", layout="centered")

# --- Login & Signup Routing ---
if st.session_state.page == "login":
    login_page()
    st.stop()
elif st.session_state.page == "signup":
    signup_page()
    st.stop()
elif not st.session_state.logged_in:
    st.warning("⚠️ Please log in to continue.")
    st.session_state.page = "login"
    st.stop()

# Initialize session


    # You can now import your assistant features here
    # from tools.smartlife_voice_assistant import main as run_voice_assistant
    # run_voice_assistant()
# --- Features ---
features = [
    "🏠 Home",
    "🗓️ Task Planner",
    "🧘 Wellness & Mood",
    "🥗 Diet Tips",
    "📈 Motivation",
    "📢 Voice Assistant",
    "📄 PDF Q&A",
    "📰 City News & Weather"
]

# Get selected feature from query param
query_selected = st.query_params.get("feature")
if query_selected and query_selected in features:
    st.session_state.selected_feature = query_selected
    st.query_params.clear()

# --- Feature Selection ---
if "selected_feature" not in st.session_state:
    st.session_state.selected_feature = "🏠 Home"

# Set current feature
feature = st.session_state.selected_feature# --- Home Page ---# --- Home Page ---
if feature == "🏠 Home":
    st.set_page_config(layout="centered")

    # --- Header CSS (Title + Logout button)
    header_css = """
    <style>
        .header-container {
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 2rem 1rem 2rem;
            box-sizing: border-box;
        }
        .header-container h1 {
            margin: 0;
            font-size: 40px;
        }
        .logout-button button {
            background-color: #ff4b4b;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            border: none;
            font-weight: bold;
            cursor: pointer;
            font-size: 16px;
            box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
        }
        .logout-button button:hover {
            background-color: #e63939;
        }
    </style>
    """
    st.markdown(header_css, unsafe_allow_html=True)

    # --- Header HTML (Title + Logout button)
    header_html = """
    <div class="header-container">
        <h1>🤖 Welcome to SmartLife – Your AI Companion</h1>
        <div class="logout-button">
            <form action="" method="post">
                <button type="submit">Logout</button>
            </form>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    # --- Logout JavaScript handling
    st.markdown("""
    <script>
        const form = window.parent.document.querySelector("form");
        if (form) {
            form.addEventListener("submit", () => {
                window.parent.postMessage({ type: "logoutClicked" }, "*");
            });
        }

        window.addEventListener("message", (event) => {
            if (event.data.type === "logoutClicked") {
                fetch("/_stcore/stream", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ clicked_logout: true })
                });
            }
        });
    </script>
    """, unsafe_allow_html=True)

    # --- Session update if logout clicked
    if st.session_state.get("clicked_logout", False):
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.session_state.username = ""
        st.rerun()

    # --- Background CSS (inside the if block!)


    # --- Feature intro
    st.markdown("### ✨ Features")

    # --- Improved Feature Card CSS
    grid_css = """
    <style>
        .stButton button {
            background-color: #f5f5f5;
            border-radius: 0.75rem;
            padding: 1rem;
            width: 100%;
            text-align: center;
            font-weight: bold;
            color: black;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
            border: none;
            margin-bottom: 1.5rem;
        }
        .stButton button:hover {
            transform: translateY(-3px);
            background-color: #eaf2ff;
        }
        .feature-caption {
            text-align: center;
            font-size: 14px;
            color: #555;
            margin-top: 0.25rem;
            margin-bottom: 1rem;
        }
    </style>
    """
    st.markdown(grid_css, unsafe_allow_html=True)

    # --- Define features
    features = [
        ("🗓️", "Task Planner", "Plan your tasks and stay organized"),
        ("🧘", "Wellness & Mood", "Get tips based on your mood"),
        ("🥗", "Diet Tips", "Personalized dietary suggestions"),
        ("📈", "Motivation", "Quotes and content to lift your spirit"),
        ("📢", "Voice Assistant", "Talk to SmartLife using voice"),
        ("📄", "PDF Q&A", "Ask questions from any PDF"),
        ("📰", "City News & Weather", "Get latest news and weather by city"),
    ]

    # --- Render features in balanced grid
    cols = st.columns(4)
    for i, (emoji, label, caption) in enumerate(features):
        with cols[i % 4]:
            if st.button(f"{emoji} {label}", key=label):
                st.session_state.selected_feature = f"{emoji} {label}"
                st.rerun()
            st.markdown(f'<div class="feature-caption">{caption}</div>', unsafe_allow_html=True)








elif feature == "🗓️ Task Planner":
    import base64
    import datetime

    spacer, left_col, right_col = st.columns([0.05, 0.4, 0.55])  # 1/4 and 3/4 ratio

    with left_col:
        img_path = "assets/task.png"
        img_base64 = base64.b64encode(open(img_path, "rb").read()).decode()

        st.markdown(
            f"""
            <div style="height: 100vh; display: flex; flex-direction: column;">
                <img src="data:image/png;base64,{img_base64}" 
                     style="width: 120%; height: 100%; object-fit: cover; margin-left: -10%;" />
            </div>
            """,
            unsafe_allow_html=True
        )

    with right_col:
        st.markdown("<h1 style='text-align: center;'>📆 Calendar Planner & Task Tracker</h1>", unsafe_allow_html=True)

        task_text = st.text_input("✍️ New Task", placeholder="e.g., Submit assignment")
        task_date = st.date_input("📅 Select Date", datetime.date.today())

        if st.button("➕ Add Task"):
            if task_text.strip():
                add_task(task_date.isoformat(), task_text.strip(), st.session_state.username)
                st.success("Task added successfully!")
            else:
                st.warning("Please enter a valid task.")

        st.markdown("### 📌 View Tasks by Date")
        selected_view_date = st.date_input("📅 Choose a date to view tasks", datetime.date.today())
        tasks = get_tasks(selected_view_date.isoformat(), st.session_state.username)

        if tasks:
            for idx, task in enumerate(tasks):
                task_display = f"{'✅' if task['completed'] else '🕒'} {task['task']}"
                col_task, col_button = st.columns([0.85, 0.15])
                with col_task:
                    st.markdown(task_display)
                with col_button:
                    if not task['completed'] and st.button("Done", key=f"{selected_view_date}_{idx}"):
                        complete_task(selected_view_date.isoformat(), idx, st.session_state.username)
                        st.session_state["motivational_quote"] = get_motivation()
                        st.rerun()
        else:
            st.info("No tasks for this date yet. Try adding one!")

        # Show motivational quote after task completion
        if "motivational_quote" in st.session_state:
            st.success(st.session_state["motivational_quote"])
            del st.session_state["motivational_quote"]

        # ✅ Go to Home Button (now properly inside right_col)
        if st.button("🏠 Go to Home"):
            st.session_state.selected_feature = "🏠 Home"
            st.rerun()

            

elif feature == "🧘 Wellness & Mood":
    import base64
    import os

    # Create two columns: 1/4 for image, 3/4 for content
    left_col, right_col = st.columns([1, 3])
    image_path = "assets/wellness_and_mood.png"
    def get_base64_image(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    if os.path.exists(image_path):
        img_base64 = get_base64_image(image_path)
        with left_col:
              st.markdown(
    f"""
    <div style="height: 85vh; display: flex; justify-content: center; align-items: center; overflow: hidden;">
        <img src="data:image/jpeg;base64,{img_base64}" 
             style="width: 145%;
                    height: 65vh;
                    object-fit: cover;
                    margin-left: -20%;
                    border-radius: 0 12px 12px 0;" />
    </div>
    """,
    unsafe_allow_html=True
)
        
    
    else:
        st.error(f"Image not found at {image_path}")



    with right_col:
        st.markdown("<h1 style='text-align: center;'>🧘‍♀️ Wellness & Mood Support</h1>", unsafe_allow_html=True)

        # Input and buttons
        mood_input = st.text_input("🧠 How are you feeling?", key="mood_input")

        if st.button("💡 Get Personalized Wellness Suggestion"):
            if mood_input.strip():
                suggestion = get_contextual_wellness_response(mood_input, llm)
                st.success("🌿 Here's something to support your wellness:")
                st.markdown(f"📝 **You said:** _{mood_input}_")
                st.markdown(f"🧘 **SmartLife Suggests:**\n> {suggestion.strip()}")
            else:
                st.warning("⚠️ Please describe how you feel to receive a suggestion.")

        if st.button("🏠 Go to Home"):
            st.session_state.selected_feature = "🏠 Home"
            st.rerun()
    



elif feature == "🥗 Diet Tips":
    col1, col2 = st.columns([3, 5])  # Sidebar image : Main content

    with col1:
        img_b64 = get_image_base64("assets/diet.png")
        st.markdown(
        f"""
        <div style="height: 100vh; width: 100%; display: flex; align-items: stretch; justify-content: flex-start; margin-left: -16px;">
            <img src="data:image/png;base64,{img_b64}" style="height: 70vh; width: 80%; object-fit: cover;">
        </div>
        """,
        unsafe_allow_html=True
    )
    
    


    with col2:
        diet_suggestion(llm)
        if st.button("🏠 Go to Home"):
            st.session_state.selected_feature = "🏠 Home"
            st.rerun()



elif feature == "📈 Motivation":
    col1, col2 = st.columns([5, 7])  # Wider left for sidebar, larger right for content

    with col1:
        img_b64 = get_image_base64("assets/motivation.png")  # Replace with your actual image
        st.markdown(
            f"""
            <div style="height: 100vh; width: 100%; display: flex; align-items: stretch; justify-content: flex-start; margin-left: -16px;">
                <img src="data:image/png;base64,{img_b64}" style="height: 100vh; width: 100%; object-fit: cover;">
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.header("📈 Motivation Booster")
        if st.button("🚀 Get Motivated"):
            st.success(get_random_motivational_quote())

        st.markdown("---")
        st.subheader("🎧 Instant Mood Booster")
        st.subheader("🧠 Custom YouTube Motivation Search")
        user_query = st.text_input("🔍 What would you like to hear?", placeholder="e.g., Tamil speech, motivation music")

        if st.button("▶️ Play Based on My Query"):
            if user_query.strip():
                url = get_youtube_video_by_query(user_query)
                if url:
                    st.video(url)
                else:
                    st.warning("Couldn't find a video for that query.")
            else:
                st.info("Please enter a phrase like 'Abdul Kalam speech'.")

        col1_inner, col2_inner, col3_inner = st.columns(3)
        with col1_inner:
            if st.button("🎵 Spotify Motivation"):
                url = get_random_spotify_playlist()
                st.markdown(f"[Open Playlist]({url})", unsafe_allow_html=True)
                st.audio(url)
        with col2_inner:
            if st.button("🔥 YouTube Pep Talk"):
                st.video(get_random_youtube_video())
        with col3_inner:
            if st.button("🌿 Nature Relaxation"):
                st.video(get_random_nature_video())

        if st.button("🏠 Go to Home"):
            st.session_state.selected_feature = "🏠 Home"
            st.rerun()



elif feature == "📢 Voice Assistant":
    col1, col2 = st.columns([6, 7])

    with col1:
        img_b64 = get_image_base64("assets/voice.png")
        st.markdown(
            f"""
            <div style="height: 40vh; width: 100%; display: flex; align-items: stretch; justify-content: flex-start; margin-left: -16px;">
                <img src="data:image/png;base64,{img_b64}" style="height: 60vh; width: 100%; object-fit: cover;">
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.header("📢 Voice Assistant Mode")
        st.markdown("🎤 Click below and speak a command like:")
        st.markdown("- *What's my schedule today?*")
        st.markdown("- *Motivate me!*")

        if st.button("🗣️ Speak Now"):
            with st.spinner("🔄 Processing your voice..."):
                audio_data, command, reply = run_voice_assistant()

            if command is None:
                st.warning(reply)
            else:
                st.write(f"🗣️ You said: **{command}**")
                st.success(f"🤖 SmartLife: {reply}")
                st.audio(audio_data, format="audio/mp3")

        if st.button("🏠 Go to Home"):
            st.session_state.selected_feature = "🏠 Home"
            st.rerun()


elif feature == "📄 PDF Q&A":
    col1, col2 = st.columns([3, 7])  # Sidebar image : PDF chat content

    with col1:
        img_b64 = get_image_base64("assets/pdf.png")  # Replace with your desired image path
        st.markdown(
            f"""
            <div style="height: 100vh; width: 100%; display: flex; align-items: stretch; justify-content: flex-start; margin-left: -16px;">
                <img src="data:image/png;base64,{img_b64}" style="height: 80vh; width: 100%; object-fit: cover;">
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        render_pdf_chat()
        if st.button("🏠 Go to Home"):
            st.session_state.selected_feature = "🏠 Home"
            st.rerun()


elif feature == "📰 City News & Weather":
    col1, col2 = st.columns([6, 7])  # Wider left for sidebar, larger right for content

    with col1:
        img_b64 = get_image_base64("assets/climate.png")  # Update path to your image
        st.markdown(
            f"""
            <div style="height: 100vh; width: 100%; display: flex; align-items: stretch; justify-content: flex-start; margin-left: -16px;">
                <img src="data:image/png;base64,{img_b64}" style="height: 80vh; width: 90%; object-fit: cover;">
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.header("📰 City News & Weather")
        city = st.text_input("🏙️ Enter your city", "Coimbatore")

        if st.button("📡 Get Weather & News"):
            weather_info, _ = get_weather(city)
            news_info = get_top_news()

            prompt = f"""
            You are a helpful assistant that provides weather and news updates.
            1. Give a short weather update for the city.
            2. Summarize each news headline clearly and professionally.
            Weather:\n{weather_info}\nNews:\n{news_info}
            """
            ai_response = conversation.predict(input=prompt)

            st.subheader("🌤️ Weather + News Summary")
            st.write(ai_response)

        if st.button("🏠 Go to Home"):
            st.session_state.selected_feature = "🏠 Home"
            st.rerun()

        

