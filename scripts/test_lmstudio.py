import requests

API_URL = "http://localhost:1234/api/v1/chat"
REQUEST_TIMEOUT_S = 120

payload = {
    "model": "l3-8b-stheno-v3.2-iq-imatrix",
    "input": "Say hello!",
}

if __name__ == "__main__":
    try:
        response = requests.post(
            API_URL, json=payload, timeout=REQUEST_TIMEOUT_S
        )
        print("Status Code:", response.status_code)
        print("Response:", response.json())
    except Exception as e:
        print("Error:", e)
