import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
	print("Y .env loaded successfully!")
else:
	print("X .env not loaded or API missing.")
