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
import pandas as pd

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
LEMMATIZER = WordNetLemmatizer()
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
    global LEMMATIZER

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

        word = LEMMATIZER.lemmatize(word, pos)

        final.append(word)

    return final


def doc_freq(word: str) -> int:
    """Gets the document frequency using the dictionary made globally

    Args:
        word (str): The word

    Returns:
        int: The document frequency of that word
    """
    global DF

    freq = 0
    try:
        freq = DF[word]
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
    global TF_IDF

    # Preprocess the query
    tokens = preprocess_sentence(query)

    query_weights = {}

    # For each word in each document
    for key in TF_IDF:

        # If word in query, add document's value to query_weights
        if key[1] in tokens:
            try:
                query_weights[key[0]] += TF_IDF[key]
            except:
                query_weights[key[0]] = TF_IDF[key]

    # Sort the weights to get highers on top
    query_weights = sorted(query_weights.items(), key=lambda x: x[1], reverse=True)

    # Get only index in places list
    results = []
    for i in query_weights[:10]:
        results.append(i[0])

    return results


def gen_vector(text: str) -> list:
    """Creates a vector from each sentence that indicates the tf-idf of the words on that sentence

    Args:
        text (str): The sentence to convert to a N dimensional vector

    Returns:
        list: The resulting vector
    """
    global total_vocab, total_vocab_size, N

    tokens = preprocess_sentence(text)

    V = np.zeros((total_vocab_size))

    counter = Counter(tokens)
    words_count = total_vocab_size

    for token in np.unique(tokens):

        tf = counter[token]/words_count
        df = doc_freq(token)
        idf = np.log((N)/(df+1))

        try:
            index = total_vocab.index(token)
            V[index] = tf*idf
        except:
            pass

    return V


def cosine_similarity(a: np.array, b: np.array) -> float:
    """Calculates the cosine similarity of 2 vectors.
          Using the formula of dot product of them divided between the multiplication of their norms

    Args:
        a (np.array): Vector 01
        b (np.array): Vector 01

    Returns:
        float: The cosine similarity between them. Its range is (0, 1) inclusive
    """
    cos_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    return cos_sim


# Get all places and preprocess them
PLACES = read_all_places()
for place in PLACES:
    place["name"] = preprocess_sentence(place["name"])
    place["description"] = preprocess_sentence(place["description"])


# Create dictionary of document frequency with ids of documents
N = len(PLACES)
DF = {}
for i in range(N):
    tokens = PLACES[i]["description"]
    tokens.extend(PLACES[i]["name"])
    for w in tokens:
        try:
            DF[w].add(i)
        except KeyError:
            DF[w] = {i}

# Get only the frequency of appearance of each word
for word in DF.keys():
    DF[word] = len(DF[word])

# Create variables neccessary for tf-idf
total_vocab = list(DF.keys())
total_vocab_size = len(total_vocab)

# Create variables to store tf-idf values of each word in both, title and text
# Alpha is set to 0.3 as words in title will be more valuable (0.7) than words in description (0.3)
tf_idf_text = {}
tf_idf_title = {}
alpha = 0.3

# for each place calculate tf-idf for description
for i, place in enumerate(PLACES):

    # get tokens of that place's description
    tokens = place["description"]

    # get word counts per document and total words
    counter = Counter(tokens)
    words_count = total_vocab_size

    # for each word in document
    for token in np.unique(tokens):

        # get term-frequency
        tf = counter[token]/words_count

        # get inverse document frequency
        idf = np.log(N/(doc_freq(token)+1))

        tf_idf_text[i, token] = tf*idf * alpha


    ### REPEAT PROCESS FOR NAME
    tokens = place["name"]

    # get word counts per document and total words
    counter = Counter(tokens)
    words_count = total_vocab_size

    # for each word in document
    for token in np.unique(tokens):

        # get term-frequency
        tf = counter[token]/words_count

        # get inverse document frequency
        idf = np.log(N/(doc_freq(token)+1))

        tf_idf_title[i, token] = tf*idf * (1-alpha)


# Create total tf_idf of all words of all documents
TF_IDF = {}
for key in tf_idf_text.keys():
    TF_IDF[key] = tf_idf_text[key] + tf_idf_title.pop(key, 0)
for key in tf_idf_title.keys():
    TF_IDF[key] = tf_idf_title.get(key, 0)


# create matrix with tf-idf of each word/place
matrix = np.zeros((N, total_vocab_size))
for word in TF_IDF:
    try:
        index = total_vocab.index(word[1])
        matrix[word[0]][index] = TF_IDF[word]
    except:
        pass

# create dataframe and set index to place's objectId
DATAFRAME = pd.DataFrame(matrix)
DATAFRAME["objectId"] = pd.Series([x["id"] for x in PLACES])
DATAFRAME = DATAFRAME.set_index("objectId", drop=True)


def matching_score_search(query: str) -> list:
    """Performs the search inside all the places

    Args:
        query (str): The text that the user entered

    Returns:
        list: The list of places as a result
    """
    global PLACES

    results = []
    places_ids = matching_score(query)
    for id in places_ids:
        results.append(PLACES[id]["id"])

    return results


def cosine_search(query: str) -> list:
    """Performs search on all places using the cosine similarity algorithm along with tf-idf algorithm

    Args:
        query (str): The text introduced by the user

    Returns:
        list: The top 10 places that match that query
    """
    global DATAFRAME

    # Create list to store cosine similarity results
    d_cosines = []

    # Create vector out of query sentence
    query_vector = gen_vector(query)

    # Calculate cosine similarity of query vector to each place's vector
    for _, row in DATAFRAME.iterrows():
        d_cosines.append(cosine_similarity(np.array(query_vector), np.array(row)))

    # Get top 10 similar places
    out = np.array(d_cosines).argsort()
    out = out[::-1][:10]

    return [DATAFRAME.index[x] for x in out]
