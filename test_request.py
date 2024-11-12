import requests

url = "http://localhost:5000/chat"
payload = {
    "user_id": "12345eferequesttest",
    "user_first_name": "John",
    "char_name": "Cleo",
    "message": "how are you!"
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())