"""
This file is intended to create a .csv dataset that contains all the information from all the places that have been liked by all the users.
This is going to lates be used to create a knn model to recommend places to users
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join('..')))

from requests.models import HTTPError
from parse import Place, get_user, get_place, User
import requests as r
from dotenv import dotenv_values
import json
from urllib.parse import urlencode

import pandas as pd
import numpy as np

# Constants
SECRETS = dotenv_values("/Users/Pablo/Desktop/dev/projects/Places/server/.env")
PARSE_SERVER_URL = SECRETS.get("PARSE_API_ADDRESS")
HEADERS = {
    "X-Parse-Application-Id": SECRETS.get("PARSE_APP_ID"),
    "X-Parse-REST-API-Key": SECRETS.get("PARSE_REST_API_KEY")
    }


def get_all_places() -> dict:
    """Gets all places and creates a dict from them so that each place can be retrieved by its objectId

    Returns:
        dict: All places
    """
    global SECRETS, PARSE_SERVER_URL, HEADERS
    result = {}
    
    url = PARSE_SERVER_URL + f"/parse/classes/{Place.class_name}"
    
    response  = r.get(url=url, headers=HEADERS)
    
    if response.status_code != 200:
        print("Request on places could not be completed")
        exit(1)
    
    else:
        print("PLACES:")
        _places = response.json().get("results", [])
        
        for i, _place in enumerate(_places):
            place = Place(_place)
            result.setdefault(place.objectId, place)
            print(f"{i+1}/{len(_places)}")
        
    return result


def get_likes(user: User) -> list:
    """Get all likes from Parse server to create the dataset

    Returns:
        list: All likes
    """
    global SECRETS, PARSE_SERVER_URL, HEADERS
    result = []
    
    constraint = {
        "where": json.dumps({
            "user": {
                "__type": "Pointer",
                "className": "_User",
                "objectId": user.objectId
            }
        })
    }
    
    url = PARSE_SERVER_URL + "/parse/classes/Like?" + urlencode(constraint)
    
    response  = r.get(url=url, headers=HEADERS)
    
    if response.status_code != 200:
        print("Request on likes could not be completed")
        print(response.json())
        exit(1)
    
    else:
        _likes = response.json().get("results", [])
        for _like in _likes:
            result.append({
                "user": _like["user"]["objectId"],
                "place": _like["place"]["objectId"]
            })
        
    return result


def get_all_users():
    """
    Gets all users from Parse backend
    """
    global SECRETS, PARSE_SERVER_URL, HEADERS
    
    url = PARSE_SERVER_URL + "/parse/users"
    
    response  = r.get(url=url, headers=HEADERS)
    if response.status_code != 200:
        print("Invalid response on GET likes: " + str(response.status_code))
    
    results = response.json().get("results", [])
    _users = {}
    print("USERS: ")
    
    for i, _user in enumerate(results):
        user = User(_user)
        _users.setdefault(user.objectId, user)
        print(f"{i+1}/{len(results)}")
    
    return _users
    

# Get values    
places = get_all_places()
users = get_all_users()

likes = []
for user in users.values():
    likes.extend(get_likes(user))

print(f"Total number of likes: {len(likes)}")

# Create DataFrame
df = pd.DataFrame()

# Create colums in DataFrame
for user in users.keys():
    df.insert(0, users[user].objectId, int(0))
    
# Create rows in DataFrame
values = [0 for _ in range(len(users))]
print(values)
for place in places.keys():
    df.loc[place] = values
    
# Fill data about likes
for like in likes:
    df.loc[like["place"], like["user"]] = 1
    
df.to_csv('/Users/Pablo/Desktop/dev/projects/Places/server/ml/likes.csv', index_label='places')
