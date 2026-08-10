import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

print("=" * 60)
print("Gemini Environment Verification")
print("=" * 60)

# Current working directory
print(f"\nCurrent Working Directory:\n{Path.cwd()}")

# Check if .env exists
env_path = Path(".env")
print(f"\n.env exists: {env_path.exists()}")

if env_path.exists():
    print(f".env path: {env_path.resolve()}")

# Load .env
loaded = load_dotenv()
print(f"\nload_dotenv() returned: {loaded}")

# Read environment variables
gemini_key = os.getenv("GEMINI_API_KEY")
google_key = os.getenv("GOOGLE_API_KEY")

print("\nEnvironment Variables")
print("-" * 60)
print(f"GEMINI_API_KEY found : {gemini_key is not None}")
print(f"GOOGLE_API_KEY found : {google_key is not None}")

if gemini_key:
    print(f"GEMINI_API_KEY prefix : {gemini_key[:10]}...")
    print(f"GEMINI_API_KEY length : {len(gemini_key)}")

if google_key:
    print(f"GOOGLE_API_KEY prefix : {google_key[:10]}...")
    print(f"GOOGLE_API_KEY length : {len(google_key)}")

# Select key
api_key = gemini_key or google_key

print("\nSelected API Key")
print("-" * 60)
print(f"Key Available : {api_key is not None}")

if api_key is None:
    print("\n❌ ERROR: No API key found.")
    print("\nYour .env should contain either:")
    print("GEMINI_API_KEY=<your_key>")
    print("or")
    print("GOOGLE_API_KEY=<your_key>")
    raise SystemExit(1)

print("\nCreating Gemini LLM...")

try:
    llm = ChatGoogleGenerativeAI(
            model="gemini-flash-lite-latest",
    )

    print("✅ LLM created successfully")

    print("\nSending test prompt...")

    response = llm.invoke("Reply with exactly: Hello from Gemini!")

    print("\n" + "=" * 60)
    print("SUCCESS")
    print("=" * 60)
    print(response.content)

except Exception as e:
    print("\n" + "=" * 60)
    print("FAILED")
    print("=" * 60)
    print(type(e).__name__)
    print(e)
