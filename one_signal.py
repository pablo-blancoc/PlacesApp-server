from dotenv import dotenv_values
import requests as r
import json

URL = "https://onesignal.com/api/v1/notifications"
SECRETS = dotenv_values(".env")
APP_ID = SECRETS.get("ONE_SIGNAL_APP_ID")
HEADERS = {
    "Content-Type": "application/json"
    }


def push(place: str, toUsers: list, title: str, text: str) -> None:
    """Send a push notification using OneSignals services

    Args:
        place (str): The placeId that goes binded to the notification
        toUsers (list): The list of users to send the notification to
        title (str): The title of the notification
        text (str): The text of the notification
    """
    global APP_ID, URL, HEADERS
    
    payload = {
        "app_id": APP_ID,
        "include_player_ids": toUsers,
        "data": 
            {
                "place": place
            },
        "contents": 
            {
                "en": text,
            },
        "headings": 
            {
                "en": title
            }
    }
    
    r.post(url=URL, headers=HEADERS, data=json.dumps(payload))
