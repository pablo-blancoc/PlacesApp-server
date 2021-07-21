from dateutil.parser import parser
from requests.models import HTTPError
from urllib.parse import urlencode
import json
import requests as r
from dotenv import dotenv_values

# Constants
SECRETS = dotenv_values(".env")
PARSE_SERVER_URL = SECRETS.get("PARSE_API_ADDRESS")
HEADERS = {
    "X-Parse-Application-Id": SECRETS.get("PARSE_APP_ID"),
    "X-Parse-REST-API-Key": SECRETS.get("PARSE_REST_API_KEY")
    }


class User:
    class_name = "_User"
    
    def __init__(self, user: dict) -> None:
        try:
            self.objectId = user["objectId"]
            self.name = user["name"]
            self.createdAt = parser(user["createdAt"])
            self.updatedAt = parser(user["updatedAt"])
            self.bio = user["bio"]
            self.profilePicture = Image(user["profilePicture"])
            self.OneSignal = user["OneSignal"]
            
        except KeyError:
            raise ValueError("User could not be created:\n" + str(user))
        
        
class Image:
    def __init__(self, image: dict) -> None:
        try:
            self.type = image["__type"]
            self.name = image["name"]
            self.url = image["url"]
            
        except KeyError:
            raise ValueError("Image could not be created:\n" + str(image))
        
        
class Place:
    class_name = "Place"
    
    def __init__(self, place: dict) -> None:
        try:
            # Values
           self.objectId = place["objectId"]
           self.address = place["address"]
           self.phoneNumber = place["phoneNumber"]
           self.public = place["public"]
           self.price = place["price"]
           self.name = place["name"]
           self.description = place["description"]
           self.likeCount = place["likeCount"]
           self.createdAt = parser(place["createdAt"])
           self.updatedAt  = parser(place["updatedAt"])
           
           # Pointers
           self.location = GeoPoint(place["location"])
           self.image = Image(place["image"])
           self.category = get_category(place["category"]["objectId"])
           self.user = get_user(place["user"]['objectId'])
            
        except KeyError:
            raise ValueError("Place could not be created:\n" + str(place))
        
    
class GeoPoint:
    class_name = "GeoPoint"
    
    def __init__(self, values: dict) -> None:
        try:
            self.latitude = values["latitude"]
            self.longitude = values["longitude"]
            
        except KeyError:
            raise ValueError("GeoPoint could not be created:\n" + str(values))
        
        
class Category:
    class_name = "Category"
    
    def __init__(self, values: dict) -> None:
        try:
            self.createdAt = parser(values["createdAt"])
            self.updatedAt  = parser(values["updatedAt"])
            self.objectId = values["objectId"]
            self.name = values["name"]
            
        except KeyError:
            raise ValueError("Category could not be created:\n" + str(values))
        
        
class Subscription:
    class_name = "Notification"
    
    def __init__(self, values: dict) -> None:
        try:
            self.createdAt = parser(values["createdAt"])
            self.updatedAt  = parser(values["updatedAt"])
            self.objectId = values["objectId"]
            self.toUser = get_user(values["to"]["objectId"])
            self.fromUser = get_user(values["from"]["objectId"])
            
        except KeyError:
            raise ValueError("Category could not be created:\n" + str(values))
        
        
def get_user(objectId: str) -> User or None:
    """Retrieves a user from Parse server

    Args:
        objectId (str): The objectId from the user

    Returns:
        User: The information of the user
        None: if no user was retrieved
    """
    
    url = f"/parse/users/{objectId}"
    
    return _get(endpoint=url, T=User)
    

def get_place(objectId: str) -> Place or None:
    """Retrieves a place from Parse server backend

    Args:
        objectId (str): The objectId of the place that wants to be retrieved

    Returns:
        Place: The place retrieved
        None: if no place could be retrieved
    """
    url = f"/parse/classes/{Place.class_name}/{objectId}"
    
    return _get(endpoint=url, T=Place)
    
    
def get_category(objectId: str) -> Category or None:
    """Retrieves a category from Parse server

    Args:
        objectId (str): The objectId from the category

    Returns:
        Category: The information of the category
        None: if no category was retrieved
    """
    url = f"/parse/classes/{Category.class_name}/{objectId}"
    
    return _get(endpoint=url, T=Category)
    

def _get(endpoint: str, T: object):
    """Retrieve object from Parse server

    Args:
        endpoint (str): The specific endpoint to call
    """
    global SECRETS, PARSE_SERVER_URL, HEADERS
    
    url = PARSE_SERVER_URL + endpoint
    
    response  = r.get(url=url, headers=HEADERS)
    
    if response.status_code == 200:
        return T(response.json())
    else:
        raise HTTPError("Request not completed")
    

def get_subscriptions(user: User) -> list:
    """Gets all the users that have subscribed to certain user

    Args:
        user (User): The user who was subscripted to

    Returns:
        list: List of users
    """
    global SECRETS, PARSE_SERVER_URL, HEADERS
    
    query = { 
            "where": 
                json.dumps({
                    "from": 
                        {
                            "__type": "Pointer",
                            "className": User.class_name,
                            "objectId": user.objectId
                        }
                })
            }
    
    url = PARSE_SERVER_URL + f"/parse/classes/{Subscription.class_name}?" + urlencode(query)
    response  = r.get(url=url, headers=HEADERS)
    
    if response.status_code == 200:
        result = []
        
        subs = response.json()["results"]
        for sub in subs:
            try:
                result.append(Subscription(sub))
            except KeyError as e:
                print(e)
                
    else:
        raise HTTPError("Get subscriptions not completed")

    return result