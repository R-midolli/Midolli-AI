import os
import time
import google.generativeai as genai
from google.api_core import retry

# Use the depleted key that hits 429
os.environ["GEMINI_API_KEY_1"] = "YOUR_DEPLETED_KEY_HERE"  # We'll rely on load_dotenv or system env
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("GEMINI_API_KEY_1")
genai.configure(api_key=key)

model = genai.GenerativeModel("gemini-1.5-flash")

t0 = time.time()
try:
    print("Trying without retry...")
    response = model.generate_content("hello", request_options={"timeout": 5, "retry": retry.Retry(initial=0, maximum=0, multiplier=1.0, deadline=1.0)})
    print("Success?", response.text)
except Exception as e:
    print("Failed:", e)
print(f"Elapsed: {time.time() - t0:.2f}s")
