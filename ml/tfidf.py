"""
This document is based on the Jupyter Notebook of the same name. The concepts and function, as well as the explanation can be found 
    on the Jupyter Notebook. In this file the functions are put together in order to get a working function that performs search on all places.
    Later, this function is going to be put into an endpoint so that it can be called from the app.
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join('..')))

import json
from collections import Counter
from urllib.parse import urlencode
import requests as r
from dotenv import dotenv_values
from parse import Place

import numpy as np

import nltk

# NLTK neccesary downloads
# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('wordnet')

from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
stop_words = set(stopwords.words('english'))
stop_words_es = set(stopwords.words('spanish'))
from nltk.corpus import wordnet

# Constants
lemmatizer = WordNetLemmatizer()
SECRETS = dotenv_values("/Users/pabloblanco/Desktop/Places/server/.env")
PARSE_SERVER_URL = SECRETS.get("PARSE_API_ADDRESS")
HEADERS = {
    "X-Parse-Application-Id": SECRETS.get("PARSE_APP_ID"),
    "X-Parse-REST-API-Key": SECRETS.get("PARSE_REST_API_KEY")
    }


# Create places .json so data can be accesed faster
def get_all_places() -> dict:
    """Gets all places and creates a dict from them so that each place can be retrieved by its objectId

    Returns:
        dict: All places
    """
    global SECRETS, PARSE_SERVER_URL, HEADERS
    result = []
    
    url = PARSE_SERVER_URL + f"/parse/classes/{Place.class_name}"
    
    response  = r.get(url=url, headers=HEADERS)
    
    if response.status_code != 200:
        print("Request on places could not be completed")
        exit(1)
    
    else:
        _places = response.json().get("results", [])
        
        for i, _place in enumerate(_places):
            place = Place(_place, simple=True)
            result.append({
                "id": place.objectId,
                "name": place.name,
                "description": place.description
                })
            
    
    with open("places.json", "w") as file:
        json.dump({"places": result}, file)
        

def read_all_places():
    """
    Reads all places from json file and creates dict object containing them
    """
    places_file = "/Users/pabloblanco/Desktop/Places/server/ml/places.json"
    data = {}
    
    with open(places_file) as file:
        data = json.load(file)
        
    places = data["places"]
        
    return places


def get_wordnet_pos(treebank_tag: str):
    """Returns the name of the tag for a WordNet TreeBank tag

    Args:
        treebank_tag (str): The tag of a word

    Returns:
        [any]: The name of the tag proccesable for NLTK
    """
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None
    

def preprocess_sentence(sentence: str) -> list:
    """Preprocess a sentence by next steps:
        1. Getting tokens
        2. Turning them to lower case
        3. Removing stopwords (english and spanish)
        4. Removing punctuation
        5. Removing one letter words
        6. Lemmatizing the words to get root

    Args:
        sentence (str): [description]

    Returns:
        list: [description]
    """ 
    tokens = word_tokenize(sentence)
    words = nltk.pos_tag(tokens)
    
    final = []
    punctuation = "!\"#$%&()*+-./:;<=>?@[\]^_`{|}~\n'"
    
    for word, tag in words:
        # lowercase
        word = word.lower()
        
        # remove stopwords
        if word in stop_words or word in stop_words_es:
            continue
            
        # remove punctuation
        for letter in punctuation:
            word = word.replace(letter, "")
        
        # remove one-letter words
        if len(word) <= 1:
            continue
        
        # lemmatize word
        pos = get_wordnet_pos(tag)
        if pos is None:
            continue
            
        word = lemmatizer.lemmatize(word, pos)
        
        final.append(word)
    
    return final


def doc_freq(word: str) -> int:
    """Gets the document frequency using the dictionary made globally

    Args:
        word (str): The word

    Returns:
        int: The document frequency of that word
    """
    global df
    
    freq = 0
    try:
        freq = df[word]
    except KeyError:
        pass
    return freq


def matching_score(query: str) -> list:
    """Gets a text as a query and finds the top 10 places that have top tf-idf values for that query

    Args:
        query (str): The text entered by user as query

    Returns:
        list: The list of places that match the query
    """
    global tf_idf
    
    # Preprocess the query
    tokens = preprocess_sentence(query)
    
    query_weights = {}

    # For each word in each document
    for key in tf_idf:
        
        # If word in query, add document's value to query_weights
        if key[1] in tokens:
            try:
                query_weights[key[0]] += tf_idf[key]
            except:
                query_weights[key[0]] = tf_idf[key]
    
    # Sort the weights to get highers on top
    query_weights = sorted(query_weights.items(), key=lambda x: x[1], reverse=True)
    
    # Get only index in places list
    results = []
    for i in query_weights[:10]:
        results.append(i[0])
    
    return results

    
# Get all places and preprocess them
places = read_all_places()
for place in places:
    place["name"] = preprocess_sentence(place["name"])
    place["description"] = preprocess_sentence(place["description"])
    
    
# Create dictionary of document frequency with ids of documents
df = {}
for i in range(len(places)):
    tokens = places[i]["description"]
    tokens.extend(places[i]["name"])
    for w in tokens:
        try:
            df[w].add(i)
        except KeyError:
            df[w] = {i}

# Get only the frequency of appearance of each word
for word in df.keys():
    df[word] = len(df[word])
    
# Create variables neccessary for tf-idf
total_vocab = df.keys()
total_vocab_size = len(total_vocab)
N = len(places)

# Create variables to store tf-idf values of each word in both, title and text
# Alpha is set to 0.3 as words in title will be more valuable (0.7) than words in description (0.3)
tf_idf_text = {}
tf_idf_title = {}
alpha = 0.3

# for each place calculate tf-idf for description
for i, place in enumerate(places):
    
    # get tokens of that place
    tokens = place["description"]

    # get word counts per document and total words
    counter = Counter(tokens)
    words_count = len(tokens)
    
    # for each word in document
    for token in np.unique(tokens):    
        
        # get term-frequency
        tf = counter[token]/words_count
        
        # get inverse document frequency
        idf = np.log(N/(doc_freq(token)+1))
        
        tf_idf_text[i, token] = tf*idf * alpha
        

# for each place calculate tf-idf for title
for i, place in enumerate(places):
    
    # get tokens of that place
    tokens = place["description"]

    # get word counts per document and total words
    counter = Counter(tokens)
    words_count = len(tokens)
    
    # for each word in document
    for token in np.unique(tokens):    
        
        # get term-frequency
        tf = counter[token]/words_count
        
        # get inverse document frequency
        idf = np.log(N/(doc_freq(token)+1))
        
        tf_idf_title[i, token] = tf*idf * (1-alpha)
        

# Create total tf_idf of all words of all documents
tf_idf = {}
for key in tf_idf_text.keys():
    tf_idf[key] = tf_idf_text[key] + tf_idf_title[key]
    
    
def search(query: str) -> list:
    """Performs the search inside all the places

    Args:
        query (str): The text that the user entered

    Returns:
        list: The list of places as a result
    """
    global places
    
    results = []
    places_ids = matching_score(query)
    for id in places_ids:
        results.append(places[id]["id"])
        
    return results
