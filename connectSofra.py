import requests

def connectSofra(username, password):
    url = "https://sofra.bilecik.edu.tr/OturumAc"

    session = requests.Session()

    data = {"KullaniciAd": username, "Parola": password}

    response = session.post(url, data = data)

    if response.json():
        return session
    else:
        return False