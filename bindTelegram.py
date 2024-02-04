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

    print("Response from /bindTelegram: ", response.json())

    if "error" in response.json():
        error = response.json()["error"]
        if error == "userHasNotFound":
            return "Bu kullanıcı Yemekoyla'ya kayıtlı değil gibi gözüküyor.\nBüyük küçük harfe dikkat ettiğinizden emin olunuz."
        if error == "alreadyVerified":
            return "Hesabınızı zaten bağlamışsınız. ☺️\n\nBir hata olduğunu düşünüyorsanız lütfen Admin ile iletişime geçiniz."


    return f"Doğrulama Kodunuz: {response.json()['code']}"