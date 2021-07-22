from parse import Place, User
import requests as r
from dotenv import dotenv_values
from requests.models import HTTPError
import json

# Constants
SECRETS = dotenv_values(".env")
PARSE_SERVER_URL = SECRETS.get("PARSE_API_ADDRESS")
HEADERS = {
    "X-Parse-Application-Id": SECRETS.get("PARSE_APP_ID"),
    "X-Parse-REST-API-Key": SECRETS.get("PARSE_REST_API_KEY"),
    "Content-Type": "application/json"
    }

def get_all_users():
    """
    Gets all users from Parse backend
    """
    global SECRETS, PARSE_SERVER_URL, HEADERS
    
    url = PARSE_SERVER_URL + "/parse/users"
    
    response  = r.get(url=url, headers=HEADERS)
    if response.status_code != 200:
        raise HTTPError("Invalid response: " + str(response.status_code))
    
    results = response.json().get("results", [])
    _users = []
    for result in results:
        _users.append(User(result))
    
    return _users

users = get_all_users()
for user in users:
    url = PARSE_SERVER_URL + "/parse/classes/Relations"
    obj = {
        "user": {
                "__type": "Pointer",
                "className": "_User",
                "objectId": f"{user.objectId}"
        },
        "followerCount": 0,
        "followingCount": 0
    }
    response = r.post(url, data=json.dumps(obj), headers=HEADERS)
    print(f"{response.status_code}: {user.name}")