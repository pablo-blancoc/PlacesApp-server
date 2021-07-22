from parse import User
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
RELATIONS = {}


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


def get_relations():
    """
    Gets the id of the relation where the user is
    """    
    url = PARSE_SERVER_URL + "/parse/classes/Relations"
    response = r.get(url, headers=HEADERS)
    if not 200 <= response.status_code <= 299:
        print("COULD NOT GET RELATIONS")
        return
    
    return response.json()["results"]


def get_key(uid):
    global RELATIONS
    for relation in RELATIONS:
        if relation["user"]["objectId"] == uid:
            return relation["objectId"]
    
    return "0"
         

RELATIONS = get_relations()
users = get_all_users()
for user in users:
    toFollow = random.sample(users, 10)
    for following in toFollow:
        # Create Follower object and save it
        url = PARSE_SERVER_URL + "/parse/classes/Follower"
        obj = {
            "follower": {
                    "__type": "Pointer",
                    "className": "_User",
                    "objectId": f"{user.objectId}"
            },
            "following": {
                    "__type": "Pointer",
                    "className": "_User",
                    "objectId": f"{following.objectId}"
            }
        }
        response = r.post(url, data=json.dumps(obj), headers=HEADERS)
        if response.status_code not in (200, 201):
            print("COULD NOT CREATE FOLLOWER OBJECT")
            sys.exit(7)
        else:
            print(f"{user.name} follows {following.name}")
        
        # Increment followerCount on Parse server
        url = PARSE_SERVER_URL + f"/parse/classes/Relations/{get_key(following.objectId)}"
        obj = {
            "followerCount": {
                "__op": "Increment",
                "amount": 1,
            }
        }
        response = r.put(url, data=json.dumps(obj), headers=HEADERS)
        if not 200 <= response.status_code <= 299:
            print("COULD NOT UPDATE FOLLOWER COUNT")
            print(response.json())
            sys.exit(7)
        
        # Increment followingCount on Parse server
        url = PARSE_SERVER_URL + f"/parse/classes/Relations/{get_key(user.objectId)}"
        obj = {
            "followingCount": {
                "__op": "Increment",
                "amount": 1
            }
        }
        response = r.put(url, data=json.dumps(obj), headers=HEADERS)
        if not 200 <= response.status_code <= 299:
            print("COULD NOT UPDATE FOLLOWING COUNT")
            print(response.json())
            sys.exit(7)