import requests
import json

url = "http://localhost:8000/chat"
payload = {
    "message": "quem é o rafael?",
    "history": [],
    "lang": "pt"
}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers)
    print("Status:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", e)
