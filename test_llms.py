import os
from openai import OpenAI
from dotenv import load_dotenv
import google.generativeai as genai

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
    genai.configure(api_key=os.getenv("GEMINI_API_KEY_1"))
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print("Gemini Failed:", e)
