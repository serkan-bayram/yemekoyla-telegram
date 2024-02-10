import requests
import json

def getBalanceUsers(token, API_URL):
    url = f"{API_URL}/getBalanceUsers"

    data = {
        "token": token
    }

    json_string = json.dumps(data)  

    response = requests.post(url, json = json_string)

    users = []

    for user in response.json()["users"]:
        users.append(user)

    return users
