import datetime
import streamlit as st

def diet_suggestion(llm):
    st.header("🥗 Personalized Diet Checker & Suggestion")

    current_hour = datetime.datetime.now().hour

    st.markdown("💬 _Tell us what you’ve eaten today. Leave blank if you skipped or haven't eaten that meal yet._")

    breakfast = st.text_input("🍳 Breakfast (e.g., Idli and chutney)")
    snack = st.text_input("🍪 Snacks (e.g., biscuits, banana)")
    lunch = st.text_input("🍛 Lunch (e.g., rice, dal, chicken curry)")

    dinner = ""
    if current_hour >= 17:
        dinner = st.text_input("🍽️ Dinner (e.g., chapati, paneer)")

    if st.button("🧾 Get My Diet Feedback"):
        if not any([breakfast, snack, lunch, dinner]):
            st.warning("Please enter at least one meal to analyze your diet.")
        else:
            diet_prompt = f"""
You're a friendly and certified dietitian AI. The user will enter their meals for today. Please analyze and return a well-formatted, colorful, and emoji-supported diet report.

**Instructions:**
1. Estimate approximate calorie intake for each provided meal.
2. Mention any unhealthy food items and their harms.
3. Suggest improvements and healthier alternatives.
4. If a meal is skipped, recommend what to eat.
5. Use markdown formatting with emojis, bullet points, and headings (e.g., **Breakfast 🍳**, **Snack 🍪**, etc.)
6. Write in a positive, supportive tone (avoid judgmental language).
7. End with a friendly reminder to stay hydrated or take care of their health.

Here are the user's meals:

🍳 **Breakfast**: {breakfast if breakfast else 'Not provided'}
🍪 **Snack**: {snack if snack else 'Not provided'}
🍛 **Lunch**: {lunch if lunch else 'Not provided'}
🍽️ **Dinner**: {dinner if dinner else 'Not provided'}

Now generate a markdown-styled diet feedback.
"""

            # Get response
            feedback_result = llm.invoke(diet_prompt)
            feedback_text = getattr(feedback_result, "content", str(feedback_result))

            st.success("🍽️ Here's your personalized diet feedback:")
            st.markdown(feedback_text, unsafe_allow_html=True)  # 👈 now markdown is rendered properly
