import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGODB_URL = os.getenv("MONGODB_URL")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
START_IMAGE = "your_start_image.jpg"  # Path to your start message image
# Define all your links here
JOIN_LINKS = ["your_group1_link", "your_group2_link", "your_group3_link"]
