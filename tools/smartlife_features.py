import random
import datetime

# --- Wellness Tips ---
WELLNESS_TIPS = [
    "Take 10 deep breaths to reset your mind. 🧘‍♂️",
    "Stretch for 5 minutes to improve blood flow. 🙆‍♀️",
    "Avoid screen for 10 minutes and relax. 🌿",
    "Drink a glass of water right now. 💧",
    "Try a 5-minute mindfulness meditation. 🧘‍♀️"
]

# --- Diet Tips ---
DIET_TIPS = [
    "Include more greens in your meals. 🥦",
    "Avoid sugary drinks; go for fresh juice. 🍹",
    "Eat more fiber-rich food like oats and veggies. 🌽",
    "Snack on fruits instead of chips. 🍎",
    "Stay hydrated—aim for 8 glasses a day. 💧"
]

# --- Motivational Quotes ---
MOTIVATIONAL_QUOTES = [
    "Believe you can and you're halfway there. 💡",
    "Every step counts. Keep going! 💪",
    "Stay focused and never give up. 🚀",
    "Your only limit is your mind. 🌟",
    "Make today count! ✨"
]

def get_random_wellness_tip():
    return random.choice(WELLNESS_TIPS)

def get_random_diet_tip():
    return random.choice(DIET_TIPS)

def get_random_motivational_quote():
    return random.choice(MOTIVATIONAL_QUOTES)

def get_voice_assistant_response():
    today = datetime.date.today().strftime("%A, %B %d")
    return f"Here's your SmartLife day plan for {today}: 🧠\n\n- Check today's tasks 🗓️\n- Review any reminders 🔔\n- Stay hydrated and eat healthy 🥗\n- Remember to take mindful breaks 🧘‍♀️\n- Keep going! 💪"

# ✅ ADD THIS AT THE END
def get_tip_based_on_mood(mood: str, llm):
    prompt = f"""
You are a friendly AI wellness assistant. A user says they are feeling {mood}.
Respond with:
1. A short motivational message.
2. One practical self-care tip.
3. A positive suggestion.

Keep the tone empathetic and uplifting.
"""
    return llm.predict(prompt)

# tools/smartlife_features.py

def get_contextual_wellness_response(user_input: str, llm):
    prompt = f"""
You are a kind and emotionally aware wellness assistant.

A user just said: "{user_input}"

Respond with:
1. A short empathetic message based on the user's input.
2. One practical self-care suggestion tailored to how they feel.
3. A motivational quote to encourage them.

Keep the tone warm, friendly, and personal.
"""
    return llm.predict(prompt)

