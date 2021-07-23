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


def get_places():
    """
    Returns the list of places to be created
    """
    _places = {
        "italian": [],
        "japanese": [],
        "drinks": [],
        "coffee": [],
        "burgers": []
    }
    
    with open('places.json', "r") as file:
        data = json.load(file)
        
        __places = {
            "italian": data["italian"],
            "japanese": data["japanese"],
            "drinks": data["drinks"],
            "coffee": data["coffee"],
            "burgers": data["burgers"]
        }
        
        for key, places_list in __places.items():
            for place in places_list:
                place.setdefault("likeCount", 0)
                place.setdefault("phoneNumber", "+523339675554")
                _places[key].append(place)
                
    return _places
        


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
places = get_places()

for i, user in enumerate(users):
    places_to_upload = []
    for places_list in places.values():
        place = places_list[i]
        place["user"]["objectId"] = user.objectId
        places_to_upload.append(place)

    for place in places_to_upload:
        response = r.post(PARSE_SERVER_URL + "/parse/classes/Place", data=json.dumps(place), headers=HEADERS)
        print(f"{response.status_code}: {place['name']}")