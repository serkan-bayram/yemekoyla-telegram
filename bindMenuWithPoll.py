import requests
import json

# using token's only purpose is authenticate it's really us
# who is making that post request to our api endpoint
# still i'm not very sure is it the right way of doing this

# updates last menu entry's pollId
def bindMenuWithPoll(pollId, token, API_URL):
    url = f"{API_URL}/bindMenuWithPoll"
    
    data = {
        "pollId": pollId,
        "token": token
    }

    json_string = json.dumps(data)  

    response = requests.post(url, json = json_string)
    

