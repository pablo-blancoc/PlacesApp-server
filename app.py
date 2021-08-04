import ml.promote as promote
import parse as parse_server
import one_signal
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import dotenv_values
from functools import wraps
import ml.knn as knn
import ml.tfidf as tfidf
from urllib.parse import unquote

app = Flask(__name__)
CORS(app)
SECRETS = dotenv_values(".env")
KNN_NEIGHBORS = knn.kNearestNeighbors()
KNN_DATA = knn.read_data()

def api_key_required(f):
    """
    Validates the API KEY sent on the request
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = SECRETS.get("API_KEY", 'True')
        headers = request.headers
        try:
            if headers.get('x-api-key', None) == api_key:
                pass
            else:
                return jsonify({"message": "invalid api key"}), 401
        except:
            return jsonify({"message": "invalid api key"}), 401
        return f(*args, **kwargs)
    return decorated


@app.errorhandler(404)
def resource_not_found(e):
    """Page not found
    Args:
        e (Error): Page not found error raised by Flask
    Returns:
        JSON: The same error raised
    """
    return jsonify(error=str(e)), 404


@app.route('/', methods=['GET'])
def test():
    """
    Sanity test to confirm backend is working
    """
    return "Working!", 200


@app.route('/push', methods=['GET'])
@api_key_required
def notify():
    """
    Send a push notification to all users suscribed to the user sent with the place that was just posted by it
    """
    try:
        userId = request.args["user"]
        placeId = request.args["place"]
    except KeyError:
        return "Place and user need to be on request", 400
    
    # Get user and place from Parse
    user = parse_server.get_user(objectId=userId)
    place = parse_server.get_place(objectId=placeId)
    
    # Get subscribers to that user
    subs = parse_server.get_subscriptions(user=user)
    
    # Create toUsers list
    toUsers = []
    for sub in subs:
        if sub.toUser.OneSignal is not None and len(sub.toUser.OneSignal) > 0:
            toUsers.append(sub.toUser.OneSignal)
    
    one_signal.push(place=place.objectId, toUsers=toUsers, title=f"{str(user.name).capitalize()} has posted a new place", text="Click and see this amazing place!")
    
    print(f"Sent {len(toUsers)} notifications!")
    
    return jsonify({"status": "ok"}), 200


@app.route('/recommend', methods=['GET'])
@api_key_required
def topK():
    """
    Gets 5 places (or less) to recommend to a specific user
    """
    global KNN_NEIGHBORS, KNN_DATA
    
    try:
        userId = request.args["user"]
    except KeyError:
        return "User not found on the request", 400
    
    # Get the list of 5 recommendations for the user
    places = knn.recommend(neighbors=KNN_NEIGHBORS, data=KNN_DATA, user=userId)
    
    return jsonify({"places": places}), 200


@app.route('/search', methods=['GET'])
@api_key_required
def search_places():
    """
    Get top 10 places for search using tf-idf algorithm
    """
    
    try:
        query = unquote(request.args["query"])
    except KeyError:
        return "Query not found", 400
    
    # Get top places for query using cosine similarity
    places = tfidf.cosine_search(query=query)
    
    return jsonify({"places": places}), 200


@app.route('/promote', methods=['GET'])
@api_key_required
def promote_place():
    """
    Promote the place given to the top 5 people that might like it
    """
    
    try:
        place = request.args["place"]
    except KeyError:
        return "Place not found", 400
    
    # Get top places for query using cosine similarity
    places = promote.promote(place=place)
    
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(SECRETS.get("PORT")))
