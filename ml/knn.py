"""
This file gets all places, likes and users from Parse server so that it can recommend a place to a user according to its likes
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join('..')))

from parse import Place, User
from urllib.parse import urlencode
import requests as r
from dotenv import dotenv_values
import json
import random

import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

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
        _places = response.json().get("results", [])
        
        for i, _place in enumerate(_places):
            place = Place(_place, simple=True)
            result.setdefault(place.objectId, place)
        
    return result


def get_likes(user: str, only_place: bool = False) -> list:
    """Get all likes from Parse server to create the dataset filtering only the ones for a specific user

    Returns:
        list: All likes of a user
    """
    global SECRETS, PARSE_SERVER_URL, HEADERS
    result = []
    
    constraint = {
        "where": json.dumps({
            "user": {
                "__type": "Pointer",
                "className": "_User",
                "objectId": user
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
            if not only_place:
                result.append({
                    "user": _like["user"]["objectId"],
                    "place": _like["place"]["objectId"]
                })
            else:
                result.append(_like["place"]["objectId"])
        
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
    
    for i, _user in enumerate(results):
        user = User(_user)
        _users.setdefault(user.objectId, user)
    
    return _users
    

def create_dataset():
    """
    Creates the dataset and saves it as csv to read later
    """
    # Get values    
    places = get_all_places()
    users = get_all_users()

    likes = []
    for user in users.values():
        likes.extend(get_likes(user.objectId))

    # Create DataFrame
    data = pd.DataFrame()

    # Create colums in DataFrame
    for user in users.keys():
        data.insert(0, users[user].objectId, int(0))

    # Create rows in DataFrame
    values = [0 for _ in range(len(users))]
    for place in places.keys():
        data.loc[place] = values

    # Fill data about likes
    for like in likes:
        data.loc[like["place"], like["user"]] = 1

    # Convert DataFrame to .csv format
    data.to_csv('/Users/pabloblanco/Desktop/Places/server/ml/likes.csv', index_label='places')


def read_data() -> pd.DataFrame:
    """Reads the data stored from a .csv file and returns it's DataFrame

    Returns:
        pd.DataFrame: All data in order to create the model
    """
    return pd.read_csv("/Users/pabloblanco/Desktop/Places/server/ml/likes.csv", index_col="places").T
    
    
def create_model() -> NearestNeighbors:
    """Creates and fits the model to the existing data

    Returns:
        NearestNeighbors: The model fitted ready to predict for a user
    """
    # Get data from .csv
    data = read_data()
    
    # Create KNN model
    model = NearestNeighbors(metric='cosine', n_neighbors=5, algorithm='brute', n_jobs=-1)
    model.fit(data)
    
    return model


def kNearestNeighbors() -> pd.DataFrame:
    """Get a DataFrame with the K nearest neighbors for each user
    
    Returns:
        pd.DataFrame: The KNN for each user so that it can be compared and recommend a place
    """
    data = read_data()
    model = create_model()

    # Get top k neighbors indexes
    # Get knn uids from indexes
    top_k_users = model.kneighbors(data, return_distance=False)
    neighbors = pd.DataFrame(np.array(top_k_users))
    
    return neighbors


def recommend(neighbors: pd.DataFrame, data: pd.DataFrame, user: str) -> list:
    """Recommends a place to a user according to similar users

    Args:
        user (str): The user id of the one making the request
        neighbors (DataFrame): The knn of each user
        data (DataFrame): The whole data

    Returns:
        list: The top 5 items (or less) to recommend to the user
    """
    # Get the 4 users that relate most to the user
    knn_index = list(neighbors.iloc[list(data.index).index(user)][1:])
    knn = [list(data.index)[x] for x in knn_index]
    
    # Get places the user has liked
    liked_by_user = []
    for index, value in data.loc[user, :].items():
        if value == 1:
            liked_by_user.append(index)
    
    # Get places liked by related users
    liked = []
    for _user in knn:
        
        # Find a place that the user hasn't liked and add it to the list
        for index, value in data.loc[_user, :].items():
            if value == 1 and index not in liked_by_user and len(liked) < 5:
                liked.append(index)
        
    # If no place to recommend then choose random        
    while len(liked) == 0:
        _place = random.choice(data.columns)
        if _place not in liked_by_user:
            liked.append(_place)
        
    return liked

