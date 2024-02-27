import requests
import json


def getUserBalances(token, API_URL):
    url = f"{API_URL}/getUserBalances"

    data = {
        "token": token
    }

    json_string = json.dumps(data)

    response = requests.post(url, json=json_string)

    users = []

    for user in response.json()["users"]:
        users.append(user)

    return users
