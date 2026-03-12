import os
from openai import OpenAI
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Test NVIDIA
print("Testing NVIDIA...")
try:
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=nvidia_key,
    )
    # let's try a known model like meta/llama-3.1-70b-instruct
    response = client.chat.completions.create(
        model="meta/llama-3.1-70b-instruct",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=10
    )
    print("NVIDIA meta/llama-3.1-70b-instruct OK:", response.choices[0].message.content)
except Exception as e:
    print("NVIDIA meta/llama-3.1-70b-instruct Failed:", e)

try:
    response = client.chat.completions.create(
        model="qwen/qwen2.5-72b-instruct",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=10
    )
    print("NVIDIA qwen/qwen2.5-72b-instruct OK:", response.choices[0].message.content)
except Exception as e:
    print("NVIDIA qwen/qwen2.5-72b-instruct Failed:", e)

# Test Gemini
print("\nTesting Gemini...")
try:
    api_key = os.getenv("GEMINI_API_KEY_1") or os.getenv("GOOGLE_API_KEY_1")
    client = genai.Client(api_key=api_key)
    for model in client.models.list():
        if "generateContent" in (model.supported_actions or []):
            print(model.name)
    client.close()
except Exception as e:
    print("Gemini Failed:", e)
