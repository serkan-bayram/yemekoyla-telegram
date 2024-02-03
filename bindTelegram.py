import requests
import json

def bindTelegram(telegramId, username, API_URL, TOKEN):
    url = f"{API_URL}/bindTelegram"

    data = {
        "telegramId": telegramId,
        "username": username,
        "token": TOKEN
    }

    json_string = json.dumps(data)

    response = requests.post(url, json = json_string)

    if "error" in response.json():
        error = response.json()["error"]
        if error == "userHasNotFound":
            return "Bu kullanıcı Yemekoyla'ya kayıtlı değil gibi gözüküyor.\nBüyük küçük harfe dikkat ettiğinden emin ol."

    return f"Doğrulama Kodunuz: {response.json()['code']}"