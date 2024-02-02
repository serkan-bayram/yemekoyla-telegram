import json
import requests

def saveRating(pollId, votedBy, isVoted, votedOption, API_URL, TOKEN):
    url = f"{API_URL}/saveRating"
    
    data = {
        "pollId": pollId,
        "votedBy": votedBy,
        "isVoted": isVoted,
        "votedOption": votedOption + 1,
        "token": TOKEN
    }

    json_string = json.dumps(data)

    requests.post(url, json = json_string)


