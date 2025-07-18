# tools/weather_tool.py

import requests
import os
from dotenv import load_dotenv
load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")

def get_weather(city):
    params = {
        "engine": "google",
        "q": f"weather in {city}",
        "api_key": SERP_API_KEY
    }
    response = requests.get("https://serpapi.com/search", params=params)

    if response.status_code == 200:
        data = response.json()

        weather_box = data.get("weather_result", {})
        temp = weather_box.get("temperature")
        description = weather_box.get("description")

        if temp and description:
            return f"The weather in {city} is {description} with a temperature of {temp}°C.", data

        answer_box = data.get("answer_box", {})
        snippet = answer_box.get("snippet")
        if snippet:
            return f"Weather info (from answer): {snippet}", data

        organic_results = data.get("organic_results", [])
        for result in organic_results:
            title = result.get("title", "")
            if "°C" in title or "weather" in title.lower():
                return f"Weather info (from search): {title}", data

        return "Weather update is currently unavailable.", data
    else:
        return "Weather update is currently unavailable.", {}
