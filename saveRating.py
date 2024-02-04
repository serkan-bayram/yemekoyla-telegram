import json
import requests

def saveRating(pollId, votedBy, isVoted, votedOption, API_URL, TOKEN):
    url = f"{API_URL}/saveRating"
    
    data = {
        "pollId": pollId,
        "votedBy": votedBy,
        "isVoted": isVoted,
        "votedOption": votedOption + 1 if votedOption != None else None,
        "token": TOKEN
    }

    json_string = json.dumps(data)

    response = requests.post(url, json = json_string)
    
    print("Response from /saveRating: ", response.json())


    if "error" in response.json():
        error = response.json()["error"]
        if error == "userHasNotFound":
            return "Değerlendirmeniz kaydedilmedi, yemeklerin iyileşmesine yardımcı olmak için lütfen sitemize kaydolun. ☺️"
        return "Değerlendirmeniz kaydedilemedi, lütfen daha sonra tekrar deneyin."

    return "Değerlendirmeniz kaydedildi! Teşekkürler. ☺️"
