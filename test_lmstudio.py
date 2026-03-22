import requests
import json

# LMStudio endpoint
API_URL = "http://localhost:1234/api/v1/chat"

# Test Message
payload = {
   "model": "l3-8b-stheno-v3.2-iq-imatrix",
   "input": "Say hello!"
}

# Try the requests
try:
    response = requests.post(API_URL, json=payload)
    print("Status Code:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", e)

