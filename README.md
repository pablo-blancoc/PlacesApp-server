# FBU App: Places Backend Server

## Table of Contents
1. [Overview](#overview)
    * [Description](#description)
2. [Documentation](#documentation)
3. [Important links](#links)

## Overview

### Description
The purpose of the backend server, even though right now is being run on a local machine, is to run the functions that should not be run on the app but help the app accomplish all user stories. It tries to represent what a real production server would do. 

There are two functions this server runs:
- Send notifications to users that have opted-in when a user posts a new place
- Run the recommendation system that lets a user get recommended a place when requested*

\* Not yet implemented

## Documentation

### Sanity check
**Request**
```GET /``` 

**Response**
- ```200: "Working!"```

This is just a sanity check to confirm the server is working and can be accessed from another device. It returns a simple string.


### Send push notifications
**Request**
```GET /push``` 

**Parameters**
- **user**: The objectId from the user that posted a new place
- **place**: The objectId of the place that was posted

**Response**
- ```200```: Push notifications that needed to be sent where sent
- ```400```: Either the place or the user are missing from the request

When this endpoint is called correctly, it will retrieve all the information from the user and the place passed. Then it will get all the information of the users that have opted-in to receive notifications from the user that just posted the place. Then the list will be filtered to only get the users that actually have a phone able to get notifications using OneSignal's tools, and a notifications is going to be sent to all of them. If the notification is clicked it is going to display the detailed information of the place that was posted.

## Links

[Main repository of Places App project](https://github.com/pablo-blancoc/PlacesApp)

[ML repository of Places](https://github.com/pablo-blancoc/PlacesApp-ml)

