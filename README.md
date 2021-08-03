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

___

### Sanity check
**Request**
```GET /``` 

**Response**
- ```200: "Working!"```

This is just a sanity check to confirm the server is working and can be accessed from another device. It returns a simple string.

___

### Send push notifications
**Request**
```GET /push``` 

**Parameters**
- **user**: The objectId from the user that posted a new place
- **place**: The objectId of the place that was posted

**Response**
- ```200```: Push notifications that needed to be sent where sent
- ```400```: Either the place or the user are missing from the request
- ```401```: API KEY is missing

When this endpoint is called correctly, it will retrieve all the information from the user and the place passed. Then it will get all the information of the users that have opted-in to receive notifications from the user that just posted the place. Then the list will be filtered to only get the users that actually have a phone able to get notifications using OneSignal's tools, and a notifications is going to be sent to all of them. If the notification is clicked it is going to display the detailed information of the place that was posted.

___

### Recommendation System
**Request**
```GET /recommend``` 

**Parameters**
- **user**: The objectId from the user that posted a new place

**Response**
- ```200```: The places where recommended succesfully
- ```400```: The user is missing from the request
- ```401```: API KEY is missing

When the endpoint is called correctly, it will retrieve all the information of the users and what places has each user liked. Also, it will retrieve the information of the places. It will then use the k nearest-neighbors algorithm using cosine similarity to find the 4 most similar users to you. From this 4 users, the server is going to recommend up to 5 places that these users have liked you haven't yet.  

**Return object (HTTP status code: 200)**
```
{
    "places": [
        <list of strings representing objectId's from Parse Place class>
    ]
}
```
___

### Search for places using TF-IDF and cosine similarity
**Request**
```GET /search``` 

**Parameters**
- **query**: The string the user wrote as search query

**Response**
- ```200```: The search was made succesfully
- ```400```: The query is missing from the request
- ```401```: API KEY is missing

When this endpoint is called correctly, it will create a vector from the query sent using all *x* values to be each word from the total bag of words that we have from the places and the values being the *tf-idf* value from each word. Then it will iterate all places vector and using cosine similarity algorithm it will find the top 10 places query best matches.It will then return a list of the objectId's from these 10 places.  

**Return object (HTTP status code: 200)**
```
{
    "places": [
        <list of strings representing objectId's from Parse Place class>
    ]
}
```
___

## Links

[Main repository of Places App project](https://github.com/pablo-blancoc/PlacesApp)

[ML repository of Places](https://github.com/pablo-blancoc/PlacesApp-ml)


