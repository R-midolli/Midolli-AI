import os
import time
from google import genai
from google.genai import types

# Use the depleted key that hits 429
os.environ["GEMINI_API_KEY_1"] = "YOUR_DEPLETED_KEY_HERE"  # We'll rely on load_dotenv or system env
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("GEMINI_API_KEY_1") or os.getenv("GOOGLE_API_KEY_1")
client = genai.Client(api_key=key)

t0 = time.time()
try:
    print("Trying without retry...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="hello",
        config=types.GenerateContentConfig(
            temperature=0,
            maxOutputTokens=16,
            httpOptions=types.HttpOptions(timeout=10000),
        ),
    )
    print("Success?", response.text)
except Exception as e:
    print("Failed:", e)
finally:
    client.close()
print(f"Elapsed: {time.time() - t0:.2f}s")
