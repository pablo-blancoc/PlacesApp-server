"""
-- How the recommend algorithm works?

1. First we use knn algorithm to get the 10 most similar places (according to likes, which means it is based on user preferences).
2. After getting the 10 most similar places, we rank all users in order from who has liked the most out of those 10 places, 
    and select the top 5 users.
3. This means that at the end, we have found the users that are most probable to liking the place to recommend because 
    they have liked the most out of the 10 most similar places to it.
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join('..')))

from sklearn.neighbors import NearestNeighbors
import pandas as pd
import numpy as np
import requests as r
from dotenv import dotenv_values
import json

# Constants
SECRETS = dotenv_values(".env")
PARSE_SERVER_URL = SECRETS.get("PARSE_API_ADDRESS")
HEADERS = {
    "X-Parse-Application-Id": SECRETS.get("PARSE_APP_ID"),
    "X-Parse-REST-API-Key": SECRETS.get("PARSE_REST_API_KEY"),
    "Content-Type": "application/json"
    }

# Read data
DATA = pd.read_csv("/Users/pabloblanco/Desktop/Places/server/ml/likes.csv", index_col="places")

# Create KNN model and train it
MODEL = NearestNeighbors(metric='cosine', n_neighbors=11, algorithm='brute', n_jobs=-1)
MODEL.fit(DATA)

# Find most similar places of each place
neighbors = pd.DataFrame(np.array(MODEL.kneighbors(DATA, return_distance=False)))


def get_best_users(place: str, user: str) -> list:
    """Gets a list of the 5 best users to promote a place given

    Args:
        place (str): The objectId of the place given
        user (str): The objectId of the user that created the promotion

    Returns:
        list: A list that contains the 5 users that are the best to promote a place to
    """
    global DATA

    # Get the 10 places that are most similar to the place passed
    knn = [list(DATA.index)[x] for x in list(neighbors.iloc[list(DATA.index).index(place)][1:])]
    
    # Get the information of the likes of all users on those 10 places
    likes = DATA.loc[knn, :]
    
    # Sum all likes per user on those 10 places
    likes_per_user = likes.astype(bool).sum(axis=0)
    
    # Rank the users in order of how many likes the have given, and get the top 5
    best_users = list(likes_per_user.sort_values(ascending=False).index)
    print(best_users)
    best_users.remove(user)[:5]
    print(best_users)
    
    return best_users


def promote(place: str, user: str) -> bool:
    """Promotes a place given

    Args:
        place (str): The place to promote
        user (str): The user that is making the promotion
        
    Returns:
        bool: if promotion was succesfull
    """
    # Set url
    url = PARSE_SERVER_URL + "/parse/classes/Promotion"
    
    # Gets users to promote to
    users = get_best_users(place=place, user=user)
    
    # Create Promotion class object
    promotion = {
        "place": {
            "__type": "Pointer",
            "className": "Place",
            "objectId": place
        },
        "user": {
            "__type": "Pointer",
            "className": "_User",
            "objectId": user
        },
        "viewed": 0,
        "sent": len(users),
        "clicked": 0
    }
    response = r.post(url, data=json.dumps(promotion), headers=HEADERS)
    if not 200 <= response.status_code <= 299:
        return False
    
    print(response.json())

