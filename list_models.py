import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

print("=" * 80)
print("Available Models")
print("=" * 80)

for model in client.models.list():
    print(model.name)