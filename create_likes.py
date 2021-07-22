from parse import User, Place
import requests as r
from dotenv import dotenv_values
from requests.models import HTTPError
import json
import random
import sys
from urllib.parse import urlencode

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


def get_all_places():
    """
    Gets all places from Parse backend
    """
    global SECRETS, PARSE_SERVER_URL, HEADERS
    
    url = PARSE_SERVER_URL + "/parse/classes/Place"
    
    response  = r.get(url=url, headers=HEADERS)
    if response.status_code != 200:
        raise HTTPError("Invalid response: " + str(response.status_code))
    
    results = response.json().get("results", [])
    _places = []
    for result in results:
        _places.append(Place(result))
    
    return _places


places = get_all_places()
users = get_all_users()
for user in users:
    toLike = random.sample(places, 45)
    for place in toLike:
        # Create like object and save it
        url = PARSE_SERVER_URL + "/parse/classes/Like"
        obj = {
            "user": {
                    "__type": "Pointer",
                    "className": "_User",
                    "objectId": f"{user.objectId}"
            },
            "place": {
                    "__type": "Pointer",
                    "className": "Place",
                    "objectId": f"{place.objectId}"
            }
        }
        response = r.post(url, data=json.dumps(obj), headers=HEADERS)
        if response.status_code not in (200, 201):
            print("COULD NOT CREATE LIKE OBJECT")
            sys.exit(7)
        else:
            print(f"{user.name} likes {place.name}")
        
        # Increment likeCount on Place class on Parse server
        url = PARSE_SERVER_URL + f"/parse/classes/Place/{place.objectId}"
        obj = {
            "likeCount": {
                "__op": "Increment",
                "amount": 1,
            }
        }
        response = r.put(url, data=json.dumps(obj), headers=HEADERS)
        if not 200 <= response.status_code <= 299:
            print("COULD NOT UPDATE LIKE COUNT")
            print(response.json())
            sys.exit(7)
