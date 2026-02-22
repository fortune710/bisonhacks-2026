
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise Exception("MONGO_URI not set in .env")

# Singleton client
client = MongoClient(MONGO_URI)
db = client["foodnav"]  # Your database