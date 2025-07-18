# db/mongo_connection.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")  # example: mongodb://localhost:27017
DB_NAME = "smartlife_db"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
