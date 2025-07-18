# tools/news_tool.py

import requests
import os
from dotenv import load_dotenv
load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_top_news():
    url = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&country=in&language=en&category=top"
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get("results", [])[:5]
        if not articles:
            return "No news headlines available."
        news = "\n\n".join([f"{i+1}. {article['title']}" for i, article in enumerate(articles)])
        return f"Top News Headlines:\n{news}"
    else:
        return f"Couldn't fetch news headlines. Status: {response.status_code}"
